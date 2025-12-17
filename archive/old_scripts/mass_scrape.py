"""
Mass Contract Scraping Script

Scrapes thousands of contracts with:
- Redis caching & progress tracking
- Automatic resume after crashes
- Real-time statistics
- Error handling
- Parallel processing

Usage:
    # Scrape 5000 verified contracts
    python scripts/mass_scrape.py --max 5000 --workers 5
    
    # Resume previous scrape
    python scripts/mass_scrape.py --resume
    
    # Scrape from address file
    python scripts/mass_scrape.py --file data/contract_addresses.txt
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import logging
from datetime import datetime
from blockchain.contracts.etherscan_scraper_redis import RedisEtherscanScraper
from scripts.discover_contracts import ContractDiscovery

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def mass_scrape(
    max_contracts: int = 5000,
    workers: int = 5,
    strategy: str = "verified",
    output_dir: Path = None,
    address_file: Path = None
):
    """
    Mass scrape contracts with progress tracking.
    
    Args:
        max_contracts: Maximum contracts to scrape
        workers: Parallel workers
        strategy: Discovery strategy (if not using file)
        output_dir: Where to save contracts
        address_file: File with addresses (one per line)
    """
    output_dir = output_dir or Path("blockchain/contracts/mass_collection")
    
    logger.info(f"\n{'='*70}")
    logger.info(f"CHAINGUARDIAN - MASS CONTRACT SCRAPING")
    logger.info(f"{'='*70}")
    logger.info(f"Target: {max_contracts} contracts")
    logger.info(f"Workers: {workers}")
    logger.info(f"Output: {output_dir}")
    logger.info(f"Strategy: {strategy}")
    logger.info(f"{'='*70}\n")
    
    # Initialize scraper
    scraper = RedisEtherscanScraper(use_redis=True)
    
    # Get contract addresses
    if address_file and address_file.exists():
        logger.info(f"Loading addresses from {address_file}...")
        with open(address_file, 'r') as f:
            addresses = [line.strip() for line in f if line.strip()]
        logger.info(f"✓ Loaded {len(addresses)} addresses from file")
    else:
        logger.info("Discovering contract addresses...")
        discovery = ContractDiscovery()
        addresses = discovery.discover_contracts(
            strategy=strategy,
            max_contracts=max_contracts
        )
    
    # Limit to max_contracts
    addresses = addresses[:max_contracts]
    
    # Show Redis stats before starting
    stats = scraper.get_stats()
    logger.info(f"\nRedis Stats (before):")
    logger.info(f"  Already processed: {stats.get('processed_contracts', 0)}")
    logger.info(f"  Cache hit rate: {stats.get('cache_hit_rate', 0):.1f}%")
    
    # Start scraping
    logger.info(f"\n{'='*70}")
    logger.info(f"Starting scrape at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"{'='*70}\n")
    
    start_time = datetime.now()
    
    saved_files = scraper.scrape_batch(
        addresses=addresses,
        output_dir=output_dir,
        save_every=50,  # Log every 50 contracts
        max_workers=workers,
        skip_processed=True  # Skip already processed
    )
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Final statistics
    logger.info(f"\n{'='*70}")
    logger.info(f"SCRAPING COMPLETE!")
    logger.info(f"{'='*70}")
    logger.info(f"Duration: {duration:.0f}s ({duration/60:.1f} minutes)")
    logger.info(f"Contracts saved: {len(saved_files)}")
    logger.info(f"Rate: {len(saved_files)/duration:.2f} contracts/second")
    
    # Redis stats after
    final_stats = scraper.get_stats()
    logger.info(f"\nRedis Stats (after):")
    logger.info(f"  Total processed: {final_stats['processed_contracts']}")
    logger.info(f"  Cache hits: {final_stats['cache_hits']}")
    logger.info(f"  Cache hit rate: {final_stats['cache_hit_rate']:.1f}%")
    logger.info(f"  Total API requests: {final_stats['total_requests']}")
    
    logger.info(f"\n✓ Contracts saved to: {output_dir}")
    logger.info(f"{'='*70}\n")
    
    return saved_files


def main():
    parser = argparse.ArgumentParser(
        description='Mass scrape smart contracts from Etherscan'
    )
    
    parser.add_argument(
        '--max',
        type=int,
        default=5000,
        help='Maximum contracts to scrape (default: 5000)'
    )
    
    parser.add_argument(
        '--workers',
        type=int,
        default=5,
        help='Number of parallel workers (default: 5)'
    )
    
    parser.add_argument(
        '--strategy',
        choices=['verified', 'popular', 'blocks', 'all'],
        default='verified',
        help='Contract discovery strategy (default: verified)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Output directory for contracts'
    )
    
    parser.add_argument(
        '--file',
        type=str,
        help='File with contract addresses (one per line)'
    )
    
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume previous scrape (uses Redis processed set)'
    )
    
    args = parser.parse_args()
    
    # Set output directory
    output_dir = Path(args.output) if args.output else None
    address_file = Path(args.file) if args.file else None
    
    # Run mass scrape
    try:
        saved = mass_scrape(
            max_contracts=args.max,
            workers=args.workers,
            strategy=args.strategy,
            output_dir=output_dir,
            address_file=address_file
        )
        
        print(f"\n✅ SUCCESS: {len(saved)} contracts scraped!")
        sys.exit(0)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user")
        print("✓ Progress saved to Redis - run with --resume to continue")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        print("✓ Progress saved to Redis - run with --resume to continue")
        sys.exit(1)


if __name__ == "__main__":
    main()
