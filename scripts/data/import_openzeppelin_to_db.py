"""
Import OpenZeppelin contracts as "safe" examples.
"""
from pathlib import Path
from chainguardian.feature_extraction.pipeline import FeaturePipeline
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_openzeppelin():
    """Import OpenZeppelin safe contracts."""
    
    oz_dir = Path("data/safe_contracts/openzeppelin_all")
    
    if not oz_dir.exists():
        logger.error(f"OpenZeppelin directory not found: {oz_dir}")
        logger.info("Run: poetry run python scripts/data/download_openzeppelin.py")
        return
    
    pipeline = FeaturePipeline()
    contracts = list(oz_dir.glob("*.sol"))
    
    logger.info(f"\n{'='*70}")
    logger.info(f"Importing {len(contracts)} OpenZeppelin contracts")
    logger.info(f"{'='*70}\n")
    
    successful = 0
    failed = 0
    
    for i, contract_file in enumerate(contracts, 1):
        contract_name = contract_file.stem
        
        try:
            # Extract features
            features = pipeline.analyze_contract(contract_file, contract_name)
            
            # ✅ ADD GROUND TRUTH METADATA
            features['address'] = None  # No address
            features['ground_truth_label'] = 'safe'
            features['ground_truth_vuln_type'] = 'none'
            features['data_source'] = 'openzeppelin'
            
            successful += 1
            
            if i % 25 == 0:
                logger.info(f"Progress: {i}/{len(contracts)} ({i/len(contracts)*100:.1f}%)")
            
        except Exception as e:
            failed += 1
            logger.error(f"✗ {contract_name}: {e}")
    
    # Summary
    logger.info(f"\n{'='*70}")
    logger.info(f"OPENZEPPELIN IMPORT SUMMARY")
    logger.info(f"{'='*70}")
    logger.info(f"Total contracts: {len(contracts)}")
    logger.info(f"Successful: {successful} ({successful/len(contracts)*100:.1f}%)")
    logger.info(f"Failed: {failed}")
    
    pipeline.print_diagnostic_summary()

if __name__ == "__main__":
    import_openzeppelin()
