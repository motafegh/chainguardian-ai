# Create src/chainguardian/data_collection/collectors/random_etherscan.py

"""
Random Etherscan Collector
Fetches random verified contracts from Etherscan API
"""

from typing import List, Dict
import requests
import random
import time
from .base import BaseCollector


class RandomEtherscanCollector(BaseCollector):
    """Collect random verified contracts from Etherscan"""
    
    def collect(self) -> List[Dict]:
        """Collect random verified contracts"""
        
        criteria = self.config.get('criteria', [])
        
        # Handle list format from config
        count = 100  # Default value
        
        # Extract count from criteria list
        for criterion in criteria:
            if isinstance(criterion, dict) and 'count' in criterion:
                count = criterion['count']
                break
        
        self.log_collection_start(self.config.get('name', 'Random Etherscan'))
        
        contracts = []
        
        try:
            # Get recent blocks
            latest_block = self._get_latest_block()
            
            # Check blocks for contract creations
            for i in range(0, 1000, 10):  # Check every 10th block for efficiency
                block_number = latest_block - i
                
                # Get transactions in this block
                txs = self._get_block_transactions(block_number)
                
                # Look for contract creation transactions
                for tx in txs:
                    if tx.get('contractAddress'):
                        address = tx['contractAddress']
                        
                        # Check if contract is verified
                        if self._is_verified(address):
                            contracts.append({
                                'address': address,
                                'name': f"Contract_{address[:8]}",
                                'source': 'random_etherscan',
                                'metadata': {
                                    'block_number': block_number,
                                    'creation_tx': tx.get('hash')
                                }
                            })
                            
                            if len(contracts) >= count:
                                break
                
                if len(contracts) >= count:
                    break
                
                time.sleep(0.2)  # Rate limiting
            
            # If we don't have enough, add some known verified contracts
            if len(contracts) < count:
                known_contracts = self._get_known_verified_contracts(count - len(contracts))
                contracts.extend(known_contracts)
            
        except Exception as e:
            self.logger.error(f"Error collecting random contracts: {e}")
        
        self.log_collection_complete(len(contracts))
        return contracts
    
    def _get_latest_block(self) -> int:
        """Get latest block number"""
        try:
            response = requests.get(
                'https://api.etherscan.io/api',
                params={
                    'module': 'proxy',
                    'action': 'eth_blockNumber',
                    'apikey': self.config.get('etherscan_api_key', 'YourApiKey')
                },
                timeout=10
            )
            response.raise_for_status()
            return int(response.json()['result'], 16)
        except Exception as e:
            self.logger.error(f"Error getting latest block: {e}")
            return 18000000  # Fallback to a recent block
    
    def _get_block_transactions(self, block_number: int) -> List[Dict]:
        """Get transactions in a block"""
        try:
            response = requests.get(
                'https://api.etherscan.io/api',
                params={
                    'module': 'proxy',
                    'action': 'eth_getBlockByNumber',
                    'tag': hex(block_number),
                    'boolean': 'true',
                    'apikey': self.config.get('etherscan_api_key', 'YourApiKey')
                },
                timeout=10
            )
            response.raise_for_status()
            block_data = response.json()
            return block_data.get('result', {}).get('transactions', [])
        except Exception as e:
            self.logger.error(f"Error getting block transactions: {e}")
            return []
    
    def _is_verified(self, address: str) -> bool:
        """Check if contract is verified"""
        try:
            response = requests.get(
                'https://api.etherscan.io/api',
                params={
                    'module': 'contract',
                    'action': 'getsourcecode',
                    'address': address,
                    'apikey': self.config.get('etherscan_api_key', 'YourApiKey')
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == '1' and data.get('result'):
                result = data['result'][0]
                return result.get('SourceCode', '') != ''
            
            return False
        except Exception as e:
            self.logger.error(f"Error checking verification: {e}")
            return False
    
    def _get_known_verified_contracts(self, count: int) -> List[Dict]:
        """Get some known verified contracts as fallback"""
        known_contracts = [
            # ERC20 Tokens
            {'address': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', 'name': 'USDC'},
            {'address': '0xdAC17F958D2ee523a2206206994597C13D831ec7', 'name': 'USDT'},
            {'address': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599', 'name': 'WBTC'},
            {'address': '0x6B175474e89094c44da98b954eedeac495271d0F', 'name': 'DAI'},
            {'address': '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984', 'name': 'UNI'},
            {'address': '0x514910771AF9Ca656af840dff83E8264EcF986CA', 'name': 'LINK'},
            {'address': '0xD533a949740bb3306d119CC777fa900bA034cd52', 'name': 'CRV'},
            {'address': '0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9', 'name': 'AAVE'},
            {'address': '0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e', 'name': 'YFI'},
            {'address': '0x6B3595068778DD592e39A122f4f5a5cF09C90fE2', 'name': 'SUSHI'},
            
            # DeFi Protocols
            {'address': '0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9', 'name': 'Aave Lending Pool'},
            {'address': '0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B', 'name': 'Compound Comptroller'},
            {'address': '0xE592427A0AEce92De3Edee1F18E0157C05861564', 'name': 'Uniswap V3 Factory'},
            {'address': '0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac', 'name': 'Uniswap V2 Router'},
            {'address': '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F', 'name': 'SushiSwap Router'},
            {'address': '0x1E19CF2B73f3c1B9955B8375448C0B4B5C9c762', 'name': 'Balancer Vault'},
            {'address': '0xBA12222222228d8Ba445958a75a0704d566BF2C8', 'name': 'Balancer Pool'},
            {'address': '0x6b3595068778dd592e39a122f4f5a5cf09c90fe2', 'name': 'SushiSwap'},
            {'address': '0x111111125421cA6dc452d289314280a0f8842A65', 'name': '1inch v3'},
            {'address': '0x1111111254EEB25477B68fb85Ed929f73A960582', 'name': '1inch v4'},
            
            # NFT Projects
            {'address': '0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D', 'name': 'Bored Ape Yacht Club'},
            {'address': '0x60E4d786628Fea6478F785A6d7e704777c86a7c6', 'name': 'Mutant Ape Yacht Club'},
            {'address': '0x495f947276749Ce646f68AC8c248420045cb7b5e', 'name': 'OpenSea Shared Storefront'},
            {'address': '0x23581767a106ae21c074b2276D25e5C3E136a68b', 'name': 'Creature World'},
            {'address': '0x1CB981c5F7c902966237595c820Bf10f285292a6', 'name': 'Doodles'},
            {'address': '0x2953399124F0cBB46d2CbACD8A89cF0599974963', 'name': 'Sandbox LANDs'},
            {'address': '0x57f1887a8BF19b14fC0dF6Fd9B2acc9Af147eA85', 'name': 'ENS .eth Names'},
            {'address': '0x8a90CAb2b38dba80c64b7734e58EE1dB38B8992e', 'name': 'Decentraland Wearables'},
            {'address': '0x2A46f2FD99e16a1827Fc95688CC14cD35b6B48A8', 'name': 'Meebits'},
            {'address': '0x05aEDf5B64F56F868a0a240d11A072a6e98E5B6c', 'name': 'Pudgy Penguins'},
        ]
        
        # Randomly select from known contracts
        selected = random.sample(known_contracts, min(count, len(known_contracts)))
        
        return [
            {
                'address': contract['address'],
                'name': contract['name'],
                'source': 'known_verified',
                'metadata': {
                    'type': 'verified_contract'
                }
            }
            for contract in selected
        ]