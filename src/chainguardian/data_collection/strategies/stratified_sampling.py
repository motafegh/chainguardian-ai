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
    
    WHY: Prevents sample bias
    HOW: Define strata, sample proportionally from each
    
    EXAMPLE:
        sampler = StratifiedSampler(target_size=100)
        sampler.add_stratum("high_quality", addresses_defi, percentage=30)
        sampler.add_stratum("random", addresses_random, percentage=40)
        final_sample = sampler.sample()
    """
    
    def __init__(self, target_size: int, random_seed: int = 42):
        self.target_size = target_size
        self.strata = {}
        self.random_seed = random_seed
        random.seed(random_seed)  # Reproducibility
    
    def add_stratum(
        self, 
        name: str, 
        population: List[str], 
        percentage: float
    ):
        """
        Add a stratum to the sampling strategy
        
        Args:
            name: Stratum identifier
            population: List of contract addresses in this stratum
            percentage: What % of final dataset (0.0-1.0)
        """
        sample_size = int(self.target_size * percentage)
        
        self.strata[name] = {
            'population': population,
            'percentage': percentage,
            'sample_size': sample_size
        }
        
        logger.info(
            f"Added stratum '{name}': "
            f"{len(population)} population → {sample_size} sample size"
        )
    
    def sample(self) -> List[Dict]:
        """
        Execute stratified sampling
        
        Returns:
            List of dicts with: address, stratum, ...
        """
        logger.info(f"Executing stratified sampling (target={self.target_size})...")
        
        final_sample = []
        
        for stratum_name, stratum_data in self.strata.items():
            population = stratum_data['population']
            sample_size = stratum_data['sample_size']
            
            # Random sample from this stratum
            if len(population) >= sample_size:
                sampled = random.sample(population, sample_size)
            else:
                # If population smaller than target, take all
                logger.warning(
                    f"Stratum '{stratum_name}' has only {len(population)} "
                    f"(target={sample_size}). Taking all."
                )
                sampled = population
            
            # Add metadata
            for addr in sampled:
                final_sample.append({
                    'address': addr if isinstance(addr, str) else addr['address'],
                    'stratum': stratum_name,
                    'metadata': addr if isinstance(addr, dict) else {}
                })
            
            logger.info(f"  ✓ Sampled {len(sampled)} from '{stratum_name}'")
        
        logger.info(f"Total sample size: {len(final_sample)}")
        
        return final_sample
