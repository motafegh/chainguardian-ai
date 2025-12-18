"""
Data Collection Infrastructure Setup
Creates directory structure and metadata templates
"""

import os
import json
from pathlib import Path
from datetime import datetime

def setup_infrastructure():
    """Create complete data collection infrastructure"""
    
    print("="*70)
    print("REAL-WORLD DATA COLLECTION - INFRASTRUCTURE SETUP")
    print("="*70)
    
    # Base directory
    base_dir = Path('../data/real_world_collection')
    
    # Create directories
    dirs = {
        'vulnerable_complex': base_dir / 'vulnerable_complex',
        'vulnerable_simple': base_dir / 'vulnerable_simple',
        'safe_complex': base_dir / 'safe_complex',
        'safe_simple': base_dir / 'safe_simple',
        'metadata': base_dir / 'metadata',
        'sources': base_dir / 'sources',
        'raw_json': base_dir / 'raw_json'
    }
    
    print("\n📁 Creating directories...")
    for name, path in dirs.items():
        path.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {name}")
    
    # Metadata template
    metadata_template = {
        "contract_address": "",
        "contract_name": "",
        "category": "",
        "vulnerability_type": "",
        "exploit_date": "",
        "lines_of_code": 0,
        "complexity_estimate": "",
        "source": "",
        "verification_status": "",
        "notes": "",
        "collection_date": datetime.now().isoformat(),
        "etherscan_url": "",
        "audit_report_url": "",
        "exploit_tx_hash": ""
    }
    
    with open(base_dir / 'metadata' / 'template.json', 'w') as f:
        json.dump(metadata_template, f, indent=2)
    
    print(f"\n✅ Metadata template created")
    
    # Target contracts list
    target_contracts = {
        "VULNERABLE_COMPLEX": [
            {
                "name": "TheDAO",
                "address": "0xbb9bc244d798123fde783fcc1c72d3bb8c189413",
                "vulnerability": "reentrancy",
                "year": 2016,
                "complexity": "complex",
                "impact": "$50M",
                "priority": "HIGH"
            },
            {
                "name": "Parity Wallet 1st",
                "address": "0x863df6bfa4469f3ead0be8f9f2aae51c91a907b4",
                "vulnerability": "delegatecall",
                "year": 2017,
                "complexity": "complex",
                "impact": "$30M",
                "priority": "HIGH"
            },
            {
                "name": "Parity Wallet 2nd",
                "address": "0x1dba1131000664b884a1ba238464159892252d3a",
                "vulnerability": "uninitialized",
                "year": 2017,
                "complexity": "complex",
                "impact": "$280M frozen",
                "priority": "HIGH"
            },
            {
                "name": "BEC Token",
                "address": "0xc5d105e63711398af9bbff092d4b6769c82f793d",
                "vulnerability": "integer_overflow",
                "year": 2018,
                "complexity": "medium",
                "impact": "Total supply manipulation",
                "priority": "HIGH"
            },
            {
                "name": "Poly Network",
                "address": "0x250e76987d838a75310c34bf422ea9f1ac4cc906",
                "vulnerability": "access_control",
                "year": 2021,
                "complexity": "complex",
                "impact": "$611M",
                "priority": "HIGH"
            },
            {
                "name": "Wormhole Bridge",
                "address": "0xf92cd566ea4864356c5491c177a430c222d7e678",
                "vulnerability": "signature_verification",
                "year": 2022,
                "complexity": "complex",
                "impact": "$325M",
                "priority": "HIGH"
            },
            {
                "name": "Nomad Bridge",
                "address": "0x5427fefa711eff984124bfbb1ab6fbf5e3da1820",
                "vulnerability": "initialization",
                "year": 2022,
                "complexity": "complex",
                "impact": "$190M",
                "priority": "HIGH"
            },
            {
                "name": "Euler Finance",
                "address": "0x27182842e098f60e3d576794a5bffb0777e025d3",
                "vulnerability": "donation_attack",
                "year": 2023,
                "complexity": "complex",
                "impact": "$197M",
                "priority": "MEDIUM"
            },
            {
                "name": "Cream Finance",
                "address": "0x44fbebd2f576670a6c33f6fc0b00aa8c5753b322",
                "vulnerability": "flash_loan_reentrancy",
                "year": 2021,
                "complexity": "complex",
                "impact": "$130M",
                "priority": "MEDIUM"
            },
            {
                "name": "Ronin Bridge",
                "address": "0x1a2a1c938ce3ec39b6d47113c7955baa9dd454f2",
                "vulnerability": "access_control",
                "year": 2022,
                "complexity": "complex",
                "impact": "$625M",
                "priority": "HIGH"
            }
        ],
        "SAFE_COMPLEX": [
            {
                "name": "USDC",
                "address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                "type": "stablecoin",
                "audits": ["Centre", "multiple"],
                "complexity": "complex",
                "priority": "HIGH"
            },
            {
                "name": "USDT",
                "address": "0xdac17f958d2ee523a2206206994597c13d831ec7",
                "type": "stablecoin",
                "audits": ["multiple"],
                "complexity": "complex",
                "priority": "HIGH"
            },
            {
                "name": "Uniswap V2 Router",
                "address": "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",
                "type": "dex",
                "audits": ["Trail of Bits", "Consensys"],
                "complexity": "complex",
                "priority": "HIGH"
            },
            {
                "name": "Uniswap V3 Router",
                "address": "0xe592427a0aece92de3edee1f18e0157c05861564",
                "type": "dex",
                "audits": ["multiple"],
                "complexity": "complex",
                "priority": "HIGH"
            },
            {
                "name": "Aave V2 LendingPool",
                "address": "0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9",
                "type": "lending",
                "audits": ["Consensys", "PeckShield", "Trail of Bits"],
                "complexity": "complex",
                "priority": "HIGH"
            }
        ]
    }
    
    with open(base_dir / 'sources' / 'target_contracts.json', 'w') as f:
        json.dump(target_contracts, f, indent=2)
    
    print(f"✅ Target contracts list created")
    
    print(f"\n{'='*70}")
    print("✅ Infrastructure setup complete!")
    print(f"{'='*70}")
    print(f"\n📁 Base directory: {base_dir}")
    print(f"   • vulnerable_complex/")
    print(f"   • vulnerable_simple/")
    print(f"   • safe_complex/")
    print(f"   • safe_simple/")
    print(f"   • metadata/")
    print(f"   • sources/")
    
    return base_dir

if __name__ == "__main__":
    setup_infrastructure()
