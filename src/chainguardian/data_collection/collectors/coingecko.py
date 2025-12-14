"""
CoinGecko API Collector
Collects top tokens by market cap with parallel processing
"""

from typing import List, Dict
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from .base import BaseCollector

class CoinGeckoCollector(BaseCollector):
    """
    Collect top tokens from CoinGecko API
    
    API: https://api.coingecko.com/api/v3
    Features:
    - Parallel detail fetching (5 threads - CoinGecko has stricter limits)
    - Rate limiting per thread
    - Progress tracking
    """
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    MAX_WORKERS = 5  # Conservative for CoinGecko free tier
    
    def collect(self) -> List[Dict]:
        """Collect top N tokens by market cap"""
        
        criteria = self.config.get('criteria', {})
        
        # Handle list format from config
        if isinstance(criteria, list):
            top_n = 200  # Increased from 100
        else:
            top_n = criteria.get('top_n', 200)
        
        category = 'ethereum-ecosystem'
        
        self.log_collection_start(self.config.get('name', 'CoinGecko'))
        
        try:
            # ================================================================
            # STEP 1: FETCH TOKEN LIST
            # ================================================================
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': top_n,
                'page': 1,
                'category': category,
                'sparkline': False
            }
            
            self.logger.info(f"Querying CoinGecko for top {top_n} tokens...")
            response = requests.get(f"{self.BASE_URL}/coins/markets", params=params, timeout=30)
            response.raise_for_status()
            tokens = response.json()
            
            self.logger.info(f"✓ Received {len(tokens)} tokens")
            
            # Calculate time estimate
            estimated_time = len(tokens) * 1.5 / self.MAX_WORKERS
            self.logger.info(
                f"   Querying details in parallel ({self.MAX_WORKERS} threads) - "
                f"estimated time: ~{estimated_time:.0f}s"
            )
            
            # ================================================================
            # STEP 2: PARALLEL DETAIL FETCHING
            # ================================================================
            contracts = []
            completed = 0
            
            def fetch_and_process(token_data):
                """Fetch details for one token and extract Ethereum address"""
                token, index = token_data
                
                try:
                    coin_id = token['id']
                    detail = self._get_coin_detail(coin_id)
                    
                    if detail and 'platforms' in detail:
                        platforms = detail['platforms']
                        
                        if 'ethereum' in platforms and platforms['ethereum']:
                            address = platforms['ethereum']
                            
                            if self.validate_address(address):
                                # Rate limiting inside thread
                                time.sleep(1.5)
                                
                                return {
                                    'address': address,
                                    'name': token['name'],
                                    'source': 'coingecko',
                                    'metadata': {
                                        'symbol': token['symbol'],
                                        'market_cap': token.get('market_cap', 0)
                                    }
                                }
                    
                    # Rate limiting even on failure
                    time.sleep(1.5)
                    
                except Exception as e:
                    self.logger.debug(f"Failed to fetch {token.get('name', 'unknown')}: {e}")
                
                return None
            
            # Create thread pool and submit tasks
            with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
                # Submit all tasks
                futures = {
                    executor.submit(fetch_and_process, (token, i)): i
                    for i, token in enumerate(tokens, 1)
                }
                
                # Process results as they complete
                for future in as_completed(futures):
                    completed += 1
                    
                    # Progress updates
                    if completed % 25 == 0 or completed == 1:
                        self.logger.info(
                            f"   [{completed}/{len(tokens)}] "
                            f"Processed | Found {len(contracts)} valid Ethereum addresses"
                        )
                    
                    result = future.result()
                    if result:
                        contracts.append(result)
                        
                        # Log milestone finds
                        if len(contracts) in [5, 10, 25, 50]:
                            self.logger.info(f"   🎯 Milestone: {len(contracts)} valid addresses found!")
            
            self.logger.info(f"✓ Completed CoinGecko collection")
            self.log_collection_complete(len(contracts))
            return contracts
            
        except Exception as e:
            self.logger.error(f"CoinGecko collection failed: {e}")
            return []
    
    def _get_coin_detail(self, coin_id: str) -> Dict:
        """Get coin details"""
        try:
            response = requests.get(f"{self.BASE_URL}/coins/{coin_id}", timeout=10)
            response.raise_for_status()
            return response.json()
        except:
            return None
