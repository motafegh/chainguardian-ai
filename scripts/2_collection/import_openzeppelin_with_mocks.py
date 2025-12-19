"""
Import OpenZeppelin Contracts (Including Mocks)

Mocks are valid safe contracts - they're used in testing
but contain real, production-quality code patterns.
"""

from pathlib import Path
import logging
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from chainguardian.feature_extraction.pipeline import FeaturePipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def import_openzeppelin_with_mocks():
    """Import OpenZeppelin contracts including mocks."""
    
    pipeline = FeaturePipeline()
    
    oz_dir = Path("data/safe_contracts/openzeppelin-contracts/contracts")
 
    if not oz_dir.exists():
        logger.error(f"❌ OpenZeppelin directory not found: {oz_dir}")
        return
    
    # Find all .sol files
    all_contracts = list(oz_dir.rglob("*.sol"))
    
    # Less aggressive filtering (keep mocks!)
    contracts = [
        c for c in all_contracts
        if 'test' not in c.parts  # Remove only test/
        and 'draft-' not in c.stem.lower()  # Remove drafts
        and not c.name.startswith('.')  # Remove hidden files
    ]
    
    logger.info("="*70)
    logger.info("🔒 IMPORTING OPENZEPPELIN (WITH MOCKS)")
    logger.info("="*70)
    logger.info(f"Total available: {len(all_contracts)}")
    logger.info(f"After filtering: {len(contracts)}")
    logger.info(f"Including mocks: Yes")
    logger.info("")
    
    success = 0
    failed = 0
    
    for i, contract_file in enumerate(contracts, 1):
        contract_name = f"oz_{contract_file.stem}"
        
        try:
            logger.info(f"[{i}/{len(contracts)}] {contract_file.relative_to(oz_dir)}")
            
            metadata = {
                'data_source': 'openzeppelin',
                'ground_truth_label': 'safe',
                'ground_truth_vuln_type': 'none',
            }
            
            pipeline.analyze_contract(contract_file, contract_name, metadata=metadata)
            success += 1
            
        except Exception as e:
            logger.error(f"   ❌ Failed: {e}")
            failed += 1
    
    logger.info("")
    logger.info("="*70)
    logger.info("✅ OPENZEPPELIN IMPORT COMPLETE")
    logger.info("="*70)
    logger.info(f"   Success: {success}/{len(contracts)}")
    logger.info(f"   Failed: {failed}/{len(contracts)}")
    logger.info("="*70)
    
    return pipeline


if __name__ == "__main__":
    pipeline = import_openzeppelin_with_mocks()
    if pipeline:
        pipeline.print_diagnostic_summary()
