"""
Contract Address Discovery

Multiple strategies to find verified smart contracts:
1. Top contracts by transaction count
2. Popular tokens (ERC20/ERC721)
3. DeFi protocols
4. Recent deployments

Author: ChainGuardian AI Team
Date: December 2025
"""

import os
import time
import requests
from typing import List, Set
import logging
from pathlib import Path
from dotenv import load_dotenv
import json

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class ContractDiscovery:
    """
    Discover verified contract addresses from Etherscan.
    
    Strategies:
    - Top contracts by gas usage
    - Popular token contracts
    - DeFi protocols
    - Recent verified contracts
    """
    
    BASE_URL = "https://api.etherscan.io/api"
    RATE_LIMIT = 0.21  # 4.76 calls/sec
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ETHERSCAN_API_KEY")
        if not self.api_key:
            raise ValueError("ETHERSCAN_API_KEY required")
        
        self._last_request = 0.0
    
    def _rate_limit(self):
        """Respect API rate limits."""
        elapsed = time.time() - self._last_request
        if elapsed < self.RATE_LIMIT:
            time.sleep(self.RATE_LIMIT - elapsed)
        self._last_request = time.time()
    
    def _make_request(self, params: dict) -> dict:
        """Make API request with rate limiting."""
        self._rate_limit()
        
        params['apikey'] = self.api_key
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {}
    
    # ================================================================
    # STRATEGY 1: Get contracts from recent blocks
    # ================================================================
    
    def get_contracts_from_blocks(
        self,
        start_block: int,
        end_block: int,
        max_contracts: int = 1000
    ) -> Set[str]:
        """
        Extract contract addresses from block transactions.
        
        Args:
            start_block: Starting block number
            end_block: Ending block number
            max_contracts: Maximum addresses to collect
        
        Returns:
            Set of contract addresses
        """
        logger.info(f"Scanning blocks {start_block} to {end_block}...")
        
        contracts = set()
        
        for block_num in range(start_block, end_block + 1):
            if len(contracts) >= max_contracts:
                break
            
            # Get block transactions
            params = {
                'module': 'proxy',
                'action': 'eth_getBlockByNumber',
                'tag': hex(block_num),
                'boolean': 'true'
            }
            
            data = self._make_request(params)
            
            if 'result' in data and data['result']:
                block = data['result']
                
                if 'transactions' in block:
                    for tx in block['transactions']:
                        # Contract creation (to address is null)
                        if tx.get('to') is None and tx.get('contractAddress'):
                            contracts.add(tx['contractAddress'])
                        # Regular contract interaction
                        elif tx.get('to'):
                            contracts.add(tx['to'])
            
            if block_num % 100 == 0:
                logger.info(f"  Block {block_num}: {len(contracts)} contracts found")
        
        logger.info(f"✓ Found {len(contracts)} unique addresses from blocks")
        return contracts
    
    # ================================================================
    # STRATEGY 2: Get verified contracts list
    # ================================================================
    
    def get_verified_contracts(
        self,
        page: int = 1,
        offset: int = 100
    ) -> List[str]:
        """
        Get list of recently verified contracts.
        
        Etherscan endpoint: Returns 10,000 most recent verified contracts
        
        Args:
            page: Page number (1-indexed)
            offset: Results per page (max 100)
        
        Returns:
            List of verified contract addresses
        """
        params = {
            'module': 'contract',
            'action': 'getverifiedcontracts',
            'page': page,
            'offset': offset
        }
        
        data = self._make_request(params)
        
        if data.get('status') == '1' and 'result' in data:
            addresses = [item['ContractAddress'] for item in data['result']]
            logger.info(f"✓ Page {page}: {len(addresses)} verified contracts")
            return addresses
        
        return []
    
    def get_all_verified_contracts(self, max_contracts: int = 10000) -> List[str]:
        """
        Fetch multiple pages of verified contracts.
        
        Args:
            max_contracts: Maximum contracts to fetch
        
        Returns:
            List of verified contract addresses
        """
        logger.info(f"Fetching up to {max_contracts} verified contracts...")
        
        all_contracts = []
        page = 1
        offset = 100
        
        while len(all_contracts) < max_contracts:
            contracts = self.get_verified_contracts(page, offset)
            
            if not contracts:
                break  # No more results
            
            all_contracts.extend(contracts)
            page += 1
            
            logger.info(f"  Total collected: {len(all_contracts)}")
        
        return all_contracts[:max_contracts]
    
    # ================================================================
    # STRATEGY 3: Popular token addresses
    # ================================================================
    
    def get_popular_tokens(self) -> List[str]:
        """
        Get addresses of popular tokens.
        
        Returns:
            List of well-known token addresses
        """
        # Top ERC20 tokens by market cap
        popular_tokens = [
            # Stablecoins
            "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
            "0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAI
            "0x4Fabb145d64652a948d72533023f6E7A623C7C53",  # BUSD
            
            # Major tokens
            "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",  # UNI
            "0x7D1AfA7B718fb893dB30A3aBc0Cfc608AaCfeBB0",  # MATIC
            "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",  # WBTC
            "0x514910771AF9Ca656af840dff83E8264EcF986CA",  # LINK
            "0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE",  # SHIB
            
            # DeFi protocols
            "0x6B3595068778DD592e39A122f4f5a5cF09C90fE2",  # SUSHI
            "0xC011a73ee8576Fb46F5E1c5751cA3B9Fe0af2a6F",  # SNX
            "0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e",  # YFI
            "0xba100000625a3754423978a60c9317c58a424e3D",  # BAL
            
            # Uniswap V2/V3
            "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",  # Uniswap V2 Factory
            "0x1F98431c8aD98523631AE4a59f267346ea31F984",  # Uniswap V3 Factory
            
            # DEXes
            "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",  # Uniswap V2 Router
            "0xE592427A0AEce92De3Edee1F18E0157C05861564",  # Uniswap V3 Router
            
            # Lending
            "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9",  # Aave V2 Pool
            "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",  # Aave V3 Pool
            
            # NFT
            "0xb47e3cd837dDF8e4c57F05d70Ab865de6e193BBB",  # CryptoPunks
            "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D",  # BAYC
        ]
        
        logger.info(f"✓ Loaded {len(popular_tokens)} popular token addresses")
        return popular_tokens
    
    # ================================================================
    # STRATEGY 4: Contracts by transaction volume
    # ================================================================
    
    def get_top_gas_consumers(self, days: int = 7) -> List[str]:
        """
        Get contracts that consumed most gas recently.
        
        Note: This requires Etherscan Pro API
        
        Args:
            days: Number of days to look back
        
        Returns:
            List of contract addresses
        """
        # This would require Pro API or alternative data source
        # For now, return empty list
        logger.warning("Top gas consumers requires Pro API - skipping")
        return []
    
    # ================================================================
    # MAIN DISCOVERY METHOD
    # ================================================================
    
    def discover_contracts(
        self,
        strategy: str = "verified",
        max_contracts: int = 5000
    ) -> List[str]:
        """
        Discover contracts using specified strategy.
        
        Args:
            strategy: Discovery method
                - "verified": Recently verified contracts
                - "popular": Well-known tokens/protocols
                - "blocks": Scan recent blocks
                - "all": Combine all strategies
            max_contracts: Maximum contracts to return
        
        Returns:
            List of unique contract addresses
        """
        all_addresses = set()
        
        logger.info(f"\n{'='*70}")
        logger.info(f"CONTRACT DISCOVERY: {strategy.upper()}")
        logger.info(f"Target: {max_contracts} contracts")
        logger.info(f"{'='*70}\n")
        
        if strategy in ["verified", "all"]:
            verified = self.get_all_verified_contracts(max_contracts)
            all_addresses.update(verified)
            logger.info(f"Added {len(verified)} verified contracts")
        
        if strategy in ["popular", "all"]:
            popular = self.get_popular_tokens()
            all_addresses.update(popular)
            logger.info(f"Added {len(popular)} popular contracts")
        
        if strategy in ["blocks", "all"]:
            # Get latest block
            latest_block_data = self._make_request({
                'module': 'proxy',
                'action': 'eth_blockNumber'
            })
            
            if 'result' in latest_block_data:
                latest_block = int(latest_block_data['result'], 16)
                start_block = latest_block - 1000  # Last 1000 blocks
                
                block_contracts = self.get_contracts_from_blocks(
                    start_block,
                    latest_block,
                    max_contracts=1000
                )
                all_addresses.update(block_contracts)
                logger.info(f"Added {len(block_contracts)} from recent blocks")
        
        result = list(all_addresses)[:max_contracts]
        
        logger.info(f"\n{'='*70}")
        logger.info(f"✓ Discovery complete: {len(result)} unique contracts")
        logger.info(f"{'='*70}\n")
        
        return result


# ================================================================
# CLI USAGE
# ================================================================

def main():
    """Discover and save contract addresses."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Discover contract addresses')
    parser.add_argument(
        '--strategy',
        choices=['verified', 'popular', 'blocks', 'all'],
        default='verified',
        help='Discovery strategy'
    )
    parser.add_argument(
        '--max-contracts',
        type=int,
        default=5000,
        help='Maximum contracts to discover'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/contract_addresses.txt',
        help='Output file for addresses'
    )
    
    args = parser.parse_args()
    
    # Discover contracts
    discovery = ContractDiscovery()
    addresses = discovery.discover_contracts(
        strategy=args.strategy,
        max_contracts=args.max_contracts
    )
    
    # Save to file
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(addresses))
    
    logger.info(f"✓ Saved {len(addresses)} addresses to {output_path}")


if __name__ == "__main__":
    main()
