"""
DeFiLlama API Collector
Collects top DeFi protocols by TVL with optimized performance and timeout handling
"""

from typing import List, Dict, Optional
import requests
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from .base import BaseCollector

logger = logging.getLogger(__name__)

class DeFiLlamaCollector(BaseCollector):
    """
    Collect top DeFi protocols from DeFiLlama API with optimized performance
    
    API: https://api.llama.fi
    """
    
    BASE_URL = "https://api.llama.fi"
    
    def collect(self) -> List[Dict]:
        """Collect top N protocols by TVL with performance optimizations"""
        
        criteria = self.config.get('criteria', {})
        
        # Handle both formats from config
        if isinstance(criteria, list):
            # Format: [{'top_by_tvl': 30}, {...}]
            top_n = next((c.get('top_by_tvl') for c in criteria if 'top_by_tvl' in c), 30)
            min_transactions = next((c.get('min_transactions') for c in criteria if 'min_transactions' in c), 1000)
        else:
            # Format: {'top_by_tvl': 30}
            top_n = criteria.get('top_by_tvl', 30)
            min_transactions = criteria.get('min_transactions', 1000)
        
        chain = 'Ethereum'
        
        self.log_collection_start(self.config.get('name', 'DeFiLlama'))
        
        try:
            logger.info(f"Querying DeFiLlama for all protocols...")
            response = requests.get(f"{self.BASE_URL}/protocols", timeout=30)
            response.raise_for_status()
            all_protocols = response.json()
            
            logger.info(f"Received {len(all_protocols)} total protocols")
            
            # Filter by chain
            chain_protocols = [
                p for p in all_protocols
                if chain in p.get('chains', [])
            ]
            
            logger.info(f"Filtered to {len(chain_protocols)} on {chain}")
            
            # Sort by TVL
            chain_protocols.sort(key=lambda x: x.get('tvl', 0), reverse=True)
            
            # Get top N
            top_protocols = chain_protocols[:top_n]
            
            # Extract addresses with optimized approach
            contracts = []
            
            # First pass: use addresses from main API response if available
            for i, protocol in enumerate(top_protocols):
                if i % 50 == 0:
                    logger.info(f"Processing protocol {i+1}/{len(top_protocols)}")
                
                # Check if address is already in main response
                address = protocol.get('address')
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
                    logger.debug(f"  ✓ Added {protocol['name']} (from main API)")
            
            # Second pass: get details for protocols without addresses
            protocols_without_address = [
                p for p in top_protocols 
                if not p.get('address') or not self.validate_address(p.get('address'))
            ]
            
            logger.info(f"Need to fetch details for {len(protocols_without_address)} protocols")
            
            if protocols_without_address:
                # Use parallel processing with a timeout
                contracts.extend(self._fetch_protocol_details_parallel(protocols_without_address, chain))
            
            self.log_collection_complete(len(contracts))
            return contracts
            
        except Exception as e:
            logger.error(f"DeFiLlama collection failed: {e}")
            return []
    
    def _fetch_protocol_details_parallel(self, protocols: List[Dict], chain: str) -> List[Dict]:
        """Fetch protocol details in parallel with timeout handling"""
        contracts = []
        
        # Limit the number of protocols to fetch details for
        max_details = 100  # Limit to prevent extremely long runtimes
        if len(protocols) > max_details:
            protocols = protocols[:max_details]
            logger.info(f"Limiting details fetch to top {max_details} protocols by TVL")
        
        # Use ThreadPoolExecutor for parallel API calls
        max_workers = 5  # Limit concurrent requests to avoid overwhelming the API
        batch_size = 20  # Increased batch size
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_protocol = {
                executor.submit(self._get_protocol_detail, protocol['slug']): protocol
                for protocol in protocols
            }
            
            # Process completed tasks with timeout
            completed = 0
            for future in as_completed(future_to_protocol, timeout=300):  # 5 minute timeout
                if completed % batch_size == 0:
                    logger.info(f"Completed {completed}/{len(protocols)} protocol details")
                
                protocol = future_to_protocol[future]
                
                try:
                    detail = future.result(timeout=10)  # 10 second timeout per request
                    
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
                            logger.debug(f"  ✓ Added {protocol['name']} (from detail API)")
                        else:
                            logger.debug(f"  ✗ No valid address for {protocol['name']}")
                    
                    completed += 1
                
                except TimeoutError:
                    logger.warning(f"Timeout fetching details for {protocol['name']}")
                    completed += 1
                
                except Exception as e:
                    logger.warning(f"Error fetching details for {protocol['name']}: {e}")
                    completed += 1
        
        return contracts
    
    def _get_protocol_detail(self, slug: str) -> Optional[Dict]:
        """Get protocol details with improved error handling and rate limiting"""
        try:
            # Add a small delay to respect rate limits
            time.sleep(0.1)
            
            response = requests.get(f"{self.BASE_URL}/protocol/{slug}", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout fetching details for {slug}")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error fetching details for {slug}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error fetching details for {slug}: {e}")
            return None