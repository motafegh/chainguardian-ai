# src/chainguardian/data_collection/collectors/polygon_contracts.py

"""
Polygon Contracts Collector
Collects popular contracts on Polygon
"""

from typing import List, Dict
import requests
import time
from .base import BaseCollector


class PolygonCollector(BaseCollector):
    """
    Collect popular contracts on Polygon
    """
    
    BASE_URL = "https://api.polygonscan.com/api"
    
    def collect(self) -> List[Dict]:
        """Collect contracts from Polygon"""
        
        # Fix: Handle criteria properly - it could be a list or dict
        criteria = self.config.get('criteria', {})
        
        # If criteria is a list, use the first item or empty dict
        if isinstance(criteria, list):
            criteria = criteria[0] if criteria else {}
            
        count = criteria.get('count', 50)
        
        self.log_collection_start(self.config.get('name', 'Polygon'))
        
        # Popular Polygon contracts
        polygon_contracts = [
            {'address': '0x7D2768dE32b0b80b7a3454c06BdAc94A69DDc7A9', 'name': 'Aave', 'source': 'polygon', 'metadata': {'category': 'defi', 'tvl': 500000000}},
            {'address': '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063', 'name': 'QuickSwap', 'source': 'polygon', 'metadata': {'category': 'defi', 'tvl': 400000000}},
            {'address': '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270', 'name': 'WMATIC', 'source': 'polygon', 'metadata': {'category': 'defi', 'tvl': 300000000}},
            {'address': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174', 'name': 'USDC', 'source': 'polygon', 'metadata': {'category': 'defi', 'tvl': 200000000}},
            {'address': '0x1BFD6700B1Bc0710c2CD1cf56D9C6b5D7aA7B95C', 'name': 'Curve', 'source': 'polygon', 'metadata': {'category': 'defi', 'tvl': 150000000}},
            {'address': '0x4e3a36A633f63aBF0a4C4f2Dc26F757c5890Df7e', 'name': 'Balancer', 'source': 'polygon', 'metadata': {'category': 'defi', 'tvl': 100000000}},
            {'address': '0x5e74C9036fb86BD7eCdcb084a0673EFc32eA31cb', 'name': 'SushiSwap', 'source': 'polygon', 'metadata': {'category': 'defi', 'tvl': 80000000}},
            {'address': '0x8317EE7bF95B5e9C6Ad5d8b5e23b1AB27483759D', 'name': 'Cometh', 'source': 'polygon', 'metadata': {'category': 'defi', 'tvl': 50000000}},
            {'address': '0x172370d5Cd63279eFa6d502DAB29171933a610AF', 'name': 'DFYN', 'source': 'polygon', 'metadata': {'category': 'defi', 'tvl': 40000000}},
            {'address': '0x0b3F868E0BE5597D5DB7f59D4CD95787f3966418', 'name': 'Polycat', 'source': 'polygon', 'metadata': {'category': 'defi', 'tvl': 30000000}},
        ]
        
        # Filter and return requested count
        valid_contracts = [
            {
                'address': contract['address'],
                'name': contract['name'],
                'source': 'polygon',
                'metadata': contract['metadata']
            }
            for contract in polygon_contracts
            if self.validate_address(contract['address'])
        ]
        
        selected = valid_contracts[:count]
        
        self.log_collection_complete(len(selected))
        return selected