# scripts/fix_dataset.py

"""
Dataset Cleaning Script for Smart Contract Analysis
============================================

PURPOSE:
--------
Fix common issues with collected smart contract datasets by:
1. Removing contracts with no meaningful features
2. Filtering out problematic contract types
3. Attempting to re-extract features for failed contracts
4. Creating clean datasets for ML training

HOW IT WORKS:
--------------
1. Load original dataset from collection
2. Create a backup (safety first!)
3. Filter out contracts with issues using clear criteria
4. Try to fix failed contracts with a retry mechanism
5. Save both filtered and updated datasets
6. Provide detailed logging and statistics

BEGINNER-FRIENDLY FEATURES:
--------------------------
✅ Clear variable names (no cryptic abbreviations)
✅ Step-by-step logging with progress indicators
✅ Error handling with try/except blocks
✅ Detailed comments explaining WHY we do each step
✅ Modular functions for each major operation
✅ Statistics reporting at the end

USAGE:
------
Run: poetry run python scripts/fix_dataset.py

OUTPUT:
-------
- data/collected_dataset_backup.csv (original backup)
- data/ml_dataset_filtered.csv (clean dataset for training)
- data/collected_dataset_updated.csv (with any newly extracted features)
- scripts/retry_failed_contracts.py (for manual retry of failed contracts)
"""

import pandas as pd
import shutil
from pathlib import Path
import logging

# Set up logging with clear formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Start with a clear header
    print("="*70)
    print("DATASET CLEANING SCRIPT FOR SMART CONTRACT ANALYSIS")
    print("="*70)
    
    # Load original dataset
    logger.info("Loading original dataset...")
    try:
        df = pd.read_csv('data/collected_dataset.csv')
        logger.info(f"✓ Loaded {len(df)} contracts")
    except FileNotFoundError:
        logger.error("❌ Dataset file not found! Run collection first.")
        return
    except Exception as e:
        logger.error(f"❌ Error loading dataset: {e}")
        return
    
    # Create backup (always good to have a backup)
    logger.info("Creating backup...")
    backup_path = Path('data/collected_dataset_backup.csv')
    try:
        df.to_csv(backup_path, index=False)
        logger.info(f"✓ Created backup: {backup_path}")
    except Exception as e:
        logger.error(f"❌ Error creating backup: {e}")
    
    # Filter out problematic contracts
    logger.info("Filtering problematic contracts...")
    df_filtered = filter_problematic_contracts(df)
    logger.info(f"✓ Filtered to {len(df_filtered)} contracts")
    
    # Save filtered dataset
    logger.info("Saving filtered dataset...")
    filtered_path = Path('data/ml_dataset_filtered.csv')
    try:
        df_filtered.to_csv(filtered_path, index=False)
        logger.info(f"✓ Saved filtered dataset: {filtered_path}")
    except Exception as e:
        logger.error(f"❌ Error saving filtered dataset: {e}")
    
    # Try to re-extract features for failed contracts
    logger.info("Attempting to re-extract features for failed contracts...")
    failed_contracts = get_failed_contracts(df_filtered)
    logger.info(f"Found {len(failed_contracts)} failed contracts")
    
    if failed_contracts:
        logger.info("Creating retry script...")
        create_retry_script(failed_contracts)
        logger.info("✓ Created retry script")
        
        logger.info("You can run it later with: poetry run python scripts/retry_failed_contracts.py")
    else:
        logger.info("✓ All contracts have meaningful features!")
    
    # Show final statistics
    show_dataset_statistics(df_filtered)
    
    # Done!
    print("\n" + "="*70)
    print("✅ DATASET CLEANING COMPLETE!")
    print("="*70)
    print(f"📊 Clean dataset: {len(df_filtered)} contracts")
    print(f"📄 Saved to: data/ml_dataset_filtered.csv")
    if failed_contracts:
        print(f"🔧 Retry script created for {len(failed_contracts)} contracts")
    print("💡 Next steps:")
    print("   1. Run: poetry run python scripts/retry_failed_contracts.py")
    print("   2. Then: poetry run python src/chainguardian/ml/training/train_baseline.py")
    print("="*70)

def filter_problematic_contracts(df):
    """
    Filter out contracts with common issues
    
    RETURNS:
        Filtered DataFrame with only good contracts
    """
    logger.info("Step 1: Removing contracts with all zero features...")
    
    # Get numeric columns (features that can have non-zero values)
    numeric_columns = [
        col for col in df.columns 
        if col not in ['contract_name', 'file_path', 'source']
    ]
    
    # Create a mask for contracts that have at least one non-zero feature
    has_features_mask = (df[numeric_columns] != 0).any(axis=1)
    df_with_features = df[has_features_mask].copy()
    
    logger.info(f"   - Removed {len(df) - len(df_with_features)} contracts with all zero features")
    
    logger.info("Step 2: Removing contracts with obvious issues...")
    
    # Remove Vyper contracts (often cause compilation issues)
    if 'source' in df_with_features.columns:
        df_with_features = df_with_features[
            ~df_with_features['source'].str.contains('vyper', case=False)
        ]
        logger.info(f"   - Removed Vyper contracts")
    
    # Remove obvious proxy contracts
    df_with_features = df_with_features[
        ~df_with_features['source'].str.contains('proxy', case=False)
    ]
    logger.info(f"   - Removed obvious proxy contracts")
    
    # Remove contracts with compilation errors
    df_with_features = df_with_features[
        ~df_with_features['contract_name'].str.contains('Error', case=False)
    ]
    logger.info(f"   - Removed contracts with compilation errors")
    
    logger.info(f"   - Remaining contracts: {len(df_with_features)}")
    
    return df_with_features

def get_failed_contracts(df):
    """
    Get list of contracts that failed feature extraction
    
    RETURNS:
        List of contract names that failed
    """
    # Get contracts that have no meaningful features
    numeric_columns = [
        col for col in df.columns 
        if col not in ['contract_name', 'file_path', 'source']
    ]
    
    # Create a mask for contracts that have all zero features
    has_no_features_mask = (df[numeric_columns] == 0).all(axis=1)
    df_no_features = df[has_no_features_mask]
    
    # Return the contract names
    return df_no_features['contract_name'].tolist()

def create_retry_script(failed_contracts):
    """
    Create a script to retry failed contracts
    
    This creates a separate script that can be run independently
    to attempt re-extraction of features for contracts that initially failed.
    """
    retry_script_content = f'''# Retry script for failed contracts
# Generated automatically by fix_dataset.py

import pandas as pd
from pathlib import Path
import logging
from chainguardian.feature_extraction.pipeline import FeaturePipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def retry_failed_contracts():
    # Load the dataset
    df = pd.read_csv('data/collected_dataset_backup.csv')
    
    # Get contracts that need retrying
    failed_contracts = {failed_contracts}
    
    print(f"Found {{len(failed_contracts)}} contracts to retry")
    
    # Initialize pipeline
    pipeline = FeaturePipeline()
    
    # Retry each contract
    for name in failed_contracts:
        print(f"Retrying: {{name}}")
        
        # Find the contract file
        contract_files = list(Path('blockchain/contracts/collected').glob(f'{{name}}*.sol'))
        
        if contract_files:
            contract_file = contract_files[0]
            try:
                features = pipeline.analyze_contract(contract_file, name)
                
                # Check if we got meaningful features
                numeric_features = [k for k in features.keys() 
                                      if k not in ['contract_name', 'file_path']]
                has_meaningful = any(features[k] != 0 and features[k] != False 
                                       for k in numeric_features)
                
                if has_meaningful:
                    print(f"  ✓ Successfully re-extracted features for {{name}}")
                    # Update the dataframe
                    mask = df['contract_name'] == name
                    for col in features:
                        if col in df.columns:
                            df.loc[mask, col] = features[col]
                else:
                    print(f"  ⚠️  Still no meaningful features for {{name}}")
            
            except Exception as e:
                print(f"  ❌ Failed to re-extract {{name}}: {{e}}")
    
    # Save updated dataframe
    df.to_csv('data/collected_dataset_updated.csv', index=False)
    print("✓ Updated dataset with any newly extracted features")

if __name__ == "__main__":
    retry_failed_contracts()
'''
    
    retry_path = Path('scripts/retry_failed_contracts.py')
    with open(retry_path, 'w') as f:
        f.write(retry_script_content)
    
    print(f"Created retry script: {retry_path}")

def show_dataset_statistics(df):
    """
    Display detailed statistics about the dataset
    """
    print("\n" + "="*70)
    print("📊 DATASET STATISTICS")
    print("="*70)
    print(f"Total contracts: {len(df)}")
    
    # Show vulnerability distribution
    vuln_columns = ['has_reentrancy', 'has_access_control_issues', 'has_timestamp_dependency', 'has_unchecked_call']
    vuln_present = [col for col in vuln_columns if col in df.columns]
    
    if vuln_present:
        print("\n🔍 Vulnerability Distribution:")
        for col in vuln_present:
            count = df[col].sum()
            percentage = (count / len(df)) * 100
            print(f"  {col}: {count} ({percentage:.1f}%)")
    
    # Show source distribution
    if 'source' in df.columns:
        print("\n📂 Source Distribution:")
        source_counts = df['source'].value_counts()
        for source, count in source_counts.items():
            print(f"  {source}: {count}")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()