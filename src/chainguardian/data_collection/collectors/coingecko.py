"""
CoinGecko API Collector
Collects top tokens by market cap
"""

from typing import List, Dict
import requests
import time
from .base import BaseCollector


class CoinGeckoCollector(BaseCollector):
    """
    Collect top tokens from CoinGecko API
    
    API: https://api.coingecko.com/api/v3
    """
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    def collect(self) -> List[Dict]:
        """Collect top N tokens by market cap"""
        
        criteria = self.config.get('criteria', {})
        
        # Handle list format from config
        if isinstance(criteria, list):
            top_n = 35  # Default from config percentage
        else:
            top_n = criteria.get('top_n', 35)
        
        category = 'ethereum-ecosystem'
        
        self.log_collection_start(self.config.get('name', 'CoinGecko'))
        
        try:
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
            
            self.logger.info(f"Received {len(tokens)} tokens")
            
            contracts = []
            
            for token in tokens:
                coin_id = token['id']
                detail = self._get_coin_detail(coin_id)
                
                if detail and 'platforms' in detail:
                    platforms = detail['platforms']
                    
                    if 'ethereum' in platforms and platforms['ethereum']:
                        address = platforms['ethereum']
                        
                        if self.validate_address(address):
                            contracts.append({
                                'address': address,
                                'name': token['name'],
                                'source': 'coingecko',
                                'metadata': {
                                    'symbol': token['symbol'],
                                    'market_cap': token.get('market_cap', 0)
                                }
                            })
                
                time.sleep(1.5)  # Rate limiting
            
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
