#!/usr/bin/env python3
"""
Extract SmartBugs Curated - December 22, 2025

Source: data/smartbugs_curated/dataset/
Label: VULNERABLE (known bugs)
Expected: ~143 contracts
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

def extract_smartbugs():
    """Extract SmartBugs Curated vulnerable contracts."""
    
    smartbugs_dir = Path("data/smartbugs_curated/dataset")
    
    if not smartbugs_dir.exists():
        logger.error(f"❌ SmartBugs directory not found: {smartbugs_dir}")
        return None
    
    # Find all .sol files in vulnerability subdirectories
    contracts = list(smartbugs_dir.rglob("*.sol"))
    
    logger.info("="*80)
    logger.info("⚠️  EXTRACTING SMARTBUGS CURATED (VULNERABLE)")
    logger.info("="*80)
    logger.info(f"Total found: {len(contracts)}")
    logger.info(f"Data source: smartbugs_curated")
    logger.info(f"Ground truth: VULNERABLE")
    logger.info("")
    
    pipeline = FeaturePipeline()
    success = 0
    failed = 0
    
    for i, contract_file in enumerate(contracts, 1):
        contract_name = contract_file.stem
        
        # Extract vulnerability type from directory structure
        # e.g., dataset/reentrancy/dao.sol -> vuln_type = reentrancy
        vuln_type = contract_file.parent.name
        
        try:
            logger.info(f"[{i}/{len(contracts)}] {contract_name} (type: {vuln_type})")
            
            metadata = {
                'data_source': 'smartbugs_curated',
                'ground_truth_label': 'vulnerable',
                'ground_truth_vuln_type': vuln_type,
            }
            
            features = pipeline.analyze_contract(
                contract_file,
                contract_name,
                metadata=metadata
            )
            
            if features.get('failure_reason') is None:
                logger.info(f"   ✓ CEI violations={features.get('cei_violations', 0)}, "
                          f"has_reentrancy={features.get('has_reentrancy', False)}")
                success += 1
            else:
                logger.info(f"   ⚠️  {features.get('failure_reason')}")
                failed += 1
                
        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
            failed += 1
    
    logger.info("")
    logger.info("="*80)
    logger.info("✅ SMARTBUGS EXTRACTION COMPLETE")
    logger.info("="*80)
    logger.info(f"Success: {success}/{len(contracts)} ({success/len(contracts)*100:.1f}%)")
    logger.info(f"Failed: {failed}/{len(contracts)}")
    logger.info("="*80 + "\n")
    
    return pipeline

if __name__ == "__main__":
    pipeline = extract_smartbugs()
    if pipeline:
        pipeline.print_diagnostic_summary()
