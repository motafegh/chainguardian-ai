"""
DeFiLlama API Collector
Collects top DeFi protocols by TVL
"""

from typing import List, Dict
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from .base import BaseCollector

class DeFiLlamaCollector(BaseCollector):
    """
    Collect top DeFi protocols from DeFiLlama API
    
    API: https://api.llama.fi
    Features:
    - Parallel detail fetching (10 threads)
    - Rate limiting per thread
    - Progress tracking
    """
    
    BASE_URL = "https://api.llama.fi"
    MAX_WORKERS = 10  # Parallel threads for detail fetching
    
    def collect(self) -> List[Dict]:
        """Collect top N protocols by TVL"""
        
        criteria = self.config.get('criteria', {})
        
        # Handle both formats from config
        if isinstance(criteria, list):
            top_n = next((c.get('top_by_tvl') for c in criteria if 'top_by_tvl' in c), 1000)
        else:
            top_n = criteria.get('top_by_tvl', 1000)
        
        chain = 'Ethereum'
        
        self.log_collection_start(self.config.get('name', 'DeFiLlama'))
        
        try:
            # ================================================================
            # STEP 1: FETCH ALL PROTOCOLS
            # ================================================================
            self.logger.info(f"Querying DeFiLlama for all protocols...")
            response = requests.get(f"{self.BASE_URL}/protocols", timeout=30)
            response.raise_for_status()
            all_protocols = response.json()
            
            self.logger.info(f"✓ Received {len(all_protocols)} total protocols")
            
            # ================================================================
            # STEP 2: FILTER BY CHAIN
            # ================================================================
            chain_protocols = [
                p for p in all_protocols
                if chain in p.get('chains', [])
            ]
            
            self.logger.info(f"✓ Filtered to {len(chain_protocols)} protocols on {chain}")
            
            # ================================================================
            # STEP 3: SORT AND SELECT TOP N
            # ================================================================
            chain_protocols.sort(key=lambda x: x.get('tvl', 0), reverse=True)
            top_protocols = chain_protocols[:top_n]
            
            self.logger.info(f"✓ Selected top {len(top_protocols)} protocols by TVL")
            
            # Calculate time estimate
            # Sequential: top_n × 0.5s
            # Parallel (10 workers): top_n × 0.5s / 10
            estimated_time = len(top_protocols) * 0.5 / self.MAX_WORKERS
            self.logger.info(
                f"   Querying details in parallel ({self.MAX_WORKERS} threads) - "
                f"estimated time: ~{estimated_time:.0f}s"
            )
            
            # ================================================================
            # STEP 4: PARALLEL DETAIL FETCHING
            # ================================================================
            contracts = []
            completed = 0
            
            # Thread-safe counter for progress
            def fetch_and_process(protocol_data):
                """Fetch details for one protocol and extract address"""
                protocol, index = protocol_data
                
                try:
                    detail = self._get_protocol_detail(protocol['slug'])
                    
                    if detail:
                        # Try different address formats
                        address = None
                        if 'address' in detail:
                            if isinstance(detail['address'], dict):
                                address = (
                                    detail['address'].get('ethereum') or 
                                    detail['address'].get('Ethereum')
                                )
                            elif isinstance(detail['address'], str):
                                address = detail['address']
                        
                        if address and self.validate_address(address):
                            return {
                                'address': address,
                                'name': protocol['name'],
                                'source': 'defillama',
                                'metadata': {
                                    'tvl': protocol.get('tvl', 0),
                                    'category': protocol.get('category', 'unknown'),
                                    'chain': chain
                                }
                            }
                    
                    # Rate limiting inside thread
                    time.sleep(0.5)
                    
                except Exception as e:
                    self.logger.debug(f"Failed to fetch {protocol.get('name', 'unknown')}: {e}")
                
                return None
            
            # Create thread pool and submit tasks
            with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
                # Submit all tasks
                futures = {
                    executor.submit(fetch_and_process, (protocol, i)): i
                    for i, protocol in enumerate(top_protocols, 1)
                }
                
                # Process results as they complete
                for future in as_completed(futures):
                    completed += 1
                    
                    # Progress updates
                    if completed % 50 == 0 or completed == 1:
                        self.logger.info(
                            f"   [{completed}/{len(top_protocols)}] "
                            f"Processed | Found {len(contracts)} valid addresses"
                        )
                    
                    result = future.result()
                    if result:
                        contracts.append(result)
                        
                        # Log milestone finds
                        if len(contracts) in [10, 25, 50, 100, 200, 300]:
                            self.logger.info(f"   🎯 Milestone: {len(contracts)} valid addresses found!")
            
            self.logger.info(f"✓ Completed DeFiLlama collection")
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
