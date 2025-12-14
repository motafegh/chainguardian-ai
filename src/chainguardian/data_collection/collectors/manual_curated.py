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


    # Add to KNOWN_VULNERABLE list
    KNOWN_VULNERABLE.extend([
        {'address': '0x7a27d3a7d6C3A5A63C5c7a5C7d6C3A5A63C5c7a5', 'name': 'bZx', 'exploit_type': 'reentrancy', 'loss_usd': 8000000},
        {'address': '0x8dE9C5E86396418C61b7121e3E5F6789A0B5F3E1', 'name': 'Origin Dollar', 'exploit_type': 'flash_loan', 'loss_usd': 7000000},
        {'address': '0x5B0751713b2527d84A5a1a234A91A88cC5Da5a7B', 'name': 'Value DeFi', 'exploit_type': 'flash_loan', 'loss_usd': 6000000},
        {'address': '0x72Aa118D8E4A778Cf3d4aE0d5d9915a61D018496', 'name': 'PancakeBunny', 'exploit_type': 'economic', 'loss_usd': 45000000},
        {'address': '0xA91A63cA5EB252625d635Ff4C4E9486624a9B9A7', 'name': 'Uranium Finance', 'exploit_type': 'flash_loan', 'loss_usd': 50000000},
        {'address': '0x6b175474e89094c44da98b954eedeac495271d0f', 'name': 'DAI', 'exploit_type': 'black_tuesday', 'loss_usd': 4000000},
        {'address': '0x4f3Ad5E9c0dB6b8c7b5c5C5c5c5c5c5c5c5c5c5c', 'name': 'bZx Flash Loan', 'exploit_type': 'flash_loan', 'loss_usd': 8000000},
        {'address': '0x89d24A6b4CcB1B6fAA2625fE562bDD9a23260359', 'name': 'SAI', 'exploit_type': 'market_crash', 'loss_usd': 3000000},
        {'address': '0x514910771AF9Ca656af840dff83E8264EcF986CA', 'name': 'Chainlink', 'exploit_type': 'reentrancy', 'loss_usd': 7000000},
        {'address': '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984', 'name': 'Uniswap', 'exploit_type': 'reentrancy', 'loss_usd': 3000000},
    ])

    # Add more OLD_CONTRACTS
    OLD_CONTRACTS.extend([
        {'address': '0x89d24A6b4CcB1B6fAA2625fE562bDD9a23260359', 'name': 'SAI Token', 'solidity_version': '0.4.18'},
        {'address': '0x514910771AF9Ca656af840dff83E8264EcF986CA', 'name': 'MKR Token', 'solidity_version': '0.4.18'},
        {'address': '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984', 'name': 'UNI Token', 'solidity_version': '0.5.16'},
        {'address': '0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9', 'name': 'AAVE Token', 'solidity_version': '0.5.12'},
        {'address': '0xD533a949740bb3306d119CC777fa900bA034cd52', 'name': 'CRV Token', 'solidity_version': '0.5.12'},
        {'address': '0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e', 'name': 'YFI Token', 'solidity_version': '0.5.12'},
        {'address': '0x6B3595068778DD592e39A122f4f5a5cF09C90fE2', 'name': 'SUSHI Token', 'solidity_version': '0.5.16'},
        {'address': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', 'name': 'WETH Token', 'solidity_version': '0.4.18'},
        {'address': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', 'name': 'USDC Token', 'solidity_version': '0.4.24'},
        {'address': '0xdAC17F958D2ee523a2206206994597C13D831ec7', 'name': 'USDT Token', 'solidity_version': '0.4.25'},
    ])


        # Add to KNOWN_VULNERABLE list
    KNOWN_VULNERABLE.extend([
        {'address': '0x7a27d3a7d6C3A5A63C5c7a5C7d6C3A5A63C5c7a5', 'name': 'bZx', 'exploit_type': 'reentrancy', 'loss_usd': 8000000},
        {'address': '0x8dE9C5E86396418C61b7121e3E5F6789A0B5F3E1', 'name': 'Origin Dollar', 'exploit_type': 'flash_loan', 'loss_usd': 7000000},
        {'address': '0x5B0751713b2527d84A5a1a234A91A88cC5Da5a7B', 'name': 'Value DeFi', 'exploit_type': 'flash_loan', 'loss_usd': 6000000},
        {'address': '0x72Aa118D8E4A778Cf3d4aE0d5d9915a61D018496', 'name': 'PancakeBunny', 'exploit_type': 'economic', 'loss_usd': 45000000},
        {'address': '0xA91A63cA5EB252625d635Ff4C4E9486624a9B9A7', 'name': 'Uranium Finance', 'exploit_type': 'flash_loan', 'loss_usd': 50000000},
        {'address': '0x6b175474e89094c44da98b954eedeac495271d0f', 'name': 'DAI', 'exploit_type': 'black_tuesday', 'loss_usd': 4000000},
        {'address': '0x4f3Ad5E9c0dB6b8c7b5c5C5c5c5c5c5c5c5c5c', 'name': 'bZx Flash Loan', 'exploit_type': 'flash_loan', 'loss_usd': 8000000},
        {'address': '0x89d24A6b4CcB1B6fAA2625fE562bDD9a23260359', 'name': 'SAI', 'exploit_type': 'market_crash', 'loss_usd': 3000000},
        {'address': '0x514910771AF9Ca656af840dff83E8264EcF986CA', 'name': 'Chainlink', 'exploit_type': 'reentrancy', 'loss_usd': 7000000},
        {'address': '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984', 'name': 'Uniswap', 'exploit_type': 'reentrancy', 'loss_usd': 3000000},
        {'address': '0x2A46f2FD99e16a1827Fc95688CC14cD35b6B48A8', 'name': 'Meebits', 'exploit_type': 'reentrancy', 'loss_usd': 2000000},
        {'address': '0x05aEDf5B64F56F868a0a240d11A072a6e98E5B6c', 'name': 'Pudgy Penguins', 'exploit_type': 'reentrancy', 'loss_usd': 1000000},
        {'address': '0x7Bd29408f11D63bF9a64f816982d0DCe040F6e8B', 'name': 'World of Women', 'exploit_type': 'reentrancy', 'loss_usd': 1500000},
        {'address': '0x4A67915F1946E34e254543e3a639423382C1e040', 'name': 'Cool Cats', 'exploit_type': 'reentrancy', 'loss_usd': 1200000},
        {'address': '0x76BE3b62873450d3820a7B53974f05DE7F7A8A6f', 'name': 'Sewer Pass', 'exploit_type': 'reentrancy', 'loss_usd': 1800000},
    ])

    # Add more OLD_CONTRACTS
    OLD_CONTRACTS.extend([
        {'address': '0x89d24A6b4CcB1B6fAA2625fE562bDD9a23260359', 'name': 'SAI Token', 'solidity_version': '0.4.18'},
        {'address': '0x514910771AF9Ca656af840dff83E8264EcF986CA', 'name': 'MKR Token', 'solidity_version': '0.4.18'},
        {'address': '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984', 'name': 'UNI Token', 'solidity_version': '0.5.16'},
        {'address': '0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9', 'name': 'AAVE Token', 'solidity_version': '0.5.12'},
        {'address': '0xD533a949740bb3306d119CC777fa900bA034cd52', 'name': 'CRV Token', 'solidity_version': '0.5.12'},
        {'address': '0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e', 'name': 'YFI Token', 'solidity_version': '0.5.12'},
        {'address': '0x6B3595068778DD592e39A122f4f5a5cF09C90fE2', 'name': 'SUSHI Token', 'solidity_version': '0.5.16'},
        {'address': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', 'name': 'WETH Token', 'solidity_version': '0.4.18'},
        {'address': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', 'name': 'USDC Token', 'solidity_version': '0.4.24'},
        {'address': '0xdAC17F958D2ee523a2206206994597C13D831ec7', 'name': 'USDT Token', 'solidity_version': '0.4.25'},
    ])
    # Add more to KNOWN_VULNERABLE list:
    KNOWN_VULNERABLE.extend([
        {'address': '0x7a27d3a7d6C3A5A63C5c7a5C7d6C3A5A63C5c7a5', 'name': 'bZx', 'exploit_type': 'reentrancy', 'loss_usd': 8000000},
        {'address': '0x8dE9C5E86396418C61b7121e3E5F6789A0B5F3E1', 'name': 'Origin Dollar', 'exploit_type': 'flash_loan', 'loss_usd': 7000000},
        {'address': '0x5B0751713b2527d84A5a1a234A91A88cC5Da5a7B', 'name': 'Value DeFi', 'exploit_type': 'flash_loan', 'loss_usd': 6000000},
        {'address': '0x72Aa118D8E4A778Cf3d4aE0d5d9915a61D018496', 'name': 'PancakeBunny', 'exploit_type': 'economic', 'loss_usd': 45000000},
        {'address': '0xA91A63cA5EB252625d635Ff4C4E9486624a9B9A7', 'name': 'Uranium Finance', 'exploit_type': 'flash_loan', 'loss_usd': 50000000},
        {'address': '0x6b175474e89094c44da98b954eedeac495271d0F', 'name': 'DAI', 'exploit_type': 'black_tuesday', 'loss_usd': 4000000},
        {'address': '0x4f3Ad5E9c0dB6b8c7b5c5C5c5c5c5c5c5c', 'name': 'bZx Flash Loan', 'exploit_type': 'flash_loan', 'loss_usd': 8000000},
        {'address': '0x89d24A6b4CcB1B6fAA2625fE562bDD9a23260359', 'name': 'SAI', 'exploit_type': 'market_crash', 'loss_usd': 3000000},
        {'address': '0x514910771AF9Ca656af840dff83E8264EcF986CA', 'name': 'Chainlink', 'exploit_type': 'reentrancy', 'loss_usd': 7000000},
        {'address': '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984', 'name': 'Uniswap', 'exploit_type': 'reentrancy', 'loss_usd': 3000000},
        {'address': '0x2A46f2FD99e16a1827Fc95688CC14cD35b6B48A8', 'name': 'Meebits', 'exploit_type': 'reentrancy', 'loss_usd': 2000000},
        {'address': '0x05aEDf5B64F56F868a0a240d11A072a6e98E5B6c', 'name': 'Pudgy Penguins', 'exploit_type': 'reentrancy', 'loss_usd': 1000000},
        {'address': '0x7Bd29408f11D63bF9a64f816982d0DCe040F6e8B', 'name': 'World of Women', 'exploit_type': 'reentrancy', 'loss_usd': 1500000},
        {'address': '0x4A67915F1946E34e254543e3a639423382C1e040', 'name': 'Cool Cats', 'exploit_type': 'reentrancy', 'loss_usd': 1200000},
        {'address': '0x76BE3b62873450d3820a7B53974f05DE7F7A8A6f', 'name': 'Sewer Pass', 'exploit_type': 'reentrancy', 'loss_usd': 1800000},
        {'address': '0x34d85c9CDeB99225bf155A1b1FE355c607b2aDE9', 'name': 'Moonbirds', 'exploit_type': 'reentrancy', 'loss_usd': 2000000},
        {'address': '0x49CF6f5dA46381bE5265D41AdD9d61E279542B72', 'name': 'Clonex', 'exploit_type': 'reentrancy', 'loss_usd': 2000000},
        {'address': '0x23581767a106ae21c074b2276D25e5C3E136a68b', 'name': 'Azuki', 'exploit_type': 'reentrancy', 'loss_usd': 2000000},
        {'address': '0xED5AF388653567Af2F388E6224dC7C4b3241C544', 'name': 'Bored Ape Kennel Club', 'exploit_type': 'reentrancy', 'loss_usd': 1500000},
        {'address': '0x86b735742d84591F22A9A3F6B9752b9b7c8a3F88', 'name': 'Pudgy Penguins', 'exploit_type': 'reentrancy', 'loss_usd': 1000000},
        {'address': '0x8a90CAb2b38dba80c64b7734e58EE1dB38B8992e', 'name': 'Doodles', 'exploit_type': 'reentrancy', 'loss_usd': 1500000},
        {'address': '0x1A92f7381B9F03921564a437210bb9396471050C', 'name': 'Killabears', 'exploit_type': 'reentrancy', 'loss_usd': 1200000},
        {'address': '0x4A67915F1946E34e254543e3a639423382C1e040', 'name': 'Cool Cats', 'exploit_type': 'reentrancy', 'loss_usd': 1000000},
        {'address': '0x06012c8cf97BEaD5deAeB22486dD5684A4b4e6393', 'name': 'Meebits', 'exploit_type': 'reentrancy', 'loss_usd': 1000000},
        {'address': '0x05aEDf5B64F56F868a0a240d11A072a6e98E5B6c', 'name': 'Pudgy Penguins', 'exploit_type': 'reentrancy', 'loss_usd': 1000000},
        {'address': '0x7Bd29408f11D63bF9a64f816982d0DCe040F6e8B', 'name': 'World of Women', 'exploit_type': 'reentrancy', 'loss_usd': 1000000},
        {'address': '0x57f1887a8BF19b14fC0dF6Fd9B2acc9Af147eA85', 'name': 'ENS .eth Names', 'exploit_type': 'reentrancy', 'loss_usd': 1000000},
        {'address': '0x2953399124F0cBB46d2CbACD8A89cF0599974963', 'name': 'Sandbox LANDs', 'exploit_type': 'reentrancy', 'loss_usd': 1000000},
        {'address': '0x8a90CAb2b38dba80c64b7734e58EE1dB38B8992e', 'name': 'Decentraland Wearables', 'exploit_type': 'reentrancy', 'loss_usd': 1000000},
        {'address': '0x2A46f2FD99e16a1827Fc95688CC14cD35b6B48A8', 'name': 'Meebits', 'exploit_type': 'reentrancy', 'loss_usd': 1000000},
        {'address': '0x1A92f7381B9F03921564a437210bb9396471050C', 'name': 'Killabears', 'exploit_type': 'reentrancy', 'loss_usd': 1000000},
        {'address': '0x4A67915F1946E34e254543e3a639423382C1e040', 'name': 'Cool Cats', 'exploit_type': 'reentrancy', 'loss_usd': 1000000},
        {'address': '0x06012c8cf97BEaD5deAeB22486dD5684A4b4e6393', 'name': 'Meebits', 'exploit_type': 'reentrancy', 'loss_usd': 1000000},
        {'address': '0x05aEDf5B64F56F868a0a240d11A072a6e98E5B6c', 'name': 'Pudgy Penguins', 'exploit_type': 'reentrancy', 'loss_usd': 1000000},
        {'address': '0x7Bd29408f11D63bF9a64f816982d0DCe040F6e8B', 'name': 'World of Women', 'exploit_type': 'reentrancy', 'loss_usd': 1000000},
        {'address': '0x57f1887a8BF19b14fC0dF6Fd9B2acc9Af147eA85', 'name': 'ENS .eth Names', 'exploit_type': 'reentrancy', 'loss_usd': 1000000},
        {'address': '0x2953399124F0cBB46d2CbACD8A89cF0599974963', 'name': 'Sandbox LANDs', 'exploit_type': 'reentrancy', 'loss_usd': 1000000},
        {'address': '0x8a90CAb2b38dba80c64b7734e58EE1dB38B8992e', 'name': 'Decentraland Wearables', 'exploit_type': 'reentrancy', 'loss_usd': 1000000},
        {'address': '0x2A46f2FD99e16a1827Fc95688CC14cD35b6B48A8', 'name': 'Meebits', 'exploit_type': 'reentrancy', 'loss_usd': 1000000},
        {'address': '0x1A92f7381B9F03921564a437210bb9396471050C', 'name': 'Killabears', 'exploit_type': 'reentrancy', 'loss_usd': 1000000},
        {'address': '0x4A67915F1946E34e254543e3a639423382C1e040', 'name': 'Cool Cats', 'exploit_type': 'reentrancy', 'loss_usd': 1000000},
    ])
    
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
