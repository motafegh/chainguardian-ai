"""Test collection pipeline without scraping"""

import yaml
import logging
from pathlib import Path

from chainguardian.data_collection.collectors.defi_llama import DeFiLlamaCollector
from chainguardian.data_collection.collectors.coingecko import CoinGeckoCollector
from chainguardian.data_collection.collectors.manual_curated import ManualCuratedCollector
from chainguardian.data_collection.strategies.stratified_sampling import StratifiedSampler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load test config
with open('src/chainguardian/data_collection/config/test_config.yaml') as f:
    config = yaml.safe_load(f)

# Create sampler
sampler = StratifiedSampler(target_size=config['dataset']['target_size'])

logger.info("="*70)
logger.info("TESTING ADDRESS COLLECTION (NO SCRAPING)")
logger.info("="*70)

# Collect from each stratum
for stratum in config['sampling_strategy']['strata']:
    logger.info(f"\nCollecting stratum: {stratum['name']}...")
    
    if stratum['name'] == 'high_quality':
        collector = DeFiLlamaCollector(stratum)
    elif stratum['name'] == 'random_verified':
        collector = CoinGeckoCollector(stratum)
    else:
        collector = ManualCuratedCollector(stratum)
    
    population = collector.collect()
    
    sampler.add_stratum(
        name=stratum['name'],
        population=population,
        percentage=stratum['percentage'] / 100.0
    )

# Execute sampling
logger.info("\n" + "="*70)
logger.info("EXECUTING STRATIFIED SAMPLING")
logger.info("="*70)

sample = sampler.sample()

logger.info("\n" + "="*70)
logger.info("COLLECTION SUMMARY")
logger.info("="*70)
logger.info(f"Target size: {config['dataset']['target_size']}")
logger.info(f"Actual size: {len(sample)}")
logger.info("\nSampled contracts:")
for s in sample[:5]:
    logger.info(f"  - {s['address']} ({s['stratum']})")
logger.info(f"  ... and {len(sample)-5} more")

logger.info("\n✅ Address collection test PASSED!")
logger.info("Next: Run full pipeline with scraping")
