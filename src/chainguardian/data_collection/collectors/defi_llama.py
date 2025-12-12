"""
DeFiLlama API Collector
Collects top DeFi protocols by TVL
"""

from typing import List, Dict
import requests
import time
from .base import BaseCollector


class DeFiLlamaCollector(BaseCollector):
    """
    Collect top DeFi protocols from DeFiLlama API
    
    API: https://api.llama.fi
    """
    
    BASE_URL = "https://api.llama.fi"
    
    def collect(self) -> List[Dict]:
        """Collect top N protocols by TVL"""
        
        criteria = self.config.get('criteria', {})
        
        # Handle both formats from config
        if isinstance(criteria, list):
            # Format: [{'top_by_tvl': 30}, {...}]
            top_n = next((c.get('top_by_tvl') for c in criteria if 'top_by_tvl' in c), 30)
        else:
            # Format: {'top_by_tvl': 30}
            top_n = criteria.get('top_by_tvl', 30)
        
        chain = 'Ethereum'
        
        self.log_collection_start(self.config.get('name', 'DeFiLlama'))
        
        try:
            self.logger.info(f"Querying DeFiLlama for all protocols...")
            response = requests.get(f"{self.BASE_URL}/protocols", timeout=30)
            response.raise_for_status()
            all_protocols = response.json()
            
            self.logger.info(f"Received {len(all_protocols)} total protocols")
            
            # Filter by chain
            chain_protocols = [
                p for p in all_protocols
                if chain in p.get('chains', [])
            ]
            
            self.logger.info(f"Filtered to {len(chain_protocols)} on {chain}")
            
            # Sort by TVL
            chain_protocols.sort(key=lambda x: x.get('tvl', 0), reverse=True)
            
            # Get top N
            top_protocols = chain_protocols[:top_n]
            
            # Extract addresses
            contracts = []
            
            for protocol in top_protocols:
                detail = self._get_protocol_detail(protocol['slug'])
                
                if detail:
                    # Try different address formats
                    address = None
                    if 'address' in detail:
                        if isinstance(detail['address'], dict):
                            address = detail['address'].get('ethereum') or detail['address'].get('Ethereum')
                        elif isinstance(detail['address'], str):
                            address = detail['address']
                    
                    if address and self.validate_address(address):
                        contracts.append({
                            'address': address,
                            'name': protocol['name'],
                            'source': 'defillama',
                            'metadata': {
                                'tvl': protocol.get('tvl', 0),
                                'category': protocol.get('category', 'unknown'),
                                'chain': chain
                            }
                        })
                        self.logger.debug(f"  ✓ Added {protocol['name']}")
                
                time.sleep(0.5)  # Rate limiting
            
            self.log_collection_complete(len(contracts))
            return contracts
            
        except Exception as e:
            self.logger.error(f"DeFiLlama collection failed: {e}")
            return []
    
    def _get_protocol_detail(self, slug: str) -> Dict:
        """Get protocol details"""
        try:
            response = requests.get(f"{self.BASE_URL}/protocol/{slug}", timeout=10)
            response.raise_for_status()
            return response.json()
        except:
            return None
