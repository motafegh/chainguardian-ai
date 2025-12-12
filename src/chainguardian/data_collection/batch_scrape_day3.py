"""
Day 3 Batch Scraper - 70 Diverse Contracts
Stratified sampling: Top DeFi + Random + Vulnerable + Old
"""

from pathlib import Path
from chainguardian.data_collection.etherscan_scraper import EtherscanScraper
from chainguardian.feature_extraction.pipeline import FeaturePipeline
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_addresses(file_path: Path):
    """Load addresses from file (ignore comments and empty lines)"""
    addresses = []
    
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return addresses
    
    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                addr = line.split()[0]
                if addr.startswith('0x'):
                    addresses.append(addr)
    
    return addresses


def main():
    print("=" * 70)
    print("DAY 3 BATCH SCRAPER - DIVERSE DATASET COLLECTION")
    print("=" * 70)
    print()
    
    sources = {
        'Top 20 DeFi': 'data/address_lists/top20_defi.txt',
        'Random 30': 'data/address_lists/random30_verified.txt',
        'Vulnerable 15': 'data/address_lists/vulnerable15_known.txt',
        'Old 5': 'data/address_lists/old5_contracts.txt',
    }
    
    all_addresses = []
    
    for name, path in sources.items():
        addrs = load_addresses(Path(path))
        all_addresses.extend(addrs)
        logger.info(f"✓ {name}: {len(addrs)} addresses")
    
    print()
    print(f"📊 Total: {len(all_addresses)} addresses")
    print()
    
    all_addresses = list(set(all_addresses))
    logger.info(f"After dedup: {len(all_addresses)} unique")
    print()
    
    logger.info("🌐 Starting scraping...")
    print()
    
    scraper = EtherscanScraper()
    
    try:
        files = scraper.scrape_batch(
            all_addresses,
            output_dir=Path("blockchain/contracts/collected"),
            save_every=10
        )
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        files = list(Path("blockchain/contracts/collected").glob("*.sol"))
    
    print()
    logger.info(f"✅ Scraped {len(files)} contracts")
    print()
    
    logger.info("⏱️  Pausing 60 seconds...")
    time.sleep(60)
    print()
    
    logger.info("🔬 Extracting features...")
    print()
    
    pipeline = FeaturePipeline()
    
    success = 0
    failed = 0
    
    for i, file_path in enumerate(files, 1):
        try:
            contract_name = file_path.stem.split('_')[0]
            logger.info(f"[{i}/{len(files)}] {contract_name}...")
            pipeline.analyze_contract(file_path, contract_name)
            success += 1
            logger.info(f"  ✓ Success")
        except Exception as e:
            failed += 1
            logger.error(f"  ✗ {e}")
        print()
    
    output = Path("data/day3_diverse_features.csv")
    pipeline.save_dataset(output)
    
    df = pipeline.to_dataframe()
    
    print("=" * 70)
    print("COMPLETE")
    print("=" * 70)
    print(f"Success: {success}")
    print(f"Failed: {failed}")
    print(f"Dataset: {output}")
    print()
    print(f"Shape: {df.shape[0]} × {df.shape[1]}")
    print()
    print("Vulnerabilities:")
    print(f"  Reentrancy: {df['has_reentrancy'].sum()}")
    print(f"  Access Control: {df['has_access_control_issues'].sum()}")
    print()
    print("Severity:")
    print(f"  HIGH: {df['high_severity_count'].sum()}")
    print(f"  MEDIUM: {df['medium_severity_count'].sum()}")
    print("=" * 70)


if __name__ == "__main__":
    main()
