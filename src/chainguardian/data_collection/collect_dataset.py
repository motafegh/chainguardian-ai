"""
Production Dataset Collection Orchestrator
Configuration-driven, reproducible, automated
"""

import yaml
from pathlib import Path
import logging
from datetime import datetime
from typing import List, Dict

# ✅ CORRECT (NEW imports)
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
    2. Query APIs for contract lists (programmatic)
    3. Apply stratified sampling (statistical)
    4. Scrape source code (Etherscan)
    5. Extract features (Slither + AST)
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
        """Execute full collection pipeline"""
        
        logger.info("="*70)
        logger.info("STARTING PRODUCTION DATASET COLLECTION")
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
        
        # Step 3: Scrape and analyze
        self._scrape_and_analyze(final_sample)
        
        # Step 4: Generate report
        self._generate_report(final_sample, strata_populations)
    
    def _collect_stratum(self, stratum_config: dict) -> List[Dict]:
        """Collect contracts for one stratum"""
        
        stratum_name = stratum_config['name']
        criteria = stratum_config['criteria']
        
        # Route to appropriate collector based on stratum name
        if stratum_name == 'high_quality':
            # Use DeFiLlama for high quality protocols
            collector = DeFiLlamaCollector(stratum_config)
            return collector.collect()
        
        elif stratum_name == 'random_verified':
            # Use CoinGecko for diverse tokens
            collector = CoinGeckoCollector(stratum_config)
            return collector.collect()
        
        elif stratum_name == 'known_vulnerable':
            # Use manual curated list for vulnerable contracts
            collector = ManualCuratedCollector(stratum_config)
            return collector.collect()
        
        elif stratum_name == 'version_diversity':
            # Use manual curated list for old contracts
            collector = ManualCuratedCollector(stratum_config)
            return collector.collect()
        
        else:
            logger.warning(f"Unknown stratum: {stratum_name}")
            return []
    
    def _scrape_and_analyze(self, sample: List[Dict]):
        """Scrape source code and extract features"""
        
        addresses = [s['address'] for s in sample]
        
        logger.info(f"\n{'='*70}")
        logger.info(f"SCRAPING {len(addresses)} CONTRACTS FROM ETHERSCAN")
        logger.info(f"{'='*70}\n")
        
        scraper = EtherscanScraper()
        files = scraper.scrape_batch(
            addresses,
            output_dir=Path("blockchain/contracts/collected")
        )
        
        logger.info(f"\n{'='*70}")
        logger.info(f"EXTRACTING FEATURES FROM {len(files)} CONTRACTS")
        logger.info(f"{'='*70}\n")
        
        pipeline = FeaturePipeline()
        
        for i, file in enumerate(files, 1):
            try:
                contract_name = file.stem.split('_')[0]
                logger.info(f"[{i}/{len(files)}] Analyzing {contract_name}...")
                pipeline.analyze_contract(file, contract_name)
            except Exception as e:
                logger.error(f"Failed to analyze {file.name}: {e}")
        
        output_path = Path(self.config['output']['path'])
        pipeline.save_dataset(output_path)
        
        logger.info(f"\n✅ Dataset saved: {output_path}")
    
    def _generate_report(self, sample: List[Dict], populations: Dict):
        """Generate metadata report for reproducibility"""
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'config_version': '1.0',
            'target_size': self.config['dataset']['target_size'],
            'actual_size': len(sample),
            'strata': {}
        }
        
        for name, pop in populations.items():
            sampled_count = len([s for s in sample if s['stratum'] == name])
            report['strata'][name] = {
                'population_size': len(pop),
                'sampled': sampled_count
            }
        
        metadata_path = Path('data/collection_metadata.yaml')
        with open(metadata_path, 'w') as f:
            yaml.dump(report, f, default_flow_style=False)
        
        logger.info(f"\n✅ Metadata report saved: {metadata_path}")
        
        # Print summary
        logger.info(f"\n{'='*70}")
        logger.info("COLLECTION SUMMARY")
        logger.info(f"{'='*70}")
        logger.info(f"Target size: {report['target_size']}")
        logger.info(f"Actual size: {report['actual_size']}")
        logger.info(f"\nStrata breakdown:")
        for stratum_name, stats in report['strata'].items():
            logger.info(f"  {stratum_name}: {stats['sampled']} sampled from {stats['population_size']} population")
        logger.info(f"{'='*70}\n")


if __name__ == "__main__":
    config_path = 'src/chainguardian/data_collection/config/collection_config.yaml'
    pipeline = DatasetCollectionPipeline(config_path)
    pipeline.collect()