"""
Extract Features from Already-Downloaded Contracts
==================================================

Skips scraping/downloading phases - uses existing contracts.
Perfect for iterating on feature extraction logic.

Usage:
    poetry run python scripts/extract_features_only.py
"""

import sys
from pathlib import Path
import logging
import yaml
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from chainguardian.feature_extraction.pipeline import FeaturePipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/feature_extraction_{datetime.now().strftime("%Y%m%d_%H%M")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def load_existing_contracts(contracts_dir: Path) -> list[tuple[Path, str]]:
    """
    Load all existing contracts from the collected directory.
    
    Returns:
        List of (contract_path, contract_name) tuples
    """
    contracts = []
    
    # Find all .sol files and directories
    for item in contracts_dir.iterdir():
        if item.is_file() and item.suffix == '.sol':
            # Single-file contract: ContractName_0xaddress.sol
            contract_name = item.stem.split('_')[0]  # Extract name before _
            contracts.append((item, contract_name))
            
        elif item.is_dir():
            # Multi-file contract: directory named ContractName_0xaddress/
            contract_name = item.name.split('_')[0]
            contracts.append((item, contract_name))
    
    logger.info(f"Found {len(contracts)} contracts in {contracts_dir}")
    return contracts


def extract_features_parallel(
    contracts: list[tuple[Path, str]],
    max_workers: int = 4
) -> FeaturePipeline:
    """
    Extract features from contracts in parallel.
    
    Args:
        contracts: List of (path, name) tuples
        max_workers: Number of parallel threads
    
    Returns:
        FeaturePipeline with extracted features
    """
    pipeline = FeaturePipeline()
    
    logger.info(f"Extracting features using {max_workers} threads...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_contract = {
            executor.submit(pipeline.analyze_contract, path, name): (path, name)
            for path, name in contracts
        }
        
        # Process with progress bar
        with tqdm(total=len(contracts), desc="Extracting features") as pbar:
            for future in as_completed(future_to_contract):
                path, name = future_to_contract[future]
                
                try:
                    features = future.result()
                    
                    # Check if successful
                    if features.get('failure_reason'):
                        pbar.set_postfix_str(f"❌ {name}")
                    else:
                        pbar.set_postfix_str(f"✅ {name}")
                    
                except Exception as e:
                    logger.error(f"Failed to process {name}: {e}")
                    pbar.set_postfix_str(f"💥 {name}")
                
                pbar.update(1)
    
    return pipeline


def main():
    """Main execution - extract features from existing contracts."""
    
    print("="*70)
    print("FEATURE EXTRACTION ONLY - Using Existing Contracts")
    print("="*70)
    
    # ========================================================================
    # STEP 1: LOAD EXISTING CONTRACTS
    # ========================================================================
    contracts_dir = project_root / "blockchain" / "contracts" / "collected"
    
    if not contracts_dir.exists():
        logger.error(f"Contracts directory not found: {contracts_dir}")
        logger.error("Run data collection first!")
        sys.exit(1)
    
    contracts = load_existing_contracts(contracts_dir)
    
    if not contracts:
        logger.error("No contracts found!")
        sys.exit(1)
    
    print(f"\n✅ Found {len(contracts)} contracts to analyze")
    
    # ========================================================================
    # STEP 2: EXTRACT FEATURES (PARALLEL)
    # ========================================================================
    pipeline = extract_features_parallel(
        contracts,
        max_workers=4  # Adjust based on your CPU
    )
    
    # ========================================================================
    # STEP 3: SAVE RESULTS
    # ========================================================================
    output_dir = project_root / "data"
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / "collected_dataset.csv"
    pipeline.save_dataset(output_path)
    
    print(f"\n✅ Dataset saved: {output_path}")
    print("\n" + "="*70)
    print("🎉 FEATURE EXTRACTION COMPLETE!")
    print("="*70)


if __name__ == "__main__":
    main()
