#!/usr/bin/env python3
"""
Extract Trail of Bits - December 22, 2025

Source: data/vulnerable_complex/trail_of_bits/
Label: VULNERABLE (known exploits)
Expected: ~25 contracts
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

def extract_trailofbits():
    """Extract Trail of Bits vulnerable contracts."""
    
    tob_dir = Path("data/vulnerable_complex/trail_of_bits")
    
    if not tob_dir.exists():
        logger.error(f"❌ Trail of Bits directory not found: {tob_dir}")
        return None
    
    contracts = list(tob_dir.rglob("*.sol"))
    
    logger.info("="*80)
    logger.info("⚠️  EXTRACTING TRAIL OF BITS (VULNERABLE)")
    logger.info("="*80)
    logger.info(f"Total found: {len(contracts)}")
    logger.info(f"Data source: trail_of_bits")
    logger.info("")
    
    pipeline = FeaturePipeline()
    success = 0
    failed = 0
    
    for i, contract_file in enumerate(contracts, 1):
        contract_name = contract_file.stem
        vuln_type = contract_file.parent.name  # directory name is vulnerability type
        
        try:
            logger.info(f"[{i}/{len(contracts)}] {contract_name} (type: {vuln_type})")
            
            metadata = {
                'data_source': 'trail_of_bits',
                'ground_truth_label': 'vulnerable',
                'ground_truth_vuln_type': vuln_type,
            }
            
            features = pipeline.analyze_contract(
                contract_file,
                contract_name,
                metadata=metadata
            )
            
            if features.get('failure_reason') is None:
                logger.info(f"   ✓ Semantic extracted successfully")
                success += 1
            else:
                logger.info(f"   ⚠️  {features.get('failure_reason')}")
                failed += 1
                
        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
            failed += 1
    
    logger.info("")
    logger.info("="*80)
    logger.info("✅ TRAIL OF BITS EXTRACTION COMPLETE")
    logger.info("="*80)
    logger.info(f"Success: {success}/{len(contracts)}")
    logger.info("="*80 + "\n")
    
    return pipeline

if __name__ == "__main__":
    pipeline = extract_trailofbits()
    if pipeline:
        pipeline.print_diagnostic_summary()
