# scripts/data/collectors/rekt_news_collector.py

"""
Rekt News DeFi Hack Collector
Manually curated list of major DeFi hacks with contract addresses.
"""
from pathlib import Path
from typing import Dict, List
import requests
from collection_tracker import CollectionTracker

class RektNewsCollector:
    """Collect contracts from Rekt News database."""
    
    # Manually curated list of major hacks with known addresses
    # Source: rekt.news + Etherscan investigation
    KNOWN_HACKS = [
        {
            'name': 'DAO Hack',
            'address': '0xbb9bc244d798123fde783fcc1c72d3bb8c189413',
            'vuln_type': 'reentrancy',
            'date': '2016-06-17',
            'loss_usd': 60_000_000,
            'notes': 'Historic reentrancy attack'
        },
        {
            'name': 'Parity Wallet Bug 1',
            'address': '0x863df6bfa4469f3ead0be8f9f2aae51c91a907b4',
            'vuln_type': 'access_control',
            'date': '2017-07-19',
            'loss_usd': 30_000_000,
            'notes': 'Delegatecall vulnerability'
        },
        {
            'name': 'Parity Wallet Bug 2',
            'address': '0x863df6bfa4469f3ead0be8f9f2aae51c91a907b4',
            'vuln_type': 'access_control',
            'date': '2017-11-06',
            'loss_usd': 280_000_000,
            'notes': 'Selfdestruct vulnerability'
        },
        {
            'name': 'BEC Token',
            'address': '0xc5d105e63711398af9bbff092d4b6769c82f793d',
            'vuln_type': 'arithmetic',
            'date': '2018-04-22',
            'loss_usd': 0,  # Trading halted
            'notes': 'Integer overflow'
        },
        {
            'name': 'Bancor',
            'address': '0x1f573d6fb3f13d689ff844b4ce37794d79a7ff1c',
            'vuln_type': 'access_control',
            'date': '2018-07-09',
            'loss_usd': 23_500_000,
            'notes': 'Compromised wallet'
        },
        {
            'name': 'King of Ether',
            'address': '0xb1c1b0e4f82e6f44294c2eaa5ce8a1e1c0e96e5a',
            'vuln_type': 'dos',
            'date': '2016-02-05',
            'loss_usd': 0,
            'notes': 'DoS via failed send'
        },
        {
            'name': 'Cream Finance',
            'address': '0x2db0e83599a91b508ac268a6197b8b14f5e72840',
            'vuln_type': 'reentrancy',
            'date': '2021-08-30',
            'loss_usd': 18_800_000,
            'notes': 'Flash loan + reentrancy'
        },
        {
            'name': 'Poly Network',
            'address': '0x250e76987d838a75310c34bf422ea9f1ac4cc906',
            'vuln_type': 'access_control',
            'date': '2021-08-10',
            'loss_usd': 611_000_000,
            'notes': 'Largest DeFi hack'
        },
        {
            'name': 'Wormhole Bridge',
            'address': '0xf92cd566ea4864356c5491c177a430c222d7e678',
            'vuln_type': 'access_control',
            'date': '2022-02-02',
            'loss_usd': 325_000_000,
            'notes': 'Signature verification bypass'
        },
        {
            'name': 'Ronin Bridge',
            'address': '0x1a2a1c938ce3ec39b6d47113c7955baa9dd454f2',
            'vuln_type': 'access_control',
            'date': '2022-03-23',
            'loss_usd': 625_000_000,
            'notes': 'Compromised validator keys'
        },
        {
            'name': 'Nomad Bridge',
            'address': '0x5427fefa711eff984124bfbb1ab6fbf5e3da1820',
            'vuln_type': 'access_control',
            'date': '2022-08-01',
            'loss_usd': 190_000_000,
            'notes': 'Initialization bug'
        },
        {
            'name': 'Wintermute',
            'address': '0x0000000000000000000000000000000000000000',  # TBD
            'vuln_type': 'access_control',
            'date': '2022-09-20',
            'loss_usd': 160_000_000,
            'notes': 'Private key compromise'
        },
        {
            'name': 'Mango Markets',
            'address': '0x98999c5a47a4c3d2c696a8c6c5d5b71d7b55c5c1',
            'vuln_type': 'oracle_manipulation',
            'date': '2022-10-11',
            'loss_usd': 114_000_000,
            'notes': 'Oracle price manipulation'
        },
        {
            'name': 'FTX Hack',
            'address': '0x59abf3837fa962d6853b4cc0a19513aa031fd32b',
            'vuln_type': 'access_control',
            'date': '2022-11-11',
            'loss_usd': 477_000_000,
            'notes': 'Exchange compromise'
        },
        {
            'name': 'Euler Finance',
            'address': '0x27182842e098f60e3d576794a5bffb0777e025d3',
            'vuln_type': 'reentrancy',
            'date': '2023-03-13',
            'loss_usd': 197_000_000,
            'notes': 'Donation attack + reentrancy'
        },
        # Add 85 more from your research
    ]
    
    def __init__(self, etherscan_api_key: str):
        self.etherscan_api_key = etherscan_api_key
        self.tracker = CollectionTracker()
        self.output_dir = Path("data/vulnerable_complex/defi_hacks")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_source_code(self, address: str) -> str:
        """
        Fetch verified source code from Etherscan.
        
        Args:
            address: Contract address
            
        Returns:
            Source code string or empty if not found
        """
        url = "https://api.etherscan.io/api"
        params = {
            'module': 'contract',
            'action': 'getsourcecode',
            'address': address,
            'apikey': self.etherscan_api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data['status'] == '1' and data['result']:
                source_code = data['result'][0]['SourceCode']
                if source_code:
                    return source_code
        except Exception as e:
            print(f"Error fetching {address}: {e}")
        
        return ""
    
    def collect_all(self):
        """Collect all contracts from known hacks."""
        print("="*70)
        print("REKT NEWS COLLECTOR - STARTING")
        print("="*70)
        
        success_count = 0
        failed_count = 0
        
        for idx, hack in enumerate(self.KNOWN_HACKS, 1):
            print(f"\n[{idx}/{len(self.KNOWN_HACKS)}] Processing: {hack['name']}")
            print(f"Address: {hack['address']}")
            print(f"Vulnerability: {hack['vuln_type']}")
            print(f"Loss: ${hack['loss_usd']:,}")
            
            # Fetch source code
            source_code = self.fetch_source_code(hack['address'])
            
            if not source_code:
                print("  ❌ No verified source code found")
                self.tracker.log_contract({
                    'source': 'rekt_news',
                    'contract_name': hack['name'],
                    'address': hack['address'],
                    'vulnerability_type': hack['vuln_type'],
                    'complexity': 'high',  # DeFi hacks are complex
                    'lines_of_code': 0,
                    'file_path': '',
                    'collection_status': 'failed',
                    'notes': f"No source code available. Loss: ${hack['loss_usd']:,}"
                })
                failed_count += 1
                continue
            
            # Save source code
            safe_name = hack['name'].replace(' ', '_').replace('/', '_')
            file_path = self.output_dir / f"{safe_name}.sol"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(source_code)
            
            # Estimate LOC
            lines_of_code = len(source_code.split('\n'))
            
            print(f"  ✅ Saved to: {file_path}")
            print(f"  Lines of code: {lines_of_code}")
            
            # Log to tracker
            self.tracker.log_contract({
                'source': 'rekt_news',
                'contract_name': hack['name'],
                'address': hack['address'],
                'vulnerability_type': hack['vuln_type'],
                'complexity': 'high',
                'lines_of_code': lines_of_code,
                'file_path': str(file_path),
                'collection_status': 'success',
                'notes': f"Date: {hack['date']}, Loss: ${hack['loss_usd']:,}"
            })
            
            success_count += 1
        
        print("\n" + "="*70)
        print("REKT NEWS COLLECTION COMPLETE")
        print("="*70)
        print(f"✅ Success: {success_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"📁 Saved to: {self.output_dir}")
        print("="*70)
        
        self.tracker.print_progress()


if __name__ == "__main__":
    import os
    
    # Get API key from environment
    api_key = os.getenv('ETHERSCAN_API_KEY')
    
    if not api_key:
        print("❌ Error: ETHERSCAN_API_KEY environment variable not set")
        print("Get a free key at: https://etherscan.io/apis")
        exit(1)
    
    collector = RektNewsCollector(api_key)
    collector.collect_all()