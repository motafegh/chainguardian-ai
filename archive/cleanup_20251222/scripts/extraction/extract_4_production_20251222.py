#!/usr/bin/env python3
"""
Extract Production Contracts - December 22, 2025

Source: data/production/
Expected: 45 vulnerable + 49 safe = 94 contracts
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

def extract_production():
    """Extract production safe and vulnerable contracts."""
    
    prod_dir = Path("data/production")
    
    if not prod_dir.exists():
        logger.error(f"❌ Production directory not found: {prod_dir}")
        return None
    
    safe_dir = prod_dir / "safe" / "raw"
    vuln_dir = prod_dir / "vulnerable" / "raw"
    
    safe_contracts = list(safe_dir.rglob("*.sol")) if safe_dir.exists() else []
    vuln_contracts = list(vuln_dir.rglob("*.sol")) if vuln_dir.exists() else []
    
    logger.info("="*80)
    logger.info("🏭 EXTRACTING PRODUCTION CONTRACTS")
    logger.info("="*80)
    logger.info(f"Safe: {len(safe_contracts)}")
    logger.info(f"Vulnerable: {len(vuln_contracts)}")
    logger.info(f"Total: {len(safe_contracts) + len(vuln_contracts)}")
    logger.info("")
    
    pipeline = FeaturePipeline()
    success = 0
    failed = 0
    
    # Extract safe contracts
    for i, contract_file in enumerate(safe_contracts, 1):
        contract_name = contract_file.stem
        
        try:
            logger.info(f"[SAFE {i}/{len(safe_contracts)}] {contract_name}")
            
            metadata = {
                'data_source': 'production_safe',
                'ground_truth_label': 'safe',
                'ground_truth_vuln_type': 'none',
            }
            
            features = pipeline.analyze_contract(contract_file, contract_name, metadata=metadata)
            
            if features.get('failure_reason') is None:
                success += 1
            else:
                failed += 1
                
        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
            failed += 1
    
    # Extract vulnerable contracts
    for i, contract_file in enumerate(vuln_contracts, 1):
        contract_name = contract_file.stem
        
        try:
            logger.info(f"[VULN {i}/{len(vuln_contracts)}] {contract_name}")
            
            metadata = {
                'data_source': 'production_vulnerable',
                'ground_truth_label': 'vulnerable',
                'ground_truth_vuln_type': 'production_bug',
            }
            
            features = pipeline.analyze_contract(contract_file, contract_name, metadata=metadata)
            
            if features.get('failure_reason') is None:
                success += 1
            else:
                failed += 1
                
        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
            failed += 1
    
    logger.info("")
    logger.info("="*80)
    logger.info("✅ PRODUCTION EXTRACTION COMPLETE")
    logger.info("="*80)
    logger.info(f"Success: {success}/{len(safe_contracts) + len(vuln_contracts)}")
    logger.info("="*80 + "\n")
    
    return pipeline

if __name__ == "__main__":
    pipeline = extract_production()
    if pipeline:
        pipeline.print_diagnostic_summary()
