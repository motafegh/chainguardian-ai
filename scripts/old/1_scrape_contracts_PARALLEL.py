"""
PHASE 1: Contract Scraping with PARALLEL PROCESSING
====================================================

Collect .sol files from Etherscan using ThreadPoolExecutor for I/O-bound tasks.
Output: blockchain/contracts/collected/*.sol

Features:
- Parallel scraping with rate limiting
- Thread-safe checkpoint tracking
- Resume capability
- Metadata tracking (address → file mapping)
- Respects Etherscan rate limits (5 calls/sec)

Performance: 2-3x faster than sequential (30 min → 10-15 min)
"""

import yaml
import json
from pathlib import Path
import logging
from typing import List, Dict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import threading

from chainguardian.data_collection.collectors.defi_llama import DeFiLlamaCollector
from chainguardian.data_collection.collectors.coingecko import CoinGeckoCollector
from chainguardian.data_collection.collectors.manual_curated import ManualCuratedCollector
from chainguardian.data_collection.strategies.stratified_sampling import StratifiedSampler
from chainguardian.data_collection.etherscan_scraper import EtherscanScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ParallelScrapingPipeline:
    """Phase 1: Scrape contracts from Etherscan with parallel processing"""

    def __init__(self, config_path: str, max_workers: int = 4):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        self.max_workers = max_workers
        self.output_dir = Path("blockchain/contracts/collected")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Thread-safe checkpoint file
        self.checkpoint_file = Path("data/scraping_checkpoint.json")
        self.checkpoint_lock = threading.Lock()
        self.checkpoint = self._load_checkpoint()

        self.sampler = StratifiedSampler(
            target_size=self.config['dataset']['target_size']
        )

    def _load_checkpoint(self) -> Dict:
        """Load checkpoint of already-scraped contracts"""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file) as f:
                return json.load(f)
        return {"scraped_addresses": [], "scraped_files": {}}

    def _save_checkpoint(self):
        """Save checkpoint (thread-safe)"""
        with self.checkpoint_lock:
            self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.checkpoint_file, 'w') as f:
                json.dump(self.checkpoint, f, indent=2)

    def scrape(self):
        """Execute parallel scraping pipeline"""
        logger.info("="*70)
        logger.info(f"PHASE 1: PARALLEL CONTRACT SCRAPING ({self.max_workers} workers)")
        logger.info("="*70)

        # Step 1: Collect contract addresses per stratum
        strata_populations = {}
        for stratum in self.config['sampling_strategy']['strata']:
            logger.info(f"\nCollecting stratum: {stratum['name']}...")
            population = self._collect_stratum(stratum)
            self.sampler.add_stratum(
                name=stratum['name'],
                population=population,
                percentage=stratum['percentage'] / 100.0
            )
            strata_populations[stratum['name']] = population

        # Step 2: Execute stratified sampling
        final_sample = self.sampler.sample()

        # Step 3: Filter out already-scraped contracts
        addresses_to_scrape = [
            s['address'] for s in final_sample 
            if s['address'] not in self.checkpoint['scraped_addresses']
        ]

        if not addresses_to_scrape:
            logger.info("\n✅ All contracts already scraped! Skipping...")
            logger.info(f"   Previously scraped: {len(self.checkpoint['scraped_addresses'])} contracts")
            return

        logger.info(f"\n📊 Scraping Status:")
        logger.info(f"   Total needed: {len(final_sample)}")
        logger.info(f"   Already scraped: {len(self.checkpoint['scraped_addresses'])}")
        logger.info(f"   To scrape now: {len(addresses_to_scrape)}")
        logger.info(f"   Workers: {self.max_workers}")

        # Step 4: Parallel scraping
        logger.info(f"\n{'='*70}")
        logger.info(f"PARALLEL SCRAPING: {len(addresses_to_scrape)} CONTRACTS")
        logger.info(f"{'='*70}\n")

        start_time = time.time()
        files = self._scrape_parallel(addresses_to_scrape)
        elapsed = time.time() - start_time

        # Step 5: Update checkpoint
        for file_path in files:
            address = self._extract_address_from_filename(file_path.name)
            if address:
                with self.checkpoint_lock:
                    self.checkpoint['scraped_addresses'].append(address)
                    self.checkpoint['scraped_files'][address] = str(file_path)

        self._save_checkpoint()

        # Step 6: Generate scraping report
        self._generate_scraping_report(final_sample, strata_populations)

        logger.info(f"\n✅ Parallel scraping complete!")
        logger.info(f"   Total contracts scraped: {len(self.checkpoint['scraped_addresses'])}")
        logger.info(f"   Time elapsed: {elapsed:.1f}s ({elapsed/60:.1f} min)")
        logger.info(f"   Speed: {len(files)/elapsed:.2f} contracts/sec")
        logger.info(f"   Files saved to: {self.output_dir}")
        logger.info(f"   Checkpoint saved: {self.checkpoint_file}")

    def _scrape_parallel(self, addresses: List[str]) -> List[Path]:
        """Scrape contracts in parallel with rate limiting"""
        scraper = EtherscanScraper()
        files = []

        # Rate limiting: 5 calls/sec
        rate_limit = 5.0  # requests per second
        min_interval = 1.0 / rate_limit

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks with staggered delays
            futures = {}
            for i, address in enumerate(addresses):
                # Stagger submissions to respect rate limit
                time.sleep(min_interval)

                future = executor.submit(
                    self._scrape_single,
                    scraper,
                    address,
                    i + 1,
                    len(addresses)
                )
                futures[future] = address

            # Collect results as they complete
            for future in as_completed(futures):
                address = futures[future]
                try:
                    file_path = future.result()
                    if file_path:
                        files.append(file_path)
                except Exception as e:
                    logger.error(f"❌ Failed to scrape {address}: {e}")

        return files

    def _scrape_single(self, scraper, address: str, idx: int, total: int) -> Path:
        """Worker function to scrape a single contract"""
        try:
            logger.info(f"[{idx}/{total}] Scraping {address}...")
            file_path = scraper.scrape_contract(address, self.output_dir)
            logger.info(f"[{idx}/{total}] ✅ Saved {file_path.name}")
            return file_path
        except Exception as e:
            logger.error(f"[{idx}/{total}] ❌ Failed {address}: {e}")
            return None

    def _collect_stratum(self, stratum_config: dict) -> List[Dict]:
        """Collect contracts for one stratum"""
        stratum_name = stratum_config['name']

        if stratum_name == 'high_quality':
            collector = DeFiLlamaCollector(stratum_config)
            return collector.collect()
        elif stratum_name == 'random_verified':
            collector = CoinGeckoCollector(stratum_config)
            return collector.collect()
        elif stratum_name == 'known_vulnerable':
            collector = ManualCuratedCollector(stratum_config)
            return collector.collect()
        elif stratum_name == 'version_diversity':
            collector = ManualCuratedCollector(stratum_config)
            return collector.collect()
        else:
            logger.warning(f"Unknown stratum: {stratum_name}")
            return []

    def _extract_address_from_filename(self, filename: str) -> str:
        """Extract address from filename like 'ContractName_0xABC123.sol'"""
        if '_0x' in filename:
            parts = filename.split('_0x')
            if len(parts) >= 2:
                address = '0x' + parts[-1].replace('.sol', '')
                return address
        return None

    def _generate_scraping_report(self, sample: List[Dict], populations: Dict):
        """Generate scraping metadata report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'phase': 'scraping',
            'parallelization': {
                'enabled': True,
                'workers': self.max_workers
            },
            'total_contracts_scraped': len(self.checkpoint['scraped_addresses']),
            'output_directory': str(self.output_dir),
            'strata': {}
        }

        for name, pop in populations.items():
            sampled_count = len([s for s in sample if s.get('stratum') == name])
            report['strata'][name] = {
                'population_size': len(pop),
                'sampled': sampled_count
            }

        report_path = Path('data/scraping_report.yaml')
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            yaml.dump(report, f, default_flow_style=False)

        logger.info(f"\n✅ Scraping report saved: {report_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Phase 1: Parallel contract scraping from Etherscan"
    )
    parser.add_argument('--config', 
                       default='config/collection_config.yaml',
                       help='Path to config file')
    parser.add_argument('--workers', type=int, default=4,
                       help='Number of parallel workers (default: 4)')

    args = parser.parse_args()

    logger.info(f"Starting parallel scraping with {args.workers} workers...")

    pipeline = ParallelScrapingPipeline(args.config, max_workers=args.workers)
    pipeline.scrape()

    print("\n" + "="*70)
    print("NEXT STEP: Run 2_extract_features_PARALLEL.py to analyze contracts")
    print("="*70)
