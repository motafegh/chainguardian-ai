"""
Import ALL OpenZeppelin contracts with proper dependency resolution.

This script:
1. Finds all .sol files in OpenZeppelin repo
2. Uses the repo root as base path (for import resolution)
3. Analyzes each contract with Slither (resolves imports automatically)
4. Extracts 85 features per contract
5. Labels all as "safe" (ground truth)
"""

from pathlib import Path
from chainguardian.feature_extraction.pipeline import FeaturePipeline
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to cloned OpenZeppelin repo
OZ_REPO = Path("data/safe_contracts/openzeppelin-contracts")
OZ_CONTRACTS_DIR = OZ_REPO / "contracts"

def get_all_oz_contracts():
    """Get all .sol files in OpenZeppelin contracts directory."""
    
    if not OZ_CONTRACTS_DIR.exists():
        logger.error(f"OpenZeppelin contracts directory not found: {OZ_CONTRACTS_DIR}")
        logger.info("Run: cd data/safe_contracts && git clone https://github.com/OpenZeppelin/openzeppelin-contracts.git")
        return []
    
    # Find all .sol files, excluding mocks and test files
    all_contracts = list(OZ_CONTRACTS_DIR.rglob("*.sol"))
    
    # Filter out test/mock contracts (not production code)
    filtered_contracts = [
        c for c in all_contracts
        if 'mock' not in c.parts  # Skip mocks/
        and 'test' not in c.parts  # Skip test/
        and 'draft-' not in c.stem.lower()  # Skip draft implementations
    ]
    
    logger.info(f"Found {len(all_contracts)} total contracts")
    logger.info(f"Filtered to {len(filtered_contracts)} production contracts")
    
    return filtered_contracts


def import_openzeppelin_full():
    """
    Import all OpenZeppelin contracts with proper dependency resolution.
    
    Key insight: Pass the CONTRACT FILE path to Slither, not the repo root.
    Slither will resolve imports relative to the file's directory.
    """
    
    contracts = get_all_oz_contracts()
    
    if not contracts:
        logger.error("No contracts found!")
        return
    
    pipeline = FeaturePipeline()
    
    logger.info(f"\n{'='*70}")
    logger.info(f"IMPORTING {len(contracts)} OPENZEPPELIN CONTRACTS")
    logger.info(f"{'='*70}\n")
    
    successful = 0
    failed = 0
    
    for i, contract_file in enumerate(contracts, 1):
        # Get contract name from filename
        contract_name = contract_file.stem
        
        # Get relative path for better logging
        rel_path = contract_file.relative_to(OZ_CONTRACTS_DIR)
        
        try:
            logger.info(f"\n[{i}/{len(contracts)}] Processing: {rel_path}")
            
            # Extract features
            # KEY: Pass absolute path to contract file
            # Slither will resolve imports relative to this file's directory
            metadata = {
                'address': None,
                'data_source': 'openzeppelin',
                'ground_truth_label': 'safe',
                'ground_truth_vuln_type': 'none',
            }

            # Pass metadata to pipeline
            features = pipeline.analyze_contract(contract_file, contract_name, metadata=metadata)
                        
            # Check if extraction was successful
            if not features.get('failure_reason'):
                successful += 1
                logger.info(f"  ✓ Success: {contract_name}")
            else:
                failed += 1
                reason = features.get('failure_reason', 'UNKNOWN')
                logger.warning(f"  ✗ Failed: {contract_name} ({reason})")
            
            # Progress update every 25 contracts
            if i % 25 == 0:
                logger.info(f"\n{'─'*70}")
                logger.info(f"Progress: {i}/{len(contracts)} ({i/len(contracts)*100:.1f}%)")
                logger.info(f"Success: {successful} | Failed: {failed}")
                logger.info(f"{'─'*70}")
            
        except KeyboardInterrupt:
            logger.warning("\n⚠️  Import interrupted by user")
            break
            
        except Exception as e:
            failed += 1
            logger.error(f"  ✗ Unexpected error in {contract_name}: {e}")
    
    # Final summary
    logger.info(f"\n{'='*70}")
    logger.info(f"OPENZEPPELIN IMPORT COMPLETE")
    logger.info(f"{'='*70}")
    logger.info(f"Total contracts: {len(contracts)}")
    logger.info(f"Successful: {successful} ({successful/len(contracts)*100:.1f}%)")
    logger.info(f"Failed: {failed} ({failed/len(contracts)*100:.1f}%)")
    logger.info(f"{'='*70}\n")
    
    # Detailed diagnostic
    pipeline.print_diagnostic_summary()


if __name__ == "__main__":
    import_openzeppelin_full()
