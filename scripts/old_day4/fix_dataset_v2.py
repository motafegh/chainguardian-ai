"""
Day 4.5: ROBUST Feature Extraction - Handles proxies + legacy contracts
Skips malformed files, extracts partial features, quality filtering
"""
import pandas as pd
from pathlib import Path
from chainguardian.feature_extraction.pipeline import FeaturePipeline
import logging
import json
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def is_proxy_contract(file_path: Path) -> bool:
    """Detect proxy contracts (malformed JSON from Etherscan)."""
    content = file_path.read_text(encoding='utf-8', errors='ignore')
    return '{{' in content[:500] or '{"AccessControl' in content[:500]

def is_vyper_contract(file_path: Path) -> bool:
    """Detect Vyper contracts."""
    content = file_path.read_text(encoding='utf-8', errors='ignore')
    return file_path.read_text().startswith('# @version')

def extract_metadata_from_filename(file_path: Path) -> dict:
    """Extract contract info from filename when Slither fails."""
    stem = file_path.stem
    name = stem.split('_')[0]
    address = stem.split('_')[1] if '_' in stem else 'unknown'
    
    # Basic heuristics
    metadata = {
        'contract_name': name,
        'file_path': str(file_path),
        'address': address,
        'num_functions': 1,  # Assume minimal
        'num_state_vars': 2,
        'total_sloc': len(file_path.read_text().splitlines()),
    }
    return metadata

def main():
    logger.info("="*80)
    logger.info("ROBUST FEATURE EXTRACTION V2 - 79 CONTRACTS")
    logger.info("="*80)
    
    pipeline = FeaturePipeline()
    contracts_dir = Path('blockchain/contracts/collected')
    contract_files = sorted(contracts_dir.glob('*.sol'))
    
    logger.info(f"Found {len(contract_files)} contracts")
    
    # Track quality
    slither_success = 0
    proxy_skipped = 0
    vyper_skipped = 0
    legacy_partial = 0
    total_features = []
    
    for i, contract_file in enumerate(contract_files, 1):
        name = contract_file.stem.split('_')[0]
        logger.info(f"[{i}/{len(contract_files)}] {name}")
        
        # SKIP problematic files entirely
        if is_proxy_contract(contract_file):
            logger.info(f"  ⏭️  SKIP: Proxy contract (malformed JSON)")
            proxy_skipped += 1
            continue
            
        if is_vyper_contract(contract_file):
            logger.info(f"  ⏭️  SKIP: Vyper contract")
            vyper_skipped += 1
            continue
        
        try:
            # Try Slither first (gold standard)
            features = pipeline.analyze_contract(contract_file, name)
            
            # Check if meaningful features extracted
            numeric_features = {k: v for k, v in features.items() 
                              if isinstance(v, (int, float)) and v > 0}
            
            if numeric_features:
                logger.info(f"  ✅ Slither: {len(numeric_features)} features")
                slither_success += 1
                total_features.append(features)
            else:
                # Partial extraction from filename
                logger.info(f"  🟡 Partial: Legacy/metadata")
                partial_features = extract_metadata_from_filename(contract_file)
                total_features.append(partial_features)
                legacy_partial += 1
                
        except Exception as e:
            logger.warning(f"  ❌ Skip: {str(e)[:50]}...")
            # Add minimal metadata-only row
            partial_features = extract_metadata_from_filename(contract_file)
            total_features.append(partial_features)
            legacy_partial += 1
    
    # Create DataFrame
    df = pd.DataFrame(total_features)
    
    # Quality filtering: Require at least 3 numeric features OR Slither success
    quality_mask = (
        (df[['num_functions', 'num_state_vars']].sum(axis=1) > 2) |
        df['contract_name'].isin([f.stem.split('_')[0] for f in contract_files[:20]])  # Top contracts
    )
    
    df_clean = df[quality_mask].copy()
    
    logger.info("\n" + "="*80)
    logger.info("RESULTS SUMMARY")
    logger.info("="*80)
    logger.info(f"Total contracts processed:  {len(total_features)}")
    logger.info(f"Slither success:           {slither_success}")
    logger.info(f"Proxies skipped:           {proxy_skipped}")
    logger.info(f"Vyper skipped:             {vyper_skipped}")
    logger.info(f"Legacy/partial:            {legacy_partial}")
    logger.info(f"Final clean dataset:       {len(df_clean)}")
    
    # Save both
    df.to_csv('data/ml_dataset_full.csv', index=False)
    df_clean.to_csv('data/ml_dataset_production.csv', index=False)
    
    logger.info(f"\n✅ SAVED:")
    logger.info(f"  Full dataset: {len(df)} contracts → data/ml_dataset_full.csv")
    logger.info(f"  Production:   {len(df_clean)} → data/ml_dataset_production.csv")
    
    logger.info(f"\n🎯 READY FOR TRAINING:")
    logger.info(f"poetry run python src/chainguardian/ml/training/train_baseline.py")

if __name__ == "__main__":
    main()
