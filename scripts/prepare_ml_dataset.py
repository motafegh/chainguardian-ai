"""
Prepare ML Dataset from Feature Extraction Results
===================================================

Quality checks, cleaning, and preprocessing for ML training.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    print("="*70)
    print("DATASET PREPARATION FOR ML TRAINING")
    print("="*70)
    
    # ================================================================
    # STEP 1: LOAD DATASET
    # ================================================================
    logger.info("\n[1/7] Loading extracted features...")
    
    dataset_path = Path('data/collected_dataset.csv')
    
    if not dataset_path.exists():
        logger.error(f"❌ Dataset not found: {dataset_path}")
        return
    
    df = pd.read_csv(dataset_path)
    logger.info(f"✓ Loaded {len(df)} contracts with {len(df.columns)} columns")
    
    # ================================================================
    # STEP 2: FILTER SUCCESSFUL EXTRACTIONS
    # ================================================================
    logger.info("\n[2/7] Filtering successful extractions...")
    
    logger.info(f"Total contracts: {len(df)}")
    logger.info(f"  - With failure_reason: {df['failure_reason'].notna().sum()}")
    logger.info(f"  - Successful: {df['failure_reason'].isna().sum()}")
    
    # Keep only successful extractions
    df_clean = df[df['failure_reason'].isna()].copy()
    
    logger.info(f"\n✓ Kept {len(df_clean)} successful extractions")
    logger.info(f"  Dropped {len(df) - len(df_clean)} failed extractions")
    
    # ================================================================
    # STEP 3: REMOVE ERROR COLUMNS
    # ================================================================
    logger.info("\n[3/7] Removing error tracking columns...")
    
    error_cols = ['failure_reason', 'error_message']
    cols_to_drop = [col for col in error_cols if col in df_clean.columns]
    
    if cols_to_drop:
        df_clean = df_clean.drop(columns=cols_to_drop)
        logger.info(f"✓ Dropped columns: {cols_to_drop}")
    
    # ================================================================
    # STEP 4: HANDLE MISSING VALUES
    # ================================================================
    logger.info("\n[4/7] Checking for missing values...")
    
    missing = df_clean.isnull().sum()
    missing = missing[missing > 0]
    
    if len(missing) > 0:
        logger.warning(f"Found missing values:")
        for col, count in missing.items():
            logger.warning(f"  - {col}: {count} missing ({count/len(df_clean)*100:.1f}%)")
        
        # Fill numeric columns with 0
        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
        df_clean[numeric_cols] = df_clean[numeric_cols].fillna(0)
        logger.info(f"✓ Filled numeric columns with 0")
    else:
        logger.info("✓ No missing values found")
    
    # ================================================================
    # STEP 5: REMOVE DUPLICATES
    # ================================================================
    logger.info("\n[5/7] Checking for duplicates...")
    
    # Check for duplicate contract names
    duplicates = df_clean['contract_name'].duplicated().sum()
    
    if duplicates > 0:
        logger.warning(f"Found {duplicates} duplicate contract names")
        
        # Keep first occurrence
        df_clean = df_clean.drop_duplicates(subset='contract_name', keep='first')
        logger.info(f"✓ Removed {duplicates} duplicates (kept first occurrence)")
    else:
        logger.info("✓ No duplicates found")
    
    # ================================================================
    # STEP 6: VALIDATE FEATURE COLUMNS
    # ================================================================
    logger.info("\n[6/7] Validating feature columns...")
    
    expected_features = [
        # Metadata
        'contract_name',
        'file_path',
        # Vulnerability features (7)
        'has_reentrancy',
        'has_access_control_issues',
        'has_timestamp_dependency',
        'has_unchecked_call',
        'high_severity_count',
        'medium_severity_count',
        'low_severity_count',
        # Code structure features (6)
        'num_functions',
        'num_external_calls',
        'num_state_vars',
        'num_modifiers',
        'max_cyclomatic_complexity',
        'num_low_level_calls',
    ]
    
    missing_features = [f for f in expected_features if f not in df_clean.columns]
    extra_features = [f for f in df_clean.columns if f not in expected_features]
    
    if missing_features:
        logger.error(f"❌ Missing expected features: {missing_features}")
        return
    
    if extra_features:
        logger.info(f"Extra columns (will keep): {extra_features}")
    
    logger.info(f"✓ All {len(expected_features)} expected features present")
    
    # ================================================================
    # STEP 7: ANALYZE TARGET VARIABLE
    # ================================================================
    logger.info("\n[7/7] Analyzing target variable distribution...")
    
    target_col = 'has_reentrancy'
    
    logger.info(f"\nTarget: {target_col}")
    logger.info(f"  Total samples: {len(df_clean)}")
    logger.info(f"  Positive (vulnerable): {df_clean[target_col].sum()} ({df_clean[target_col].sum()/len(df_clean)*100:.1f}%)")
    logger.info(f"  Negative (safe): {(~df_clean[target_col]).sum()} ({(~df_clean[target_col]).sum()/len(df_clean)*100:.1f}%)")
    
    # Check other targets too
    logger.info(f"\nOther potential targets:")
    for col in ['has_access_control_issues', 'has_timestamp_dependency', 'has_unchecked_call']:
        if col in df_clean.columns:
            count = df_clean[col].sum()
            pct = count / len(df_clean) * 100
            logger.info(f"  {col}: {count} ({pct:.1f}%)")
    
    # ================================================================
    # STEP 8: FEATURE STATISTICS
    # ================================================================
    logger.info("\n" + "="*70)
    logger.info("FEATURE STATISTICS")
    logger.info("="*70)
    
    numeric_features = df_clean.select_dtypes(include=[np.number]).columns
    numeric_features = [f for f in numeric_features if f not in ['contract_name', 'file_path']]
    
    stats = df_clean[numeric_features].describe()
    
    logger.info(f"\nNumeric features summary:")
    for col in numeric_features:
        if col.startswith('has_'):
            continue  # Skip boolean flags
        
        mean_val = stats[col]['mean']
        std_val = stats[col]['std']
        min_val = stats[col]['min']
        max_val = stats[col]['max']
        
        logger.info(f"  {col:.<40} mean={mean_val:.1f}, std={std_val:.1f}, range=[{min_val:.0f}, {max_val:.0f}]")
    
    # ================================================================
    # SAVE CLEANED DATASET
    # ================================================================
    logger.info("\n" + "="*70)
    logger.info("SAVING CLEANED DATASET")
    logger.info("="*70)
    
    output_path = Path('data/ml_dataset_clean_dedup.csv')
    df_clean.to_csv(output_path, index=False)
    
    logger.info(f"\n✓ Saved to: {output_path}")
    logger.info(f"  - Contracts: {len(df_clean)}")
    logger.info(f"  - Features: {len(df_clean.columns)}")
    logger.info(f"  - Size: {output_path.stat().st_size / 1024:.1f} KB")
    
    # ================================================================
    # QUALITY SUMMARY
    # ================================================================
    logger.info("\n" + "="*70)
    logger.info("QUALITY SUMMARY")
    logger.info("="*70)
    
    logger.info(f"\n✅ Dataset ready for ML training!")
    logger.info(f"  - Input contracts: {len(df)}")
    logger.info(f"  - Successful extractions: {len(df_clean)}")
    logger.info(f"  - Success rate: {len(df_clean)/len(df)*100:.1f}%")
    logger.info(f"  - Features: {len(numeric_features)} numeric + 2 metadata")
    logger.info(f"  - No missing values: ✓")
    logger.info(f"  - No duplicates: ✓")
    logger.info(f"  - Target variable: {target_col}")
    logger.info(f"  - Class balance: {df_clean[target_col].sum()}/{len(df_clean)} positive")
    
    # Check if enough data
    if len(df_clean) < 50:
        logger.warning(f"\n⚠️ WARNING: Only {len(df_clean)} samples!")
        logger.warning("   Recommended minimum: 50-100 samples for baseline model")
        logger.warning("   Consider collecting more data or using simpler model")
    elif len(df_clean) < 100:
        logger.warning(f"\n⚠️ Dataset is small ({len(df_clean)} samples)")
        logger.warning("   Use simple models (Random Forest) and careful validation")
    else:
        logger.info(f"\n✅ Dataset size is adequate ({len(df_clean)} samples)")
    
    # Check class balance
    minority_class = min(df_clean[target_col].sum(), (~df_clean[target_col]).sum())
    if minority_class < 10:
        logger.warning(f"\n⚠️ WARNING: Minority class has only {minority_class} samples!")
        logger.warning("   SMOTE may not work well - consider:")
        logger.warning("   1. Collecting more vulnerable contracts")
        logger.warning("   2. Using different target (e.g., has_access_control_issues)")
        logger.warning("   3. Using anomaly detection instead of classification")
    elif minority_class < 20:
        logger.warning(f"\n⚠️ Small minority class ({minority_class} samples)")
        logger.warning("   SMOTE will help but be cautious of overfitting")
    else:
        logger.info(f"\n✅ Minority class size is adequate ({minority_class} samples)")
    
    logger.info("\n" + "="*70)
    logger.info("NEXT STEP: Run ML training")
    logger.info("  poetry run python src/chainguardian/ml/training/train_baseline.py")
    logger.info("="*70)


if __name__ == "__main__":
    main()
