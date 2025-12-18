"""
Clean Dataset - Remove Zero-Feature Contracts
Remove contracts where all features are zeros (failed analysis)
"""

import pandas as pd
from pathlib import Path

def clean_dataset(
    input_path: str = "data/collected_dataset.csv",
    output_path: str = "data/collected_dataset_cleaned.csv"
):
    """
    Remove contracts with all-zero features.
    
    Args:
        input_path: Path to raw dataset
        output_path: Path to save cleaned dataset
    """
    print(f"{'='*70}")
    print(f"DATASET CLEANING - Remove Zero-Feature Contracts")
    print(f"{'='*70}\n")
    
    # Read dataset
    print(f"Reading dataset from: {input_path}")
    df = pd.read_csv(input_path)
    
    print(f"Original dataset: {len(df)} contracts\n")
    
    # Define feature columns (exclude metadata)
    feature_columns = [
        'has_reentrancy',
        'has_access_control_issues',
        'has_timestamp_dependency',
        'has_unchecked_call',
        'high_severity_count',
        'medium_severity_count',
        'low_severity_count',
        'num_functions',
        'num_external_calls',
        'num_state_vars',
        'num_modifiers',
        'max_cyclomatic_complexity',
        'num_low_level_calls'
    ]
    
    # Show original statistics
    print(f"{'='*70}")
    print(f"ORIGINAL DATASET STATISTICS")
    print(f"{'='*70}")
    print(f"Total contracts: {len(df)}")
    print(f"\nFeature statistics:")
    print(df[feature_columns].describe())
    
    # Identify zero-feature contracts
    # Convert boolean columns to int for sum
    df_numeric = df[feature_columns].copy()
    for col in ['has_reentrancy', 'has_access_control_issues', 
                'has_timestamp_dependency', 'has_unchecked_call']:
        df_numeric[col] = df_numeric[col].astype(int)
    
    # Sum all features per row
    feature_sum = df_numeric.sum(axis=1)
    
    # Contracts with zero features
    zero_mask = feature_sum == 0
    zero_contracts = df[zero_mask]
    valid_contracts = df[~zero_mask]
    
    print(f"\n{'='*70}")
    print(f"FILTERING RESULTS")
    print(f"{'='*70}")
    print(f"Zero-feature contracts: {len(zero_contracts)} ({len(zero_contracts)/len(df)*100:.1f}%)")
    print(f"Valid contracts:        {len(valid_contracts)} ({len(valid_contracts)/len(df)*100:.1f}%)")
    
    # Show sample of removed contracts
    if len(zero_contracts) > 0:
        print(f"\nSample of removed contracts (first 10):")
        for i, row in zero_contracts.head(10).iterrows():
            print(f"  - {row['contract_name']:30s} ({Path(row['file_path']).name})")
        
        if len(zero_contracts) > 10:
            print(f"  ... and {len(zero_contracts) - 10} more")
    
    # Save cleaned dataset
    valid_contracts.to_csv(output_path, index=False)
    
    print(f"\n{'='*70}")
    print(f"CLEANED DATASET STATISTICS")
    print(f"{'='*70}")
    print(f"Total contracts: {len(valid_contracts)}")
    print(f"\nFeature statistics:")
    print(valid_contracts[feature_columns].describe())
    
    print(f"\n{'='*70}")
    print(f"✅ Cleaned dataset saved to: {output_path}")
    print(f"{'='*70}\n")
    
    # Return summary stats
    return {
        'original_count': len(df),
        'removed_count': len(zero_contracts),
        'valid_count': len(valid_contracts),
        'success_rate': len(valid_contracts) / len(df) * 100
    }


if __name__ == "__main__":
    stats = clean_dataset()
    
    print(f"\n📊 SUMMARY:")
    print(f"   Original:  {stats['original_count']} contracts")
    print(f"   Removed:   {stats['removed_count']} contracts (all zeros)")
    print(f"   Cleaned:   {stats['valid_count']} contracts")
    print(f"   Success:   {stats['success_rate']:.1f}%\n")
