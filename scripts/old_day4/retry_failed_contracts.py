# scripts/retry_failed_contracts.py

import pandas as pd
import concurrent.futures
from pathlib import Path
import logging
from chainguardian.feature_extraction.pipeline import FeaturePipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def retry_failed_contracts():
    df = pd.read_csv('data/collected_dataset_backup.csv')
    failed_contracts = df[~df[['has_reentrancy', 'has_access_control_issues', 'has_timestamp_dependency', 'has_unchecked_call']].any(axis=1)]['contract_name'].tolist()
    
    logger.info(f"Retrying {len(failed_contracts)} failed contracts")
    
    # Create a pipeline instance for parallel processing
    pipeline = FeaturePipeline()
    
    # Process in parallel (4 workers)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        
        for name in failed_contracts[:20]:  # Limit to first 20 for testing
            future = executor.submit(retry_single_contract, name, pipeline)
            futures.append(future)
        
        # Collect results
        results = []
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    
    # Update dataframe
    for result in results:
        if result['success']:
            mask = df['contract_name'] == result['name']
            for col in result['features']:
                if col in df.columns:
                    df.loc[mask, col] = result['features'][col]
    
    # Save updated dataframe
    df.to_csv('data/collected_dataset_updated.csv', index=False)
    logger.info(f"Updated {len(results)} contracts successfully")

def retry_single_contract(name, pipeline):
    try:
        # Find the contract file
        contract_files = list(Path('blockchain/contracts/collected').glob(f'{name}_*.sol'))
        
        if contract_files:
            contract_file = contract_files[0]
            features = pipeline.analyze_contract(contract_file, name)
            
            # Check if we got meaningful features
            numeric_features = [k for k in features.keys() 
                              if k not in ['contract_name', 'file_path']]
            has_meaningful = any(features[k] != 0 and features[k] != False 
                             for k in numeric_features)
            
            return {
                'success': has_meaningful,
                'name': name,
                'features': features
            }
        else:
            return {
                'success': False,
                'name': name,
                'error': 'No contract file found'
            }
    except Exception as e:
        return {
            'success': False,
            'name': name,
            'error': str(e)
        }

if __name__ == "__main__":
    retry_failed_contracts()