"""
Stratified Sampling Strategy
Ensures dataset diversity by sampling from defined strata
"""

from typing import List, Dict
import random
import logging

logger = logging.getLogger(__name__)

class StratifiedSampler:
    """
    Implement stratified sampling for contract selection
    
    Performance: O(n) where n = total population size
    Already optimized - random.sample() is very fast
    """
    
    def __init__(self, target_size: int, random_seed: int = 42):
        self.target_size = target_size
        self.strata = {}
        self.random_seed = random_seed
        random.seed(random_seed)
        
        logger.info(f"Initialized StratifiedSampler (target={target_size}, seed={random_seed})")
    
    def add_stratum(
        self,
        name: str,
        population: List[str],
        percentage: float
    ):
        """Add a stratum to the sampling strategy"""
        sample_size = int(self.target_size * percentage)
        
        self.strata[name] = {
            'population': population,
            'percentage': percentage,
            'sample_size': sample_size
        }
        
        logger.info(
            f"✓ Added stratum '{name}': "
            f"{len(population)} population → {sample_size} sample target"
        )
    
    def sample(self) -> List[Dict]:
        """
        Execute stratified sampling with duplicate detection
        """
        logger.info("")
        logger.info(f"{'='*70}")
        logger.info(f"Executing stratified sampling (target={self.target_size})...")
        logger.info(f"{'='*70}")
        
        final_sample = []
        seen_addresses = set()  # NEW: Track seen addresses
        duplicates_removed = 0  # NEW: Count duplicates
        
        for stratum_name, stratum_data in self.strata.items():
            population = stratum_data['population']
            sample_size = stratum_data['sample_size']
            
            logger.info("")
            logger.info(f"Stratum: {stratum_name}")
            logger.info(f"  Population: {len(population)}")
            logger.info(f"  Target sample: {sample_size}")
            
            # Random sample from this stratum
            if len(population) >= sample_size:
                sampled = random.sample(population, sample_size)
                logger.info(f"  ✓ Sampled: {len(sampled)}")
            else:
                logger.warning(
                    f"  ⚠ Population ({len(population)}) < target ({sample_size}). "
                    f"Taking all available."
                )
                sampled = population
                logger.info(f"  ✓ Sampled: {len(sampled)} (all available)")
            
            # Add metadata with duplicate detection
            for addr in sampled:
                # Extract address string
                address = addr if isinstance(addr, str) else addr['address']
                
                # NEW: Check for duplicates (case-insensitive)
                address_lower = address.lower()
                if address_lower in seen_addresses:
                    duplicates_removed += 1
                    logger.debug(f"  ⚠ Skipping duplicate: {address[:10]}...")
                    continue
                
                # Add to seen set
                seen_addresses.add(address_lower)
                
                # Add to final sample
                final_sample.append({
                    'address': address,
                    'stratum': stratum_name,
                    'metadata': addr if isinstance(addr, dict) else {}
                })
        
        logger.info("")
        logger.info(f"{'='*70}")
        logger.info(f"✓ Stratified sampling complete: {len(final_sample)} contracts")
        
        if duplicates_removed > 0:
            logger.info(f"  Removed {duplicates_removed} duplicate addresses")
        
        logger.info(f"{'='*70}")
        
        return final_sample

