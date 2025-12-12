"""
Collectors package
Each collector knows how to fetch contracts from one data source
"""

from .base import BaseCollector
from .defi_llama import DeFiLlamaCollector
from .coingecko import CoinGeckoCollector
from .manual_curated import ManualCuratedCollector

__all__ = [
    'BaseCollector',
    'DeFiLlamaCollector',
    'CoinGeckoCollector',
    'ManualCuratedCollector',
]
