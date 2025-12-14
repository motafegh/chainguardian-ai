"""
Production Dataset Collection Orchestrator
Configuration-driven, reproducible, parallel processing
FIXED: Multi-file contract support
"""

import yaml
from pathlib import Path
import logging
from datetime import datetime
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from chainguardian.data_collection.collectors.token_lists import TokenListCollector
from chainguardian.data_collection.collectors.defi_llama import DeFiLlamaCollector
from chainguardian.data_collection.collectors.coingecko import CoinGeckoCollector
from chainguardian.data_collection.collectors.manual_curated import ManualCuratedCollector
from chainguardian.data_collection.strategies.stratified_sampling import StratifiedSampler
from chainguardian.data_collection.etherscan_scraper import EtherscanScraper
from chainguardian.feature_extraction.pipeline import FeaturePipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatasetCollectionPipeline:
    """
    End-to-end dataset collection from configuration
    
    WORKFLOW:
    1. Load config (YAML)
    2. Query APIs for contract lists (parallel)
    3. Apply stratified sampling (with duplicate detection)
    4. Scrape source code (parallel - Etherscan)
    5. Extract features (parallel - Slither + AST)
    6. Export dataset (CSV)
    7. Generate metadata report (reproducibility)
    """
    
    def __init__(self, config_path: str):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        
        self.sampler = StratifiedSampler(
            target_size=self.config['dataset']['target_size']
        )
    
    def collect(self):
        """Execute full collection pipeline with parallel processing"""
        
        logger.info("="*70)
        logger.info("🚀 CHAINGUARDIAN AI - PRODUCTION DATASET COLLECTION")
        logger.info("="*70)
        logger.info("")
        
        total_strata = len(self.config['sampling_strategy']['strata'])
        
        # ====================================================================
        # PHASE 1: COLLECT CONTRACT ADDRESSES PER STRATUM
        # ====================================================================
        logger.info("📊 PHASE 1/4: Collecting contract addresses from APIs")
        logger.info("="*70)
        
        strata_populations = {}
        
        for stratum_idx, stratum in enumerate(self.config['sampling_strategy']['strata'], 1):
            logger.info("")
            logger.info(f"[STRATUM {stratum_idx}/{total_strata}] {stratum['name']}")
            logger.info("-" * 70)
            
            population = self._collect_stratum(stratum)
            
            self.sampler.add_stratum(
                name=stratum['name'],
                population=population,
                percentage=stratum['percentage'] / 100.0
            )
            
            strata_populations[stratum['name']] = population
            
            logger.info(f"✓ Stratum '{stratum['name']}' complete: {len(population)} contracts")
        
        logger.info("")
        logger.info("="*70)
        logger.info(f"✓ PHASE 1 COMPLETE: Collected {sum(len(p) for p in strata_populations.values())} total contracts")
        logger.info("="*70)
        
        # ====================================================================
        # PHASE 2: STRATIFIED SAMPLING (with duplicate detection)
        # ====================================================================
        logger.info("")
        logger.info("📊 PHASE 2/4: Executing stratified sampling")
        logger.info("="*70)
        
        final_sample = self.sampler.sample()
        
        logger.info(f"✓ PHASE 2 COMPLETE: Sampled {len(final_sample)} contracts")
        logger.info("="*70)
        
        # ====================================================================
        # PHASE 3: SCRAPE SOURCE CODE FROM ETHERSCAN (Parallel)
        # ====================================================================
        logger.info("")
        logger.info("📊 PHASE 3/4: Scraping source code from Etherscan")
        logger.info("="*70)
        
        files = self._scrape_contracts(final_sample)
        
        # ====================================================================
        # PHASE 4: EXTRACT FEATURES (Parallel)
        # ====================================================================
        logger.info("")
        logger.info("📊 PHASE 4/4: Extracting ML features")
        logger.info("="*70)
        
        self._extract_features_parallel(files)
        
        # ====================================================================
        # PHASE 5: GENERATE METADATA REPORT
        # ====================================================================
        logger.info("")
        logger.info("📊 Generating reproducibility metadata")
        logger.info("="*70)
        
        self._generate_report(final_sample, strata_populations)
        
        logger.info("")
        logger.info("="*70)
        logger.info("🎉 ALL PHASES COMPLETE - Dataset ready for ML training!")
        logger.info("="*70)
    
    def _collect_stratum(self, stratum_config: dict) -> List[Dict]:
        """Collect contracts for one stratum"""
        stratum_name = stratum_config['name']
        
        # Route to appropriate collector
        if stratum_name == 'high_quality':
            collector = DeFiLlamaCollector(stratum_config)
            return collector.collect()
        elif stratum_name == 'random_verified':
            collector = CoinGeckoCollector(stratum_config)
            return collector.collect()
        elif stratum_name == 'token_lists':
            collector = TokenListCollector(stratum_config)
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
    
    def _scrape_contracts(self, sample: List[Dict]) -> List[Path]:
        """Scrape source code from Etherscan (parallel)"""
        
        addresses = [s['address'] for s in sample]
        
        logger.info(f"Scraping {len(addresses)} contracts from Etherscan...")
        logger.info(f"Using 5 parallel workers")
        estimated_time = len(addresses) * 0.21 / 5
        logger.info(f"Estimated time: ~{estimated_time:.0f}s")
        logger.info("")
        
        scraper = EtherscanScraper()
        files = scraper.scrape_batch(
            addresses,
            output_dir=Path("blockchain/contracts/collected"),
            max_workers=5
        )
        
        logger.info("")
        logger.info(f"✓ Scraping complete: {len(files)}/{len(addresses)} contracts saved")
        logger.info("="*70)
        
        return files
    
    def _extract_features_parallel(self, files: List[Path]):
        """
        Extract features from contracts using parallel processing.
        
        FIXED: Handles both single-file and multi-file contracts
        
        Args:
            files: List of file paths (may be inside directories for multi-file contracts)
        """
        if not files:
            logger.warning("No files to analyze")
            return
        
        # ================================================================
        # CONVERT FILE PATHS TO CONTRACT PATHS
        # ================================================================
        # For multi-file contracts: Use parent directory
        # For single-file contracts: Use file itself
        contract_paths = []
        seen_paths = set()
        
        for file_path in files:
            # Check if this is a multi-file contract (file is inside a directory with _0x pattern)
            parent_dir = file_path.parent
            parent_name = parent_dir.name
            
            # Multi-file contract: parent directory name has _0x pattern
            if '_0x' in parent_name and parent_dir != Path("blockchain/contracts/collected"):
                contract_path = parent_dir
            else:
                # Single-file contract
                contract_path = file_path
            
            # Avoid duplicates
            if contract_path not in seen_paths:
                contract_paths.append(contract_path)
                seen_paths.add(contract_path)
        
        logger.info("")
        logger.info(f"Analyzing {len(contract_paths)} unique contracts...")
        logger.info(f"  Single-file contracts: {sum(1 for p in contract_paths if p.is_file())}")
        logger.info(f"  Multi-file contracts: {sum(1 for p in contract_paths if p.is_dir())}")
        
        # Performance estimates
        sequential_time = len(contract_paths) * 5
        parallel_workers = 5
        parallel_time = sequential_time / parallel_workers
        
        logger.info(f"Sequential estimate: ~{sequential_time}s ({sequential_time/60:.1f} min)")
        logger.info(f"Parallel ({parallel_workers} workers): ~{parallel_time}s ({parallel_time/60:.1f} min)")
        logger.info(f"Using parallel feature extraction...")
        logger.info("="*70)
        logger.info("")
        
        # Initialize pipeline (thread-safe)
        pipeline = FeaturePipeline()
        
        successful = 0
        failed = 0
        
        def analyze_one_contract(contract_path):
            """
            Analyze single contract (runs in thread pool)
            
            Args:
                contract_path: Path to .sol file OR directory with .sol files
            """
            try:
                # Extract contract name from path
                if contract_path.is_dir():
                    # Multi-file: directory name like "FRAXShares_0x3432b6a6"
                    dir_name = contract_path.name
                    contract_name = dir_name.rsplit('_', 1)[0]  # Remove _0xABCD suffix
                else:
                    # Single-file: filename like "BNB_0xb8c77482.sol"
                    file_stem = contract_path.stem
                    contract_name = file_stem.rsplit('_', 1)[0]  # Remove _0xABCD suffix
                
                # Analyze contract (pipeline handles both file and directory)
                pipeline.analyze_contract(contract_path, contract_name)
                return True, contract_name
                
            except Exception as e:
                logger.error(f"Failed to analyze {contract_path.name}: {e}")
                return False, contract_path.name
        
        # Thread pool for parallel analysis
        with ThreadPoolExecutor(max_workers=parallel_workers) as executor:
            # Submit all tasks
            futures = {
                executor.submit(analyze_one_contract, path): path
                for path in contract_paths
            }
            
            # Process with progress bar
            with tqdm(total=len(contract_paths), desc="Extracting features", ncols=100) as pbar:
                for future in as_completed(futures):
                    success, name = future.result()
                    
                    if success:
                        successful += 1
                    else:
                        failed += 1
                    
                    pbar.update(1)
                    
                    # Checkpoint every 25 contracts
                    if (successful + failed) % 25 == 0:
                        logger.info(
                            f"   [{successful + failed}/{len(contract_paths)}] "
                            f"Analyzed | {successful} success, {failed} failed"
                        )
        
        logger.info("")
        logger.info(f"✓ Feature extraction complete: {successful}/{len(contract_paths)} successful")
        
        if failed > 0:
            logger.warning(f"   {failed} contracts failed analysis (returned default values)")
        
        logger.info("="*70)
        
        # Save dataset
        output_path = Path(self.config['output']['path'])
        pipeline.save_dataset(output_path)
        
        logger.info("")
        logger.info(f"✅ Dataset saved: {output_path}")
    
    def _generate_report(self, sample: List[Dict], populations: Dict):
        """Generate metadata report for reproducibility"""
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'config_version': '3.0',
            'target_size': self.config['dataset']['target_size'],
            'actual_size': len(sample),
            'parallel_processing': {
                'defillama_workers': 10,
                'coingecko_workers': 5,
                'etherscan_workers': 5,
                'feature_extraction_workers': 5
            },
            'strata': {}
        }
        
        for name, pop in populations.items():
            sampled_count = len([s for s in sample if s['stratum'] == name])
            report['strata'][name] = {
                'population_size': len(pop),
                'sampled': sampled_count
            }
        
        metadata_path = Path('data/collection_metadata.yaml')
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(metadata_path, 'w') as f:
            yaml.dump(report, f, default_flow_style=False)
        
        logger.info(f"✅ Metadata report saved: {metadata_path}")
        
        # Print summary
        logger.info(f"")
        logger.info(f"{'='*70}")
        logger.info("COLLECTION SUMMARY")
        logger.info(f"{'='*70}")
        logger.info(f"Target size: {report['target_size']}")
        logger.info(f"Actual size: {report['actual_size']}")
        logger.info(f"")
        logger.info(f"Strata breakdown:")
        for stratum_name, stats in report['strata'].items():
            logger.info(
                f"  {stratum_name}: {stats['sampled']} sampled "
                f"from {stats['population_size']} population"
            )
        logger.info(f"{'='*70}")
        logger.info(f"")


if __name__ == "__main__":
    config_path = 'src/chainguardian/data_collection/config/collection_config.yaml'
    pipeline = DatasetCollectionPipeline(config_path)
    pipeline.collect()
