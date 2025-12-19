# scripts/export_final_dataset.py
"""
Export final dataset with all 85 features.
Ready for ML training.
"""
from chainguardian.database.manager import DatabaseManager
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def export_dataset():
    """Export complete dataset with feature analysis."""
    
    db = DatabaseManager()
    df = db.get_all_features()
    
    # Separate successful and failed
    successful = df[df['failure_reason'].isna()].copy()
    failed = df[df['failure_reason'].notna()].copy()
    
    print("="*70)
    print("FINAL DATASET EXPORT")
    print("="*70)
    
    # Dataset stats
    print(f"\n📊 Dataset Overview:")
    print(f"  Total contracts: {len(df)}")
    print(f"  Successful extractions: {len(successful)} ({len(successful)/len(df)*100:.1f}%)")
    print(f"  Failed extractions: {len(failed)} ({len(failed)/len(df)*100:.1f}%)")
    print(f"  Total features: {len(df.columns)}")
    
    # Feature breakdown
    feature_cols = [col for col in successful.columns if col not in 
                   ['contract_id', 'contract_name', 'address', 'file_path', 
                    'compiler_version', 'failure_reason', 'error_message']]
    
    graph_features = [col for col in feature_cols if col.startswith(('cfg_', 'cg_', 'dfg_'))]
    vuln_features = [col for col in feature_cols if col.startswith('has_')]
    
    print(f"\n📈 Feature Categories:")
    print(f"  Total ML features: {len(feature_cols)}")
    print(f"  Vulnerability flags: {len(vuln_features)}")
    print(f"  Graph features: {len(graph_features)}")
    print(f"  Other features: {len(feature_cols) - len(vuln_features) - len(graph_features)}")
    
    # Vulnerability distribution
    if len(successful) > 0:
        high_severity = successful[successful['high_severity_count'] > 0]
        has_any_vuln = successful[
            (successful['high_severity_count'] > 0) |
            (successful['medium_severity_count'] > 0) |
            (successful['low_severity_count'] > 0)
        ]
        
        print(f"\n🐛 Vulnerability Distribution:")
        print(f"  High severity issues: {len(high_severity)} ({len(high_severity)/len(successful)*100:.1f}%)")
        print(f"  Any vulnerabilities: {len(has_any_vuln)} ({len(has_any_vuln)/len(successful)*100:.1f}%)")
        print(f"  Clean contracts: {len(successful) - len(has_any_vuln)} ({(len(successful) - len(has_any_vuln))/len(successful)*100:.1f}%)")
    
    # Graph feature stats
    print(f"\n📊 Graph Feature Statistics (Sample):")
    if len(successful) > 0:
        print(f"  Avg CFG cycles: {successful['cfg_num_cycles'].mean():.2f}")
        print(f"  Avg external calls: {successful['cg_num_external_calls'].mean():.2f}")
        print(f"  Avg tainted flows: {successful['dfg_num_tainted_flows'].mean():.2f}")
        print(f"  Contracts with complex loops: {successful['cfg_has_complex_loops'].sum()} ({successful['cfg_has_complex_loops'].sum()/len(successful)*100:.1f}%)")
        print(f"  Contracts with cyclic calls: {successful['cg_has_cyclic_calls'].sum()} ({successful['cg_has_cyclic_calls'].sum()/len(successful)*100:.1f}%)")
    
    # Export files
    output_dir = 'data'
    
    # 1. Full dataset (all contracts)
    full_path = f"{output_dir}/chainguardian_full_dataset.csv"
    df.to_csv(full_path, index=False)
    print(f"\n💾 Exported Files:")
    print(f"  Full dataset: {full_path}")
    print(f"    ({len(df)} contracts, {len(df.columns)} columns)")
    
    # 2. Clean dataset (successful only)
    clean_path = f"{output_dir}/chainguardian_clean_dataset.csv"
    successful.to_csv(clean_path, index=False)
    print(f"  Clean dataset: {clean_path}")
    print(f"    ({len(successful)} contracts, {len(successful.columns)} columns)")
    
    # 3. ML-ready dataset (features only)
    ml_features = successful[feature_cols].copy()
    
    # Create target variable
    ml_features['target_high_severity'] = (successful['high_severity_count'] > 0).astype(int)
    ml_features['target_any_vulnerability'] = (
        (successful['high_severity_count'] > 0) |
        (successful['medium_severity_count'] > 0) |
        (successful['low_severity_count'] > 0)
    ).astype(int)
    
    ml_path = f"{output_dir}/chainguardian_ml_ready.csv"
    ml_features.to_csv(ml_path, index=False)
    print(f"  ML-ready dataset: {ml_path}")
    print(f"    ({len(ml_features)} contracts, {len(ml_features.columns)} features + 2 targets)")
    
    # 4. Feature metadata
    feature_info = pd.DataFrame({
        'feature_name': feature_cols,
        'non_zero_count': [successful[col].astype(bool).sum() for col in feature_cols],
        'mean_value': [successful[col].mean() if successful[col].dtype in ['int64', 'float64'] else 0 
                      for col in feature_cols],
        'category': ['graph' if col.startswith(('cfg_', 'cg_', 'dfg_')) 
                    else 'vulnerability' if col.startswith('has_')
                    else 'severity' if 'severity' in col
                    else 'other'
                    for col in feature_cols]
    })
    
    feature_info_path = f"{output_dir}/feature_metadata.csv"
    feature_info.to_csv(feature_info_path, index=False)
    print(f"  Feature metadata: {feature_info_path}")
    
    print("\n" + "="*70)
    print("✅ DATASET READY FOR ML TRAINING")
    print("="*70)
    print(f"\nNext steps:")
    print(f"1. Train ensemble models (RF, XGBoost, LightGBM)")
    print(f"2. Track experiments with MLflow")
    print(f"3. Build FastAPI endpoint")
    print("="*70 + "\n")
    
    return successful

if __name__ == "__main__":
    df = export_dataset()
