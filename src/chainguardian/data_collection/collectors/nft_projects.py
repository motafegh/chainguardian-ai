"""
NFT Projects Collector
Collects major NFT project contracts
"""

from typing import List, Dict
from .base import BaseCollector


class NFTProjectsCollector(BaseCollector):
    """Collect NFT project contracts"""
    
    # Known major NFT projects
    NFT_PROJECTS = [
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
        {'address': '0x7Bd29408f11D63bF9a64f816982d0DCe040F6e8B', 'name': 'World of Women'},
        {'address': '0x4A67915F1946E34e254543e3a639423382C1e040', 'name': 'Cool Cats'},
        {'address': '0x76BE3b62873450d3820a7B53974f05DE7F7A8A6f', 'name': 'Sewer Pass'},
        {'address': '0x34d85c9CDeB99225bf155A1b1FE355c607b2aDE9', 'name': 'Moonbirds'},
        {'address': '0x49CF6f5dA46381bE5265D41AdD9d61E279542B72', 'name': 'Clonex'},
        {'address': '0x23581767a106ae21c074b2276D25e5C3E136a68b', 'name': 'Azuki'},
        {'address': '0xED5AF388653567Af2F388E6224dC7C4b3241C544', 'name': 'Bored Ape Kennel Club'},
        {'address': '0x86b735742d84591F22A9A3F6B9752b9b7c8a3F88', 'name': 'Pudgy Penguins'},
        {'address': '0x8a90CAb2b38dba80c64b7734e58EE1dB38B8992e', 'name': 'Doodles'},
        {'address': '0x1A92f7381B9F03921564a437210bb9396471050C', 'name': 'Killabears'},
    ]
    # Add more NFT projects to the NFT_PROJECTS list:

    NFT_PROJECTS.extend([
        # Add these to existing list
        {'address': '0x23581767a106ae21c074b2276D25e5C3E136a68b', 'name': 'Azuki', 'source': 'nft_projects'},
        {'address': '0x49CF6f5dA46381bE5265D41AdD9d61E279542B72', 'name': 'CloneX', 'source': 'nft_projects'},
        {'address': '0x34d85c9CDeB99225bf155A1b1FE355c607b2aDE9', 'name': 'Moonbirds', 'source': 'nft_projects'},
        {'address': '0x76BE3b62873450d3820a7B53974f05DE7F7A8A6f', 'name': 'Sewer Pass', 'source': 'nft_projects'},
        {'address': '0xED5AF388653567Af2F388E6224dC7C4b3241C544', 'name': 'Bored Ape Kennel Club', 'source': 'nft_projects'},
        {'address': '0x86b735742d84591F22A9A3F6B9752b9b7c8a3F88', 'name': 'Pudgy Penguins', 'source': 'nft_projects'},
        {'address': '0x8a90CAb2b38dba80c64b7734e58EE1dB38B8992e', 'name': 'Doodles', 'source': 'nft_projects'},
        {'address': '0x1A92f7381B9F03921564a437210bb9396471050C', 'name': 'Killabears', 'source': 'nft_projects'},
        {'address': '0x4A67915F1946E34e254543e3a639423382C1e040', 'name': 'Cool Cats', 'source': 'nft_projects'},
        {'address': '0x06012c8cf97BEaD5deAeB22486dD5684A4b4e6393', 'name': 'Meebits', 'source': 'nft_projects'},
        {'address': '0x05aEDf5B64F56F868a0a240d11A072a6e98E5B6c', 'name': 'Pudgy Penguins', 'source': 'nft_projects'},
        {'address': '0x7Bd29408f11D63bF9a64f816982d0DCe040F6e8B', 'name': 'World of Women', 'source': 'nft_projects'},
        {'address': '0x57f1887a8BF19b14fC0dF6Fd9B2acc9Af147eA85', 'name': 'ENS .eth Names', 'source': 'nft_projects'},
        {'address': '0x2953399124F0cBB46d2CbACD8A89cF0599974963', 'name': 'Sandbox LANDs', 'source': 'nft_projects'},
        {'address': '0x8a90CAb2b38dba80c64b7734e58EE1dB38B8992e', 'name': 'Decentraland Wearables', 'source': 'nft_projects'},
        {'address': '0x2A46f2FD99e16a1827Fc95688CC14cD35b6B48A8', 'name': 'Meebits', 'source': 'nft_projects'},
        {'address': '0x1A92f7381B9F03921564a437210bb9396471050C', 'name': 'Killabears', 'source': 'nft_projects'},
        {'address': '0x4A67915F1946E34e254543e3a639423382C1e040', 'name': 'Cool Cats', 'source': 'nft_projects'},
        {'address': '0x06012c8cf97BEaD5deAeB22486dD5684A4b4e6393', 'name': 'Meebits', 'source': 'nft_projects'},
        {'address': '0x05aEDf5B64F56F868a0a240d11A072a6e98E5B6c', 'name': 'Pudgy Penguins', 'source': 'nft_projects'},
        {'address': '0x7Bd29408f11D63bF9a64f816982d0DCe040F6e8B', 'name': 'World of Women', 'source': 'nft_projects'},
        {'address': '0x57f1887a8BF19b14fC0dF6Fd9B2acc9Af147eA85', 'name': 'ENS .eth Names', 'source': 'nft_projects'},
        {'address': '0x2953399124F0cBB46d2CbACD8A89cF0599974963', 'name': 'Sandbox LANDs', 'source': 'nft_projects'},
        {'address': '0x8a90CAb2b38dba80c64b7734e58EE1dB38B8992e', 'name': 'Decentraland Wearables', 'source': 'nft_projects'},
        {'address': '0x2A46f2FD99e16a1827Fc95688CC14cD35b6B48A8', 'name': 'Meebits', 'source': 'nft_projects'},
        {'address': '0x1A92f7381B9F03921564a437210bb9396471050C', 'name': 'Killabears', 'source': 'nft_projects'},
        {'address': '0x4A67915F1946E34e254543e3a639423382C1e040', 'name': 'Cool Cats', 'source': 'nft_projects'},
        {'address': '0x06012c8cf97BEaD5deAeB22486dD5684A4b4e6393', 'name': 'Meebits', 'source': 'nft_projects'},
        {'address': '0x05aEDf5B64F56F868a0a240d11A072a6e98E5B6c', 'name': 'Pudgy Penguins', 'source': 'nft_projects'},
        {'address': '0x7Bd29408f11D63bF9a64f816982d0DCe040F6e8B', 'name': 'World of Women', 'source': 'nft_projects'},
        {'address': '0x57f1887a8BF19b14fC0dF6Fd9B2acc9Af147eA85', 'name': 'ENS .eth Names', 'source': 'nft_projects'},
        {'address': '0x2953399124F0cBB46d2CbACD8A89cF0599974963', 'name': 'Sandbox LANDs', 'source': 'nft_projects'},
        {'address': '0x8a90CAb2b38dba80c64b7734e58EE1dB38B8992e', 'name': 'Decentraland Wearables', 'source': 'nft_projects'},
        {'address': '0x2A46f2FD99e16a1827Fc95688CC14cD35b6B48A8', 'name': 'Meebits', 'source': 'nft_projects'},
        {'address': '0x1A92f7381B9F03921564a437210bb9396471050C', 'name': 'Killabears', 'source': 'nft_projects'},
        {'address': '0x4A67915F1946E34e254543e3a639423382C1e040', 'name': 'Cool Cats', 'source': 'nft_projects'},
        {'address': '0x06012c8cf97BEaD5deAeB22486dD5684A4b4e6393', 'name': 'Meebits', 'source': 'nft_projects'},
        {'address': '0x05aEDf5B64F56F868a0a240d11A072a6e98E5B6c', 'name': 'Pudgy Penguins', 'source': 'nft_projects'},
        {'address': '0x7Bd29408f11D63bF9a64f816982d0DCe040F6e8B', 'name': 'World of Women', 'source': 'nft_projects'},
        {'address': '0x57f1887a8BF19b14fC0dF6Fd9B2acc9Af147eA85', 'name': 'ENS .eth Names', 'source': 'nft_projects'},
        {'address': '0x2953399124F0cBB46d2CbACD8A89cF0599974963', 'name': 'Sandbox LANDs', 'source': 'nft_projects'},
        {'address': '0x8a90CAb2b38dba80c64b7734e58EE1dB38B8992e', 'name': 'Decentraland Wearables', 'source': 'nft_projects'},
        {'address': '0x2A46f2FD99e16a1827Fc95688CC14cD35b6B48A8', 'name': 'Meebits', 'source': 'nft_projects'},
    ])
    
    def collect(self) -> List[Dict]:
        """Collect NFT project contracts"""
        
        self.log_collection_start(self.config.get('name', 'NFT Projects'))
        
        contracts = []
        
        for project in self.NFT_PROJECTS:
            if self.validate_address(project['address']):
                contracts.append({
                    'address': project['address'],
                    'name': project['name'],
                    'source': 'nft_projects',
                    'metadata': {
                        'type': 'nft',
                        'category': 'art'
                    }
                })
        
        self.log_collection_complete(len(contracts))
        return contracts