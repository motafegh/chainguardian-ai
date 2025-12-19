"""
Etherscan Contract Fetcher - API V2
Updated for Etherscan API V2 (August 2025)
"""

import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()

class EtherscanFetcher:
    """Fetch contract source code from Etherscan API V2"""
    
    def __init__(self, api_key: Optional[str] = None, base_dir: str = '../data/real_world_collection', chainid: int = 1):
        """
        Initialize Etherscan fetcher (V2 API)
        
        Args:
            api_key: Etherscan API key
            base_dir: Base directory for saving contracts
            chainid: Chain ID (1=Ethereum, 137=Polygon, etc.)
        """
        self.api_key = api_key or os.getenv('ETHERSCAN_API_KEY', '')
        self.base_url = "https://api.etherscan.io/v2/api"  # V2 endpoint
        self.chainid = chainid
        self.rate_limit_delay = 0.21 if self.api_key else 1.5
        self.base_dir = Path(base_dir)
        
        self.stats = {
            'total_attempted': 0,
            'successful': 0,
            'failed': 0,
            'not_verified': 0,
            'errors': []
        }
        
        print(f"🔑 Etherscan Fetcher V2 initialized")
        print(f"   API Key: {'✅ Configured' if self.api_key else '❌ Not configured'}")
        print(f"   Chain ID: {chainid} (Ethereum Mainnet)")
        print(f"   Rate limit: {'5 req/sec' if self.api_key else '~1 req/sec'}")
    
    def get_contract_source(self, address: str) -> Optional[Dict]:
        """
        Fetch contract source code from Etherscan V2 API
        
        Args:
            address: Contract address
            
        Returns:
            Dictionary with contract data or None if failed
        """
        self.stats['total_attempted'] += 1
        
        # V2 API parameters
        params = {
            'chainid': self.chainid,  # Required for V2
            'module': 'contract',
            'action': 'getsourcecode',
            'address': address,
        }
        
        if self.api_key:
            params['apikey'] = self.api_key
        
        try:
            print(f"   📡 Fetching: {address[:10]}...", end=' ')
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == '1' and data['result']:
                result = data['result'][0]
                
                if result['SourceCode']:
                    print(f"✅ {result['ContractName']}")
                    self.stats['successful'] += 1
                    
                    return {
                        'address': address,
                        'name': result['ContractName'],
                        'source_code': result['SourceCode'],
                        'abi': result['ABI'],
                        'compiler_version': result['CompilerVersion'],
                        'optimization_used': result['OptimizationUsed'],
                        'runs': result['Runs'],
                        'constructor_arguments': result['ConstructorArguments'],
                        'evm_version': result['EVMVersion'],
                        'license_type': result['LicenseType'],
                        'proxy': result['Proxy'],
                        'implementation': result['Implementation'],
                    }
                else:
                    print(f"❌ Not verified")
                    self.stats['not_verified'] += 1
                    return None
            else:
                msg = data.get('message', 'Unknown error')
                result_msg = data.get('result', '')
                print(f"❌ {msg}")
                self.stats['failed'] += 1
                self.stats['errors'].append(f"{address}: {msg} - {result_msg}")
                return None
        
        except Exception as e:
            print(f"❌ Error: {e}")
            self.stats['failed'] += 1
            self.stats['errors'].append(f"{address}: {str(e)}")
            return None
        
        finally:
            time.sleep(self.rate_limit_delay)
    
    def save_contract(self, contract_data: Dict, category: str, metadata: Dict) -> Path:
        """Save contract source code and metadata"""
        
        name = contract_data['name'].replace(' ', '_').replace('/', '_')
        address = contract_data['address']
        filename = f"{name}_{address[:8]}.sol"
        
        file_path = self.base_dir / category / filename
        
        # Handle multi-file contracts
        source_code = contract_data['source_code']
        if source_code.startswith('{'):
            try:
                source_json = json.loads(source_code[1:-1])
                if 'sources' in source_json:
                    first_file = list(source_json['sources'].values())[0]
                    source_code = first_file.get('content', source_code)
            except:
                pass
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(source_code)
        
        # Save metadata
        metadata_enhanced = {
            **metadata,
            'contract_address': address,
            'contract_name': contract_data['name'],
            'compiler_version': contract_data['compiler_version'],
            'optimization': contract_data['optimization_used'],
            'optimization_runs': contract_data['runs'],
            'file_path': str(file_path),
            'collection_timestamp': datetime.now().isoformat(),
            'etherscan_url': f"https://etherscan.io/address/{address}#code"
        }
        
        metadata_path = self.base_dir / 'metadata' / f"{name}_{address[:8]}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata_enhanced, f, indent=2)
        
        # Save raw response
        raw_path = self.base_dir / 'raw_json' / f"{name}_{address[:8]}.json"
        with open(raw_path, 'w') as f:
            json.dump(contract_data, f, indent=2)
        
        print(f"      💾 Saved: {file_path.name}")
        return file_path
    
    def print_stats(self):
        """Print collection statistics"""
        print(f"\n{'='*70}")
        print("COLLECTION STATISTICS")
        print("="*70)
        print(f"   Total attempted: {self.stats['total_attempted']}")
        print(f"   Successful: {self.stats['successful']} ✅")
        print(f"   Not verified: {self.stats['not_verified']} ⚠️")
        print(f"   Failed: {self.stats['failed']} ❌")
        print(f"   Success rate: {self.stats['successful']/max(self.stats['total_attempted'],1)*100:.1f}%")
        
        if self.stats['errors']:
            print(f"\n⚠️  Errors ({len(self.stats['errors'])} total):")
            for err in self.stats['errors'][:5]:
                print(f"   • {err}")
            if len(self.stats['errors']) > 5:
                print(f"   ... and {len(self.stats['errors'])-5} more")

if __name__ == "__main__":
    # Test with V2 API
    fetcher = EtherscanFetcher()
    
    print("\n🧪 Testing Etherscan API V2 with USDC...")
    data = fetcher.get_contract_source('0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48')
    
    if data:
        print(f"\n✅ V2 API works!")
        print(f"   Name: {data['name']}")
        print(f"   Compiler: {data['compiler_version']}")
        print(f"   Source length: {len(data['source_code'])} chars")
    else:
        print(f"\n❌ Test failed")
    
    fetcher.print_stats()
