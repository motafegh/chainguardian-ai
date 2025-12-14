"""
Base Collector Interface
All collectors inherit from this to ensure consistent API
"""

from abc import ABC, abstractmethod
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """
    Abstract base class for all collectors
    
    WHY: Ensures all collectors have the same interface
    HOW: Child classes must implement collect() method
    """
    
    def __init__(self, config: Dict):
        """
        Initialize collector with configuration
        
        Args:
            config: Dictionary with collector-specific settings
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def collect(self) -> List[Dict]:
        """
        Collect contracts based on criteria
        
        MUST BE IMPLEMENTED by child classes
        
        Returns:
            List of dicts with at minimum:
            [
                {
                    'address': '0x...',
                    'name': 'ContractName',
                    'source': 'defillama|coingecko|manual',
                    'metadata': {...}
                },
                ...
            ]
        """
        pass
    
    def validate_address(self, address: str) -> bool:
        """Validate Ethereum address format"""
        if not address:
            return False
        if not address.startswith('0x'):
            return False
        if len(address) != 42:
            return False
        try:
            int(address, 16)
            return True
        except ValueError:
            return False
    
    def log_collection_start(self, stratum_name: str):
        """Helper: Log start of collection"""
        self.logger.info(f"Starting collection for stratum: {stratum_name}")
    
    def log_collection_complete(self, count: int):
        """Helper: Log completion"""
        self.logger.info(f"✓ Collected {count} contracts")