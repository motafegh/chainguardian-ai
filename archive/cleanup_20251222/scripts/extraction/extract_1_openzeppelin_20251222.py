#!/usr/bin/env python3
"""
Extract OpenZeppelin Contracts - December 22, 2025

Source: data/safe_contracts/openzeppelin-contracts/contracts/
Label: SAFE (ground truth)
Expected: ~676 contracts
"""

from pathlib import Path
import logging
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from chainguardian.feature_extraction.pipeline import FeaturePipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def extract_openzeppelin():
    """Extract OpenZeppelin contracts (safe baseline)."""
    
    oz_dir = Path("data/safe_contracts/openzeppelin-contracts/contracts")
    
    if not oz_dir.exists():
        logger.error(f"❌ OpenZeppelin directory not found: {oz_dir}")
        logger.error("   Expected: data/safe_contracts/openzeppelin-contracts/")
        return None
    
    # Find all .sol files (including mocks - they're valid safe code)
    all_contracts = list(oz_dir.rglob("*.sol"))
    
    # Minimal filtering
    contracts = [
        c for c in all_contracts
        if 'test' not in c.parts
        and 'draft-' not in c.stem.lower()
        and not c.name.startswith('.')
    ]
    
    logger.info("="*80)
    logger.info("🔒 EXTRACTING OPENZEPPELIN CONTRACTS")
    logger.info("="*80)
    logger.info(f"Total found: {len(all_contracts)}")
    logger.info(f"After filtering: {len(contracts)}")
    logger.info(f"Including mocks: Yes (they're safe code)")
    logger.info(f"Data source: openzeppelin")
    logger.info("")
    
    pipeline = FeaturePipeline()
    success = 0
    failed = 0
    
    for i, contract_file in enumerate(contracts, 1):
        contract_name = contract_file.stem  # Use actual filename
        rel_path = contract_file.relative_to(oz_dir)
        
        try:
            logger.info(f"[{i}/{len(contracts)}] {rel_path}")
            
            metadata = {
                'data_source': 'openzeppelin',
                'ground_truth_label': 'safe',
                'ground_truth_vuln_type': 'none',
            }
            
            features = pipeline.analyze_contract(
                contract_file, 
                contract_name, 
                metadata=metadata
            )
            
            # Verify semantic extraction happened
            if features.get('failure_reason') is None:
                logger.info(f"   ✓ Semantic: CEI={features.get('cei_violations', 0)}, "
                          f"score={features.get('cei_pattern_score', 1.0):.2f}")
                success += 1
            else:
                logger.info(f"   ⚠️  Failed: {features.get('failure_reason')}")
                failed += 1
            
        except Exception as e:
            logger.error(f"   ❌ Unexpected error: {e}")
            failed += 1
    
    logger.info("")
    logger.info("="*80)
    logger.info("✅ OPENZEPPELIN EXTRACTION COMPLETE")
    logger.info("="*80)
    logger.info(f"Success: {success}/{len(contracts)} ({success/len(contracts)*100:.1f}%)")
    logger.info(f"Failed: {failed}/{len(contracts)} ({failed/len(contracts)*100:.1f}%)")
    logger.info("="*80 + "\n")
    
    # Verify in database
    from chainguardian.database.manager import DatabaseManager
    db = DatabaseManager()
    count = db._get_connection().cursor()
    count.execute("SELECT COUNT(*) FROM contracts WHERE data_source='openzeppelin'")
    db_count = count.fetchone()[0]
    count.close()
    
    logger.info(f"📊 Database verification: {db_count} contracts saved")
    
    return pipeline

if __name__ == "__main__":
    pipeline = extract_openzeppelin()
    if pipeline:
        pipeline.print_diagnostic_summary()
