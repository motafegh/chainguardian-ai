"""
Manual Curated Collector
For vulnerable and old contracts
"""

from typing import List, Dict
from .base import BaseCollector


class ManualCuratedCollector(BaseCollector):
    """Collect manually curated contracts"""
    
    KNOWN_VULNERABLE = [
        {'address': '0xBB9bc244D798123fDe783fCc1C72d3Bb8C189413', 'name': 'The DAO', 'exploit_type': 'reentrancy', 'loss_usd': 60000000},
        {'address': '0x863DF6BFa4469f3ead0bE8f9F2AAE51c91A907b4', 'name': 'Parity Multi-Sig', 'exploit_type': 'access_control', 'loss_usd': 30000000},
        {'address': '0x1dBA1131000664b884A1Ba238464159892252D3a', 'name': 'Parity Wallet', 'exploit_type': 'delegatecall', 'loss_usd': 150000000},
        {'address': '0xC5d105E63711398aF9bbff092d4B6769C82F793D', 'name': 'BEC Token', 'exploit_type': 'integer_overflow', 'loss_usd': 900000000},
        {'address': '0x0eEe3E3828A45f7601D5F54bF49bB01d1A9dF5ea', 'name': 'Lendf.me', 'exploit_type': 'reentrancy', 'loss_usd': 25000000},
        {'address': '0x053c80eA73Dc6941F518a68E2FC52Ac45BDE7c9C', 'name': 'Harvest Finance', 'exploit_type': 'flash_loan', 'loss_usd': 34000000},
        {'address': '0xbD17B1ce622d73bD438b9E658acA5996dc394b0d', 'name': 'Pickle Finance', 'exploit_type': 'logic_error', 'loss_usd': 20000000},
        {'address': '0x2Db6c82CE72C8d7D770ba1b5F5Ed0b6E075066d6', 'name': 'Cream Finance', 'exploit_type': 'flash_loan', 'loss_usd': 130000000},
        {'address': '0x250e76987d838a75310c34bf422ea9f1AC4Cc906', 'name': 'Poly Network', 'exploit_type': 'access_control', 'loss_usd': 611000000},
        {'address': '0x1fcdb04d0c5364fbd92c73ca8af9baa72c269107', 'name': 'Badger DAO', 'exploit_type': 'frontend_attack', 'loss_usd': 120000000},
    ]
    
    OLD_CONTRACTS = [
        {'address': '0x86fa049857e0209aa7d9e616f7eb3b3b78ecfdb0', 'name': 'EOS Token', 'solidity_version': '0.4.11'},
        {'address': '0xd850942ef8811f2a866692a623011bde52a462c1', 'name': 'VeChain Token', 'solidity_version': '0.4.8'},
        {'address': '0xf230b790e05390fc8295f4d3f60332c93bed42e2', 'name': 'Tron Token', 'solidity_version': '0.4.11'},
        {'address': '0x8d12A197cB00D4747a1fe03395095ce2A5CC6819', 'name': 'EtherDelta', 'solidity_version': '0.4.9'},
        {'address': '0xa74476443119A942dE498590Fe1f2454d7D4aC0d', 'name': 'Golem Token', 'solidity_version': '0.4.11'},
    ]
    
    def collect(self) -> List[Dict]:
        """Collect based on criteria"""
        
        criteria = self.config.get('criteria', {})
        
        # Handle list format
        if isinstance(criteria, list):
            # Check which type
            has_database = any('from_database' in c for c in criteria)
            has_version = any('solidity_version' in c for c in criteria)
        else:
            has_database = 'from_database' in criteria
            has_version = 'solidity_version' in criteria
        
        self.log_collection_start(self.config.get('name', 'Manual'))
        
        contracts = []
        
        if has_database:
            # Vulnerable contracts
            for vuln in self.KNOWN_VULNERABLE:
                contracts.append({
                    'address': vuln['address'],
                    'name': vuln['name'],
                    'source': 'manual_curated',
                    'metadata': {
                        'type': 'vulnerable',
                        'exploit_type': vuln['exploit_type'],
                        'loss_usd': vuln['loss_usd']
                    }
                })
        
        if has_version:
            # Old contracts
            for old in self.OLD_CONTRACTS:
                contracts.append({
                    'address': old['address'],
                    'name': old['name'],
                    'source': 'manual_curated',
                    'metadata': {
                        'type': 'old_version',
                        'solidity_version': old['solidity_version']
                    }
                })
        
        self.log_collection_complete(len(contracts))
        return contracts
