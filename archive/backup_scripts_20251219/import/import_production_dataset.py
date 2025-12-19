"""
Import Production Dataset to Database

Imports collected production contracts with proper labeling:
- Vulnerable contracts → label = 1
- Safe contracts → label = 0
"""

from pathlib import Path
import logging
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from chainguardian.feature_extraction.pipeline import FeaturePipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def import_production_vulnerable():
    """Import vulnerable contracts from production collection."""
    
    pipeline = FeaturePipeline()
    
    vuln_dir = Path("data/production/vulnerable/raw")
    
    if not vuln_dir.exists():
        logger.error(f"❌ Vulnerable contracts directory not found: {vuln_dir}")
        logger.error(f"   Run master collector first!")
        return
    
    # Find all .sol files (handles both single files and directories)
    contracts = list(vuln_dir.glob("*.sol"))
    contracts.extend(vuln_dir.glob("*/")) # Multi-file contracts
    
    # Filter to only directories and single .sol files
    contracts = [c for c in contracts if c.is_file() or (c.is_dir() and not c.name.startswith('.'))]
    
    logger.info("="*70)
    logger.info(f"🔥 IMPORTING VULNERABLE CONTRACTS")
    logger.info("="*70)
    logger.info(f"Found {len(contracts)} contracts to process")
    logger.info("")
    
    for i, contract_path in enumerate(contracts, 1):
        contract_name = contract_path.stem if contract_path.is_file() else contract_path.name
        
        try:
            logger.info(f"[{i}/{len(contracts)}] Processing: {contract_name}")
            
            metadata = {
                'data_source': 'production_vulnerable',
                'ground_truth_label': 'vulnerable',
                'ground_truth_vuln_type': 'mixed',  # Real exploits have various types
            }
            
            pipeline.analyze_contract(contract_path, contract_name, metadata=metadata)
            
        except Exception as e:
            logger.error(f"   ❌ Failed: {e}")
    
    logger.info("")
    logger.info("="*70)
    logger.info("✅ VULNERABLE IMPORT COMPLETE")
    logger.info("="*70)
    
    return pipeline


def import_production_safe():
    """Import safe contracts from production collection."""
    
    pipeline = FeaturePipeline()
    
    safe_dir = Path("data/production/safe/raw")
    
    if not safe_dir.exists():
        logger.error(f"❌ Safe contracts directory not found: {safe_dir}")
        logger.error(f"   Run master collector first!")
        return
    
    # Find all .sol files
    contracts = list(safe_dir.glob("*.sol"))
    contracts.extend(safe_dir.glob("*/"))
    
    contracts = [c for c in contracts if c.is_file() or (c.is_dir() and not c.name.startswith('.'))]
    
    logger.info("="*70)
    logger.info(f"🔒 IMPORTING SAFE CONTRACTS")
    logger.info("="*70)
    logger.info(f"Found {len(contracts)} contracts to process")
    logger.info("")
    
    for i, contract_path in enumerate(contracts, 1):
        contract_name = contract_path.stem if contract_path.is_file() else contract_path.name
        
        try:
            logger.info(f"[{i}/{len(contracts)}] Processing: {contract_name}")
            
            metadata = {
                'data_source': 'production_safe',
                'ground_truth_label': 'safe',
                'ground_truth_vuln_type': 'none',
            }
            
            pipeline.analyze_contract(contract_path, contract_name, metadata=metadata)
            
        except Exception as e:
            logger.error(f"   ❌ Failed: {e}")
    
    logger.info("")
    logger.info("="*70)
    logger.info("✅ SAFE IMPORT COMPLETE")
    logger.info("="*70)
    
    return pipeline


def main():
    """Run complete production dataset import."""
    
    logger.info("")
    logger.info("╔"+"="*68+"╗")
    logger.info("║" + " "*15 + "PRODUCTION DATASET IMPORT" + " "*27 + "║")
    logger.info("╚"+"="*68+"╝")
    logger.info("")
    
    # Import vulnerable
    pipeline_vuln = import_production_vulnerable()
    
    # Import safe
    pipeline_safe = import_production_safe()
    
    # Combined diagnostic
    if pipeline_vuln and pipeline_safe:
        logger.info("")
        logger.info("="*70)
        logger.info("📊 COMBINED DIAGNOSTIC SUMMARY")
        logger.info("="*70)
        pipeline_vuln.print_diagnostic_summary()
    
    logger.info("")
    logger.info("="*70)
    logger.info("🎉 PRODUCTION IMPORT COMPLETE!")
    logger.info("="*70)
    logger.info("")
    logger.info("📋 NEXT: Verify dataset")
    logger.info("   poetry run python scripts/analysis/verify_dataset.py")
    logger.info("="*70)


if __name__ == "__main__":
    main()