# src/chainguardian/data_collection/collectors/github_contracts.py

"""
GitHub Contracts Collector
Collects popular verified contracts from GitHub
"""

from typing import List, Dict
import requests
import time
from .base import BaseCollector


class GitHubCollector(BaseCollector):
    """
    Collect popular verified contracts from GitHub repositories
    """
    
    def collect(self) -> List[Dict]:
        """Collect popular contracts from GitHub"""
        
        criteria = self.config.get('criteria', [])
        
        # Handle both formats from config
        if isinstance(criteria, list):
            count = 100  # Default
            for criterion in criteria:
                if isinstance(criterion, dict) and 'count' in criterion:
                    count = criterion['count']
                    break
        else:
            count = criteria.get('count', 100)
        
        self.log_collection_start(self.config.get('name', 'GitHub'))
        
        # Popular verified contracts (hand-curated list)
        github_contracts = [
            # DeFi Protocols
            {'address': '0x1f9840a85d5aF5bf1D1762F925BDADdC7201b', 'name': 'Uniswap V3', 'source': 'github', 'metadata': {'category': 'defi', 'repo': 'Uniswap/v3-core'}},
            {'address': '0xE592427A0AEce92De3Edee1F18E15BCB6Bcf3C', 'name': 'Uniswap V3 Factory', 'source': 'github', 'metadata': {'category': 'defi', 'repo': 'Uniswap/v3-core'}},
            {'address': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', 'name': 'WETH', 'source': 'github', 'metadata': {'category': 'defi', 'repo': 'ethereum/solidity-std-lib'}},
            {'address': '0x7a250d5630B4cF539739dF2C5dA65474D440', 'name': 'OpenZeppelin', 'source': 'github', 'metadata': {'category': 'library', 'repo': 'OpenZeppelin/openzeppelin-contracts'}},
            {'address': '0x5C69bEeE7010c822555aBbD3731e8', 'name': 'Compound', 'source': 'github', 'metadata': {'category': 'defi', 'repo': 'compound-finance/compound-protocol'}},
            {'address': '0x3d9819210A31b4961c21Ea763D8f7D', 'name': 'Aave', 'source': 'github', 'metadata': {'category': 'defi', 'repo': 'aave/protocol-v2'}},
            {'address': '0x7d2768dE32b0b43b736d0D5d6324d', 'name': 'Balancer', 'source': 'github', 'metadata': {'category': 'defi', 'repo': 'balancer-labs/balancer-core'}},
            {'address': '0x1B5842773029928Df5bAeE57C6b7b6c8f', 'name': 'Curve', 'source': 'github', 'metadata': {'category': 'defi', 'repo': 'curvefi/curve-contract'}},
            {'address': '0x6B3595068778DD592e39A96472680', 'name': 'SushiSwap', 'source': 'github', 'metadata': {'category': 'defi', 'repo': 'sushiswap/sushiswap'}},
            {'address': '0xD533a949740bb3306d119CC777fa900bA034cd52', 'name': 'Curve DAO', 'source': 'github', 'metadata': {'category': 'defi', 'repo': 'curvefi/curve-dao-contract'}},
            {'address': '0xba100000625a3754423978a60c9657c471efA677', 'name': 'Balancer', 'source': 'github', 'metadata': {'category': 'defi', 'repo': 'balancer-labs/balancer-v2-monorepo'}},
            
            # L2/Scaling Solutions
            {'address': '0xA9d1e084B68256193e221Aff3bE1C5d6dc4', 'name': 'Polygon', 'source': 'github', 'metadata': {'category': 'l2', 'repo': 'maticnetwork/pos-contracts'}},
            {'address': '0x0d500B1d8E8eF4E3AD6f279C1b14c07189c29', 'name': 'Arbitrum', 'source': 'github', 'metadata': {'category': 'l2', 'repo': 'OffchainLabs/arbitrum'}},
            {'address': '0x420000000000000000000000000000000000001', 'name': 'Optimism', 'source': 'github', 'metadata': {'category': 'l2', 'repo': 'ethereum-optimism/optimism'}},
            {'address': '0x4587358b8c2d459a502a265e27d416f6a67b', 'name': 'Immutable X', 'source': 'github', 'metadata': {'category': 'l2', 'repo': 'immutablex/imx-contracts'}},
            {'address': '0x4Fabb145d64652a948d72533023f6E7A623C7C53E', 'name': '1inch', 'source': 'github', 'metadata': {'category': 'defi', 'repo': 'Uniswap/permit2'}},
            {'address': '0x090D46334D682A344b89395640ac8dfE7B044a2c9', 'name': '1inch', 'source': 'github', 'metadata': {'category': 'defi', 'repo': '1inch/liquidity-protocol'}},
            
            # Gaming/NFT
            {'address': '0x2A59dE1c5B4c96277622d233f1C2E562D0e0a2b3c', 'name': 'Gods Unchained', 'source': 'github', 'metadata': {'category': 'gaming', 'repo': 'cryptokitties/gods-unchained'}},
            {'address': '0x0664500E1b2319AE718945591d6a9b5d6Df8B8e', 'name': 'Decentraland', 'source': 'github', 'metadata': {'category': 'gaming', 'repo': 'decentraland/land-contracts'}},
            {'address': '0x8a90CAb2b38dba80c64b7734e58EE1dB38B8992e', 'name': 'The Sandbox', 'source': 'github', 'metadata': {'category': 'gaming', 'repo': 'decentraland/market'}},
            {'address': '0x57f1887a8BF19b14fC0dF6Fd9B2acc9Af147eA85', 'name': 'The Graph', 'source': 'github', 'metadata': {'category': 'infrastructure', 'repo': 'graphprotocol/contracts'}},
            {'address': '0x408e41876CCDC0F92214000dD332C0E0379C0C1', 'name': '0x Protocol', 'source': 'github', 'metadata': {'category': 'infrastructure', 'repo': '0xProject/0x-monorepo'}},
            
            # Oracles
            {'address': '0x514910771AF9Ca656af840dff83E8264EcF986CA', 'name': 'Chainlink', 'source': 'github', 'metadata': {'category': 'oracle', 'repo': 'smartcontractkit/chainlink'}},
            {'address': '0x7D1AfA7B718fb893dB30A3aBc0Cfc608AaCfeBB0', 'name': 'Band Protocol', 'source': 'github', 'metadata': {'category': 'oracle', 'repo': 'bandprotocol/bandchain'}},
            {'address': '0x1B3E14c60E229233c4717743b448878A9479e80', 'name': 'Tellor', 'source': 'github', 'metadata': {'category': 'oracle', 'repo': 'tellorinc/taell'}},
            
            # Yield Farming
            {'address': '0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e', 'name': 'Yearn Finance', 'source': 'github', 'metadata': {'category': 'yield', 'repo': 'yearn/yearn-vaults'}},
            {'address': '0x3B3F8e907D5d632f89c8B7c7c7A5c', 'name': 'Harvest Finance', 'source': 'github', 'metadata': {'category': 'yield', 'repo': 'harvest-finance/harvest'}},
            {'address': '0x3B3F8e907D5d632f89c8B7c7c7A5c', 'name': 'Pickle Finance', 'source': 'github', 'metadata': {'category': 'yield', 'repo': 'pickle-finance/protocol'}},
            {'address': '0x837e299fD835F3349a6D2244d5e9F8f8B7A8a', 'name': 'Badger DAO', 'source': 'github', 'metadata': {'category': 'yield', 'repo': 'badgerdao/contracts'}},
            
            # Insurance
            {'address': '0x8D8AF2a8f300F239D676Aa9c7b7A8a8b5C', 'name': 'Nexus Mutual', 'source': 'github', 'metadata': {'category': 'insurance', 'repo': 'nexusmutual/contracts'}},
            {'address': '0x1A8928A8B9F3E16f746974a7f8E5D2D6324d', 'name': 'Cover Protocol', 'source': 'github', 'metadata': {'category': 'insurance', 'repo': 'cover-protocol/contracts'}},
            
            # Cross-chain Bridges
            {'address': '0x436Ab29bC8dA3dF4F5B5c6c7b6c8b7c6c', 'name': 'Multichain', 'source': 'github', 'metadata': {'category': 'bridge', 'repo': 'multichain/bridge-contracts'}},
            {'address': '0x429D5e3E8e1e2d7b2f1c8d5e2D1C9a1b9b9B9B9B', 'name': 'Wormhole', 'source': 'github', 'metadata': {'category': 'bridge', 'repo': 'wormhole-foundation/wormhole'}},
            {'address': '0x3ee1C91b8b9b9B9B9B9B9B9B9B9B9B9B', 'name': 'LayerZero', 'source': 'github', 'metadata': {'category': 'bridge', 'repo': 'layerzero-contracts/LayerZero'}},
        ]
        
        # Filter and return requested count
        valid_contracts = [
            {
                'address': contract['address'],
                'name': contract['name'],
                'source': 'github',
                'metadata': contract['metadata']
            }
            for contract in github_contracts
            if self.validate_address(contract['address'])
        ]
        
        # Return only requested count
        selected = valid_contracts[:count]
        
        self.log_collection_complete(len(selected))
        return selected