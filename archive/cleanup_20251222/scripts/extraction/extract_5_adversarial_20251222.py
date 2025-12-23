#!/usr/bin/env python3
"""
Extract Adversarial Test Contracts - December 22, 2025

Source: test_contracts/
Expected: 25 edge-case contracts
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

def extract_adversarial():
    """Extract adversarial test contracts with VERBOSE semantic logging."""
    
    test_dir = Path("test_contracts")
    
    if not test_dir.exists():
        logger.error(f"❌ Test contracts directory not found: {test_dir}")
        return None
    
    contracts = list(test_dir.glob("*.sol"))
    
    logger.info("="*80)
    logger.info("🎯 EXTRACTING ADVERSARIAL TEST SET")
    logger.info("="*80)
    logger.info(f"Total found: {len(contracts)}")
    logger.info(f"Data source: adversarial_test")
    logger.info("")
    
    pipeline = FeaturePipeline()
    success = 0
    failed = 0
    
    for i, contract_file in enumerate(contracts, 1):
        contract_name = contract_file.stem
        
        # Label based on contract name
        is_vulnerable = any(keyword in contract_name.lower() for keyword in [
            'reentrancy', 'vulnerable', 'danger', 'exploit', 
            'honeypot', 'delegatecall', 'front_running', 'intentional'
        ])
        
        try:
            logger.info(f"[{i}/{len(contracts)}] {contract_name} ({'VULN' if is_vulnerable else 'SAFE'})")
            
            metadata = {
                'data_source': 'adversarial_test',
                'ground_truth_label': 'vulnerable' if is_vulnerable else 'safe',
                'ground_truth_vuln_type': 'adversarial_edge_case',
            }
            
            features = pipeline.analyze_contract(
                contract_file,
                contract_name,
                metadata=metadata
            )
            
            # VERBOSE SEMANTIC LOGGING
            if features.get('failure_reason') is None:
                logger.info(f"   ✓ SUCCESS")
                logger.info(f"   📊 Semantic features:")
                logger.info(f"      - CEI violations: {features.get('cei_violations', 0)}")
                logger.info(f"      - CEI score: {features.get('cei_pattern_score', 1.0):.3f}")
                logger.info(f"      - State after call: {features.get('state_after_call_count', 0)}")
                logger.info(f"      - Has reentrancy guard: {features.get('has_reentrancy_guard', False)}")
                logger.info(f"      - Unchecked in critical: {features.get('unchecked_calls_in_critical_context', 0)}")
                success += 1
            else:
                logger.info(f"   ❌ FAILED: {features.get('failure_reason')}")
                logger.info(f"      Error: {features.get('error_message', '')[:100]}")
                failed += 1
                
        except Exception as e:
            logger.error(f"   ❌ Unexpected error: {e}")
            failed += 1
    
    logger.info("")
    logger.info("="*80)
    logger.info("✅ ADVERSARIAL EXTRACTION COMPLETE")
    logger.info("="*80)
    logger.info(f"Success: {success}/{len(contracts)}")
    logger.info(f"Failed: {failed}/{len(contracts)}")
    
    if success == 0:
        logger.error("⚠️  ALL ADVERSARIAL CONTRACTS FAILED!")
        logger.error("   This means semantic features will be ZERO for adversarial set")
    
    logger.info("="*80 + "\n")
    
    return pipeline

if __name__ == "__main__":
    pipeline = extract_adversarial()
    if pipeline:
        pipeline.print_diagnostic_summary()
