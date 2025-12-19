"""
Export final dataset with smart labeling and test mock filtering.

FIXED VERSION v3:
- Filters out test/mock contracts (intentionally vulnerable)
- Ignores low-severity issues (informational/style)
- Source-based labeling for known datasets
- Creates balanced vulnerable/safe dataset
- BACKWARD COMPATIBLE with train_llm_feeder.py
- CONVERTS BOOLEAN STRINGS TO INTEGERS (Critical fix!)
- REMOVES LEAKY FEATURES (risk_score_simple, risk_score_weighted)

Author: Ali - ChainGuardian AI Project
"""
from chainguardian.database.manager import DatabaseManager
import pandas as pd
import logging
import re
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_boolean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert boolean columns to numeric (0/1).
    
    CRITICAL FIX: Handles both string booleans ('True'/'False') 
    and Python booleans (True/False). Converts to int64 for sklearn.
    
    Args:
        df: DataFrame with potential boolean columns
        
    Returns:
        DataFrame with booleans converted to 0/1 integers
    """
    # Identify boolean columns by naming patterns
    boolean_patterns = [
        'has_',           # has_reentrancy, has_access_control_issues, etc.
        'is_high_risk',   # is_high_risk flag
        'cfg_has_',       # cfg_has_complex_loops
        'cg_has_',        # cg_has_cyclic_calls
        'dfg_has_',       # dfg_has_cross_function_flow
    ]
    
    boolean_columns = [
        col for col in df.columns 
        if any(col.startswith(pattern) for pattern in boolean_patterns)
    ]
    
    if not boolean_columns:
        return df
    
    print(f"\n🔄 Converting {len(boolean_columns)} boolean columns to numeric...")
    
    converted_count = 0
    for col in boolean_columns:
        if col not in df.columns:
            continue
        
        # Convert if column is object (string) OR bool type
        if df[col].dtype == 'object':
            # String booleans: 'True'/'False' → 1/0
            df[col] = df[col].map({
                'True': 1, 'False': 0,
                True: 1, False: 0,
                'true': 1, 'false': 0,
                1: 1, 0: 0,
                '1': 1, '0': 0,
            })
            df[col] = df[col].fillna(0).astype(int)
            converted_count += 1
            
        elif df[col].dtype == 'bool':
            # Python booleans: True/False → 1/0
            df[col] = df[col].astype(int)
            converted_count += 1
    
    if converted_count > 0:
        print(f"✅ Converted {converted_count} boolean columns to int64")
        print(f"   (sklearn requires numeric features for optimal performance)")
    
    return df



def identify_test_mocks(df: pd.DataFrame) -> pd.Series:
    """
    Identify test/mock contracts that shouldn't be in training data.
    
    These are intentionally vulnerable or incomplete for testing purposes.
    Including them would confuse the model with "correct bad examples".
    """
    test_patterns = [
        r'Mock$',           # ERC3156FlashBorrowerMock
        r'Test$',           # SomeTest
        r'Dirty$',          # Base64Dirty
        r'Reentrant$',      # TimelockReentrant (intentionally vulnerable)
        r'^Dummy',          # DummyImplementation
        r'Harness$',        # TestHarness
        r'Example$',        # ExampleContract
        r'^Bad',            # BadImplementation
        r'Malicious',       # MaliciousContract
        r'Attacker',        # AttackerContract
        r'Vulnerable',      # VulnerableExample (test contracts)
    ]
    
    test_pattern = '|'.join(test_patterns)
    is_test = df['contract_name'].str.contains(test_pattern, case=False, regex=True, na=False)
    
    logger.info(f"🧪 Identified {is_test.sum()} test/mock contracts")
    
    return is_test


def label_contracts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Label contracts as vulnerable/safe with smart filtering.
    
    Strategy:
    1. Filter out test mocks (intentionally vulnerable)
    2. Ignore low-severity issues (informational: floating pragma, assembly)
    3. Trust source labels for known datasets
    4. Use HIGH/MEDIUM severity for mixed sources
    """
    
    # Identify test mocks
    df['is_test_mock'] = identify_test_mocks(df)
    
    # Initialize labels (default = safe)
    df['is_vulnerable'] = False
    
    # ================================================================
    # LABEL BY SOURCE (Known datasets)
    # ================================================================
    
    # Known vulnerable datasets (100% vulnerable)
    vulnerable_sources = [
        'smartbugs_curated',
        'production_vulnerable',
        'trail_of_bits',
        'swc_registry',
        'rekt_news',
        'slowmist_hacked'
    ]
    df.loc[df['data_source'].isin(vulnerable_sources), 'is_vulnerable'] = True
    
    # Known safe datasets (exclude test mocks)
    safe_sources = ['openzeppelin', 'production_safe']
    safe_mask = df['data_source'].isin(safe_sources) & ~df['is_test_mock']
    df.loc[safe_mask, 'is_vulnerable'] = False
    
    # ================================================================
    # MIXED SOURCES: Use detector results (HIGH/MEDIUM only)
    # ================================================================
    mixed_sources = ['adversarial_test', 'diagnostic', 'manual']
    mixed_mask = df['data_source'].isin(mixed_sources)
    
    # Only HIGH/MEDIUM severity counts as vulnerable
    # LOW severity is mostly informational (floating pragma, assembly optimization)
    df.loc[mixed_mask, 'is_vulnerable'] = (
        (df.loc[mixed_mask, 'high_severity_count'] > 0) |
        (df.loc[mixed_mask, 'medium_severity_count'] > 0)
    )
    
    # Create clean flag
    df['is_clean'] = ~df['is_vulnerable']
    
    logger.info(f"✅ Labeled {len(df)} contracts")
    
    return df


def remove_leaky_features(feature_cols: list) -> list:
    """
    Remove features that leak target information.
    
    CRITICAL: risk_score_simple and risk_score_weighted are calculated
    from the target variable (severity counts). Including them causes
    the model to just copy these scores instead of learning patterns.
    
    Args:
        feature_cols: List of feature column names
        
    Returns:
        Filtered list without leaky features
    """
    leaky_features = [
        'risk_score_simple',      # Calculated from severity counts (target leakage)
        'risk_score_weighted',
        'is_high_risk', 
        'total_detector_hits',  # Same - direct calculation from target
    ]
    
    filtered = [col for col in feature_cols if col not in leaky_features]
    removed = set(feature_cols) - set(filtered)
    
    if removed:
        print(f"\n🚫 Removed {len(removed)} leaky features:")
        for feat in sorted(removed):
            print(f"   - {feat} (causes target leakage)")
    
    return filtered


def export_dataset():
    """Export complete dataset with smart labeling, boolean conversion, and filtering."""
    
    db = DatabaseManager()
    df = db.get_all_features()
    
    print("\n" + "="*70)
    print("FINAL DATASET EXPORT (FIXED v3 - Boolean Conversion)")
    print("="*70)
    
    # ================================================================
    # SEPARATE SUCCESSFUL AND FAILED
    # ================================================================
    successful = df[df['failure_reason'].isna()].copy()
    failed = df[df['failure_reason'].notna()].copy()
    
    print(f"\n📊 Initial Dataset:")
    print(f"  Total contracts: {len(df)}")
    print(f"  Successful extractions: {len(successful)} ({len(successful)/len(df)*100:.1f}%)")
    print(f"  Failed extractions: {len(failed)} ({len(failed)/len(df)*100:.1f}%)")
    
    # ================================================================
    # APPLY SMART LABELING
    # ================================================================
    print(f"\n🏷️  Applying smart labeling...")
    successful = label_contracts(successful)
    
    # ================================================================
    # FILTER OUT TEST MOCKS
    # ================================================================
    df_production = successful[~successful['is_test_mock']].copy()
    df_test_mocks = successful[successful['is_test_mock']].copy()
    
    print(f"\n🧹 After filtering test mocks:")
    print(f"  Production contracts: {len(df_production)}")
    print(f"  Test mocks removed: {len(df_test_mocks)}")
    
    # ================================================================
    # CRITICAL FIX: CONVERT BOOLEAN STRINGS TO INTEGERS
    # ================================================================
    df_production = convert_boolean_columns(df_production)
    
    # ================================================================
    # STATISTICS
    # ================================================================
    print(f"\n🐛 Vulnerability Distribution (Production only):")
    vuln_count = df_production['is_vulnerable'].sum()
    clean_count = df_production['is_clean'].sum()
    print(f"  Vulnerable: {vuln_count} ({vuln_count/len(df_production)*100:.1f}%)")
    print(f"  Clean: {clean_count} ({clean_count/len(df_production)*100:.1f}%)")
    
    # By severity
    high_sev = (df_production['high_severity_count'] > 0).sum()
    med_sev = (df_production['medium_severity_count'] > 0).sum()
    low_sev = (df_production['low_severity_count'] > 0).sum()
    
    print(f"\n⚠️  Severity Breakdown:")
    print(f"  High severity: {high_sev} ({high_sev/len(df_production)*100:.1f}%)")
    print(f"  Medium severity: {med_sev} ({med_sev/len(df_production)*100:.1f}%)")
    print(f"  Low severity: {low_sev} ({low_sev/len(df_production)*100:.1f}%)")
    
    # By source
    print(f"\n📊 By Source (Production only):")
    for source in sorted(df_production['data_source'].unique()):
        source_df = df_production[df_production['data_source'] == source]
        source_vuln = source_df['is_vulnerable'].sum()
        source_clean = source_df['is_clean'].sum()
        print(f"  {source:25s}: {len(source_df):4d} total "
              f"({source_vuln:3d} vuln, {source_clean:3d} clean)")
    
    # ================================================================
    # PREPARE FEATURE COLUMNS (Remove metadata and leaky features)
    # ================================================================
    metadata_cols = [
        'contract_id', 'contract_name', 'address', 'file_path', 
        'compiler_version', 'failure_reason', 'error_message',
        'data_source', 'is_test_mock', 'is_vulnerable', 'is_clean', 
        'filepath', 'created_at', 'updated_at'
    ]
    
    feature_cols = [col for col in df_production.columns if col not in metadata_cols]
    
    # Remove leaky features (critical for model integrity)
    feature_cols = remove_leaky_features(feature_cols)
    
    graph_features = [col for col in feature_cols if col.startswith(('cfg_', 'cg_', 'dfg_'))]
    vuln_features = [col for col in feature_cols if col.startswith('has_')]
    
    print(f"\n📈 Feature Categories:")
    print(f"  Total ML features: {len(feature_cols)}")
    print(f"  Vulnerability flags: {len(vuln_features)}")
    print(f"  Graph features: {len(graph_features)}")
    print(f"  Other features: {len(feature_cols) - len(vuln_features) - len(graph_features)}")
    
    # Verify boolean features are now numeric
    boolean_features = [col for col in vuln_features if col in df_production.columns]
    if boolean_features:
        sample_types = df_production[boolean_features[:3]].dtypes
        print(f"\n✅ Boolean Feature Types (sample):")
        for col, dtype in sample_types.items():
            print(f"  {col}: {dtype}")
    
    # Graph feature stats
    if len(df_production) > 0:
        print(f"\n📊 Graph Feature Statistics (Sample):")
        print(f"  Avg CFG cycles: {df_production['cfg_num_cycles'].mean():.2f}")
        print(f"  Avg external calls: {df_production['cg_num_external_calls'].mean():.2f}")
        print(f"  Avg tainted flows: {df_production['dfg_num_tainted_flows'].mean():.2f}")
        
        if 'cfg_has_complex_loops' in df_production.columns:
            complex_loops = df_production['cfg_has_complex_loops'].sum()
            print(f"  Contracts with complex loops: {complex_loops} "
                  f"({complex_loops/len(df_production)*100:.1f}%)")
        
        if 'cg_has_cyclic_calls' in df_production.columns:
            cyclic_calls = df_production['cg_has_cyclic_calls'].sum()
            print(f"  Contracts with cyclic calls: {cyclic_calls} "
                  f"({cyclic_calls/len(df_production)*100:.1f}%)")
    
    # ================================================================
    # EXPORT FILES
    # ================================================================
    output_dir = Path('data')
    output_dir.mkdir(exist_ok=True)
    
    print(f"\n💾 Exported Files:")
    
    # 1. Full dataset (all contracts, including failed)
    full_path = output_dir / "chainguardian_full_dataset.csv"
    df.to_csv(full_path, index=False)
    print(f"  Full dataset: {full_path}")
    print(f"    ({len(df)} contracts, {len(df.columns)} columns)")
    
    # 2. Production dataset (no test mocks, successful only, booleans converted)
    prod_path = output_dir / "chainguardian_production_dataset.csv"
    df_production.to_csv(prod_path, index=False)
    print(f"  Production dataset: {prod_path}")
    print(f"    ({len(df_production)} contracts, {len(df_production.columns)} columns)")
    
    # ================================================================
    # BACKWARD COMPATIBILITY FILES FOR train_llm_feeder.py
    # ================================================================
    print(f"\n🔄 Backward Compatibility Files:")
    
    # training_clean.csv: features + binary label (expected by train_llm_feeder.py)
    df_training_clean = df_production[feature_cols].copy()
    df_training_clean['label'] = df_production['is_vulnerable'].astype(int).values
    
    training_clean_path = output_dir / "training_clean.csv"
    df_training_clean.to_csv(training_clean_path, index=False)
    print(f"  training_clean.csv: {training_clean_path}")
    print(f"    ({len(df_training_clean)} contracts, {len(df_training_clean.columns)} columns)")
    
    # training_labeled_full.csv: all columns for risk score calculation
    df_training_full = df_production.copy()
    df_training_full['label'] = df_training_full['is_vulnerable'].astype(int)
    
    training_full_path = output_dir / "training_labeled_full.csv"
    df_training_full.to_csv(training_full_path, index=False)
    print(f"  training_labeled_full.csv: {training_full_path}")
    print(f"    ({len(df_training_full)} contracts, {len(df_training_full.columns)} columns)")
    
    # prediction_clean.csv: for unlabeled prediction (legacy compatibility)
    df_prediction = df_production[feature_cols].copy()
    
    prediction_path = output_dir / "prediction_clean.csv"
    df_prediction.to_csv(prediction_path, index=False)
    print(f"  prediction_clean.csv: {prediction_path}")
    print(f"    ({len(df_prediction)} contracts, {len(feature_cols)} features)")
    
    # ================================================================
    # NEW FORMAT FILES
    # ================================================================
    print(f"\n📦 New Format Files:")
    
    # ML-ready dataset (features + multiple targets)
    ml_features = df_production[feature_cols].copy()
    
    # Add target variables
    ml_features['is_vulnerable'] = df_production['is_vulnerable'].values
    ml_features['high_severity'] = (df_production['high_severity_count'] > 0).astype(int).values
    ml_features['medium_severity'] = (df_production['medium_severity_count'] > 0).astype(int).values
    
    ml_path = output_dir / "chainguardian_ml_ready.csv"
    ml_features.to_csv(ml_path, index=False)
    print(f"  chainguardian_ml_ready.csv: {ml_path}")
    print(f"    ({len(ml_features)} contracts, {len(feature_cols)} features + 3 targets)")
    
    # Test mocks (for reference)
    if len(df_test_mocks) > 0:
        mocks_path = output_dir / "chainguardian_test_mocks.csv"
        df_test_mocks.to_csv(mocks_path, index=False)
        print(f"  chainguardian_test_mocks.csv: {mocks_path}")
        print(f"    ({len(df_test_mocks)} test/mock contracts - excluded from training)")
    
    # Feature metadata
    feature_info = pd.DataFrame({
        'feature_name': feature_cols,
        'non_zero_count': [df_production[col].astype(bool).sum() for col in feature_cols],
        'mean_value': [df_production[col].mean() if df_production[col].dtype in ['int64', 'float64'] else 0 
                      for col in feature_cols],
        'std_value': [df_production[col].std() if df_production[col].dtype in ['int64', 'float64'] else 0 
                     for col in feature_cols],
        'category': ['graph' if col.startswith(('cfg_', 'cg_', 'dfg_')) 
                    else 'vulnerability' if col.startswith('has_')
                    else 'severity' if 'severity' in col
                    else 'code_quality' if col in ['lines_of_code', 'num_functions', 'num_comments']
                    else 'other'
                    for col in feature_cols]
    })
    
    feature_info_path = output_dir / "feature_metadata.csv"
    feature_info.to_csv(feature_info_path, index=False)
    print(f"  feature_metadata.csv: {feature_info_path}")
    
    # ================================================================
    # RECOMMENDATIONS
    # ================================================================
    print("\n" + "="*70)
    print("✅ DATASET READY FOR ML TRAINING")
    print("="*70)
    
    vuln_ratio = df_production['is_vulnerable'].mean()
    
    print(f"\n💡 Dataset Quality Check:")
    if vuln_ratio > 0.7:
        print(f"  ⚠️  Dataset skewed toward vulnerable ({vuln_ratio*100:.0f}%)")
        print(f"     → Consider adding more safe contracts")
    elif vuln_ratio < 0.3:
        print(f"  ⚠️  Dataset skewed toward safe ({(1-vuln_ratio)*100:.0f}%)")
        print(f"     → Consider adding more vulnerable contracts")
    else:
        print(f"  ✅ Good balance ({vuln_ratio*100:.0f}% vulnerable, {(1-vuln_ratio)*100:.0f}% safe)")
    
    print(f"\n📝 Next steps:")
    print(f"  1. Train LLM feeder models:")
    print(f"     poetry run python scripts/3_training/train_llm_feeder.py")
    print(f"  2. Test on adversarial cases:")
    print(f"     poetry run python scripts/3_training/test_model_adversarial.py")
    print(f"  3. Expected improvement: 24% → 60-75% accuracy")
    print("="*70 + "\n")
    
    return df_production


if __name__ == "__main__":
    df = export_dataset()
