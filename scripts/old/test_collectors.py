# scripts/test_collectors.py

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'src'))

from chainguardian.data_collection.collectors.dex_pools import DEXPoolsCollector
from chainguardian.data_collection.collectors.nft_projects import NFTProjectsCollector
from chainguardian.data_collection.collectors.known_tokens import KnownTokensCollector

# Test Known Tokens collector
print("Testing Known Tokens collector...")
kt_config = {
    'name': 'Known Tokens',
    'criteria': [{'count': 100}]
}
kt_collector = KnownTokensCollector(kt_config)
kt_results = kt_collector.collect()
print(f"✓ Known Tokens: {len(kt_results)} contracts")
if kt_results:
    print(f"  Sample: {kt_results[0]['name']} - {kt_results[0]['address'][:10]}...")

# Test DEX pools
print("\nTesting DEX pools collector...")
dex_config = {
    'name': 'DEX Pools',
    'criteria': [{'min_liquidity': 50000}]
}
dex_collector = DEXPoolsCollector(dex_config)
dex_results = dex_collector.collect()
print(f"✓ DEX pools: {len(dex_results)} contracts")
if dex_results:
    print(f"  Sample: {dex_results[0]['name']} - {dex_results[0]['address'][:10]}...")

# Test NFT projects
print("\nTesting NFT projects collector...")
nft_config = {
    'name': 'NFT Projects',
    'criteria': [{'source': 'opensea_top'}]
}
nft_collector = NFTProjectsCollector(nft_config)
nft_results = nft_collector.collect()
print(f"✓ NFT projects: {len(nft_results)} contracts")
if nft_results:
    print(f"  Sample: {nft_results[0]['name']} - {nft_results[0]['address'][:10]}...")

# Summary
print("\n" + "="*50)
print("COLLECTION SUMMARY")
print("="*50)
print(f"Total potential contracts: {len(dex_results) + len(nft_results) + len(kt_results)}")
print(f"  - Known Tokens: {len(kt_results)}")
print(f"  - DEX pools: {len(dex_results)}")
print(f"  - NFT projects: {len(nft_results)}")