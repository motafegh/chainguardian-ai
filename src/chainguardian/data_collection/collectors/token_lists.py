"""
Token Lists Collector
=====================

Collects verified ERC-20 tokens from public token lists maintained by:
- Uniswap (most comprehensive)
- CoinGecko (curated quality tokens)
- 1inch (aggregator tokens)

These lists contain thousands of verified contracts with metadata.
"""

from typing import List, Dict
import requests
import time
from .base import BaseCollector


class TokenListCollector(BaseCollector):
    """
    Collect verified tokens from public token lists.
    
    Token lists are community-maintained JSON files following the
    Token Lists standard (https://tokenlists.org/)
    
    Features:
    - No rate limits (static JSON files)
    - Pre-verified contracts
    - Rich metadata (symbol, decimals, logoURI)
    - Thousands of contracts available
    """
    
    # Popular token list URLs
    LISTS = {
        'uniswap': 'https://tokens.uniswap.org',
        'coingecko': 'https://tokens.coingecko.com/uniswap/all.json',
        '1inch': 'https://tokens.1inch.io/v1.2/1',  # Chain ID 1 = Ethereum mainnet
    }
    
    def collect(self) -> List[Dict]:
        """
        Collect tokens from all configured token lists.
        
        Returns:
            List of contract dicts with address, name, source, metadata
        """
        criteria = self.config.get('criteria', {})
        
        # Extract config parameters
        if isinstance(criteria, list):
            # Get max tokens from criteria list
            max_tokens = next(
                (c.get('max_tokens') for c in criteria if 'max_tokens' in c),
                1000
            )
        else:
            max_tokens = criteria.get('max_tokens', 1000)
        
        self.log_collection_start(self.config.get('name', 'Token Lists'))
        
        self.logger.info(f"Fetching from {len(self.LISTS)} token lists...")
        self.logger.info(f"Max tokens per list: {max_tokens}")
        
        all_contracts = []
        seen_addresses = set()
        
        for source, url in self.LISTS.items():
            self.logger.info(f"")
            self.logger.info(f"Fetching {source.upper()} token list...")
            
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                # Extract tokens (format varies by list)
                tokens = self._extract_tokens(data, source)
                
                self.logger.info(f"✓ Received {len(tokens)} tokens from {source}")
                
                # Process tokens
                added = 0
                for token in tokens[:max_tokens]:  # Limit per list
                    address = token.get('address', '').lower()
                    
                    # Skip if we've seen this address
                    if address in seen_addresses:
                        continue
                    
                    # Validate Ethereum address format
                    if not self.validate_address(address):
                        continue
                    
                    # Add to collection
                    seen_addresses.add(address)
                    all_contracts.append({
                        'address': address,
                        'name': token.get('name', 'Unknown Token'),
                        'source': f'tokenlist_{source}',
                        'metadata': {
                            'symbol': token.get('symbol', ''),
                            'decimals': token.get('decimals', 18),
                            'chain_id': token.get('chainId', 1),
                            'logo_uri': token.get('logoURI', '')
                        }
                    })
                    added += 1
                
                self.logger.info(f"✓ Added {added} unique tokens from {source}")
                
                # Small delay between lists (be nice to servers)
                time.sleep(1)
                
            except requests.RequestException as e:
                self.logger.error(f"Failed to fetch {source}: {e}")
                continue
            except Exception as e:
                self.logger.error(f"Error processing {source}: {e}")
                continue
        
        self.logger.info(f"")
        self.logger.info(f"✓ Total unique tokens collected: {len(all_contracts)}")
        self.log_collection_complete(len(all_contracts))
        
        return all_contracts
    
    def _extract_tokens(self, data: Dict, source: str) -> List[Dict]:
        """
        Extract tokens from API response.
        
        Different token lists use different JSON structures.
        
        Args:
            data: Parsed JSON response
            source: Source name ('uniswap', 'coingecko', '1inch')
        
        Returns:
            List of token dicts
        """
        if source == '1inch':
            # 1inch uses dict of address -> token data
            # Example: {"0xabc...": {"symbol": "DAI", "name": "Dai", ...}}
            tokens = []
            for address, token_data in data.items():
                token_data['address'] = address
                tokens.append(token_data)
            return tokens
        
        else:
            # Uniswap, CoinGecko use standard token list format
            # Example: {"tokens": [{"address": "0x...", "name": "...", ...}]}
            return data.get('tokens', [])


# Convenience function for standalone testing
def test_token_lists():
    """Test token list collector standalone"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    config = {
        'name': 'token_lists_test',
        'criteria': [
            {'max_tokens': 100}  # Limit for testing
        ]
    }
    
    collector = TokenListCollector(config)
    contracts = collector.collect()
    
    print(f"\n{'='*70}")
    print(f"Test Results:")
    print(f"{'='*70}")
    print(f"Total contracts collected: {len(contracts)}")
    print(f"\nFirst 5 contracts:")
    for i, contract in enumerate(contracts[:5], 1):
        print(f"{i}. {contract['name']} ({contract['metadata']['symbol']})")
        print(f"   Address: {contract['address']}")
        print(f"   Source: {contract['source']}")
    print(f"{'='*70}\n")


# Convenience function for standalone testing
if __name__ == "__main__":
    """Test token list collector standalone"""
    import sys
    from pathlib import Path
    
    # Add project root to Python path for imports
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    # Now we can import
    from chainguardian.data_collection.collectors.token_lists import TokenListCollector
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    config = {
        'name': 'token_lists_test',
        'criteria': [
            {'max_tokens': 100}  # Limit for testing
        ]
    }
    
    collector = TokenListCollector(config)
    contracts = collector.collect()
    
    print(f"\n{'='*70}")
    print(f"Test Results:")
    print(f"{'='*70}")
    print(f"Total contracts collected: {len(contracts)}")
    print(f"\nFirst 5 contracts:")
    for i, contract in enumerate(contracts[:5], 1):
        print(f"{i}. {contract['name']} ({contract['metadata']['symbol']})")
        print(f"   Address: {contract['address']}")
        print(f"   Source: {contract['source']}")
    print(f"{'='*70}\n")
