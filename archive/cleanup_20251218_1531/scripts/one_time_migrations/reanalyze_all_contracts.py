"""
Re-analyze all 319 contracts with expanded 58-feature extraction.

This will:
1. Fetch all contracts from database
2. Re-analyze with new feature extraction (58 features)
3. Update database with expanded features
4. Generate summary statistics
"""

from chainguardian.feature_extraction.pipeline import FeaturePipeline
from chainguardian.database.manager import DatabaseManager
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import logging
import pandas as pd
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/reanalysis_{pd.Timestamp.now().strftime("%Y%m%d_%H%M")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def reanalyze_contract(contract_row, pipeline):
    """Re-analyze a single contract with expanded features."""
    try:
        file_path = Path(contract_row['file_path'])
        contract_name = contract_row['contract_name']
        
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return {'status': 'file_not_found', 'contract': contract_name}
        
        # Re-analyze with 58 features
        features = pipeline.analyze_contract(file_path, contract_name)
        
        return {'status': 'success', 'contract': contract_name, 'features': features}
        
    except Exception as e:
        logger.error(f"Failed to re-analyze {contract_name}: {e}")
        return {'status': 'failed', 'contract': contract_name, 'error': str(e)}

def main():
    print("=" * 70)
    print("RE-ANALYZING ALL CONTRACTS WITH 58 FEATURES")
    print("=" * 70)
    
    # Get all contracts
    db = DatabaseManager()
    df = db.get_all_features()
    
    print(f"\n📊 Current database state:")
    print(f"   - Total contracts: {len(df)}")
    print(f"   - Feature columns: {len(df.columns)}")
    
    # Filter contracts to re-analyze
    contracts_to_analyze = df[df['file_path'].notna()]
    
    print(f"\n🎯 Contracts to re-analyze: {len(contracts_to_analyze)}")
    print(f"   (Skipping {len(df) - len(contracts_to_analyze)} without file paths)")
    
    confirm = input("\n⚠️  This will update the database. Continue? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Aborted.")
        return
    
    # Initialize pipeline
    print("\n🔧 Initializing pipeline...")
    pipeline = FeaturePipeline()
    
    # Re-analyze contracts (parallel)
    print("\n🚀 Starting re-analysis (parallel processing)...")
    
    results = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(reanalyze_contract, row, pipeline): idx
            for idx, row in contracts_to_analyze.iterrows()
        }
        
        with tqdm(total=len(contracts_to_analyze), desc="Re-analyzing") as pbar:
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                pbar.update(1)
    
    # Summary
    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = sum(1 for r in results if r['status'] == 'failed')
    
    print("\n" + "=" * 70)
    print("✅ RE-ANALYSIS COMPLETE!")
    print("=" * 70)
    print(f"\n📊 Results:")
    print(f"   - Successful: {success_count}")
    print(f"   - Failed: {failed_count}")
    print(f"   - Total: {len(results)}")
    
    # Get updated stats
    df_new = db.get_all_features()
    
    print(f"\n📈 New feature statistics:")
    print(f"   - Total features: {len(df_new.columns)}")
    print(f"   - High risk contracts: {df_new['is_high_risk'].sum()}")
    print(f"   - Avg risk score: {df_new['risk_score_simple'].mean():.2f}")
    print(f"   - Avg LOC: {df_new['lines_of_code'].mean():.0f}")
    
    print("\n➡️  Next: Train ML models with 58 features!")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    import pandas as pd
    main()
