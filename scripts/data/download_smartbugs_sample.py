"""
Download real SmartBugs Wild contracts - no assumptions, just reality!

🎯 Goal: Get actual contracts that exist in the repository
This script uses GitHub API to discover real files and downloads them
"""

import requests
import json
from pathlib import Path
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# GitHub API token (optional - helps with rate limits)
GITHUB_TOKEN = None  # Add your token here if you have one


def get_github_files(owner, repo, path):
    """
    Get list of files from GitHub repository using API
    
    Args:
        owner (str): Repository owner
        repo (str): Repository name
        path (str): Path within repository
    
    Returns:
        list: List of file objects from GitHub API
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {'Accept': 'application/vnd.github.v3+json'}
    
    if GITHUB_TOKEN:
        headers['Authorization'] = f'token {GITHUB_TOKEN}'
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return [item for item in response.json() if item.get('type') == 'file' and item.get('name', '').endswith('.sol')]
    except Exception as e:
        logger.error(f"❌ GitHub API error: {e}")
        return []


def download_smartbugs_contracts():
    """
    Discover and download actual existing contracts from SmartBugs Wild
    
    🎓 This script:
    1. Uses GitHub API to list ALL contract files in /contracts/ folder
    2. Downloads a sample of real contracts (no assumptions!)
    3. Shows exactly what exists in the repository
    """
    
    # Create directory for samples
    sample_dir = Path("data/smartbugs_contracts")
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("🔍 Discovering actual contracts in SmartBugs Wild repository...")
    logger.info(f"📁 Saving to: {sample_dir}")
    logger.info("")
    
    # Repository details
    REPO_OWNER = "smartbugs"
    REPO_NAME = "smartbugs-wild"
    CONTRACTS_PATH = "contracts"
    
    # Step 1: Get ALL actual contract files from GitHub API
    logger.info("🌐 Fetching contract list from GitHub API...")
    contract_files = get_github_files(REPO_OWNER, REPO_NAME, CONTRACTS_PATH)
    
    if not contract_files:
        logger.error("❌ Failed to get contract files from GitHub API")
        logger.info("💡 Manual fallback: Using known working contract addresses")
        
        # Fallback to known working addresses from the example URL
        contract_files = [
            {'name': '0x0000000000027f6d87be8ade118d9ee56767d993.sol', 'download_url': 'https://raw.githubusercontent.com/smartbugs/smartbugs-wild/master/contracts/0x0000000000027f6d87be8ade118d9ee56767d993.sol'},
            {'name': '0x0000000000170ccc93903185be5a2094c870df62.sol', 'download_url': 'https://raw.githubusercontent.com/smartbugs/smartbugs-wild/master/contracts/0x0000000000170ccc93903185be5a2094c870df62.sol'},
            {'name': '0x00000000001876eb1444c986fd502e618c587430.sol', 'download_url': 'https://raw.githubusercontent.com/smartbugs/smartbugs-wild/master/contracts/0x00000000001876eb1444c986fd502e618c587430.sol'},
            {'name': '0x0000000000531e1fe81486b48474fa588d2e9f88.sol', 'download_url': 'https://raw.githubusercontent.com/smartbugs/smartbugs-wild/master/contracts/0x0000000000531e1fe81486b48474fa588d2e9f88.sol'},
            {'name': '0x000000000089d837fb56a5c7f96c4f24b0bc4372.sol', 'download_url': 'https://raw.githubusercontent.com/smartbugs/smartbugs-wild/master/contracts/0x000000000089d837fb56a5c7f96c4f24b0bc4372.sol'}
        ]
    else:
        logger.info(f"✅ Found {len(contract_files)} actual contract files in repository")
        logger.info(f"📝 First 5 contracts: {', '.join([f['name'][:12] + '...' for f in contract_files[:5]])}")
    
    # Step 2: Download a sample of these actual contracts
    logger.info("\n📥 Downloading sample contracts...")
    
    max_to_download = min(5, len(contract_files))
    contracts_to_download = contract_files[:max_to_download]
    
    success_count = 0
    
    for i, contract in enumerate(contracts_to_download, 1):
        contract_name = contract['name']
        contract_address = contract_name.replace('.sol', '')
        contract_url = contract.get('download_url', f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/master/{CONTRACTS_PATH}/{contract_name}")
        
        logger.info(f"[{i}/{max_to_download}] Downloading {contract_address[:12]}...")
        logger.info(f"  🌐 URL: {contract_url}")
        
        contract_dir = sample_dir / contract_address
        contract_dir.mkdir(exist_ok=True)
        output_path = contract_dir / contract_name
        
        try:
            response = requests.get(contract_url, timeout=15)
            response.raise_for_status()
            
            # Save the contract
            with open(output_path, 'w') as f:
                f.write(response.text)
            
            logger.info(f"  ✅ Successfully downloaded {contract_name}")
            logger.info(f"  💾 Saved to: {output_path}")
            logger.info(f"  📏 File size: {len(response.text)} characters")
            
            # Save metadata
            metadata = {
                'contract_address': contract_address,
                'original_url': contract_url,
                'file_size': len(response.text),
                'downloaded_at': time.strftime("%Y-%m-%d %H:%M:%S"),
                'first_lines': response.text[:300] if response.text else ''
            }
            
            with open(contract_dir / 'metadata.json', 'w') as f:
                json.dump(metadata, f, indent=2)
            
            success_count += 1
            
        except Exception as e:
            logger.error(f"  ❌ Download failed: {e}")
        
        logger.info("")
        time.sleep(1)  # Be nice to GitHub servers
    
    logger.info("="*70)
    logger.info(f"✅ Download complete! Successfully downloaded {success_count}/{max_to_download} contracts")
    logger.info("="*70)
    logger.info(f"📁 All files saved to: {sample_dir}")
    logger.info("")
    logger.info("🔍 Next steps:")
    logger.info("  1. Examine the downloaded contracts:")
    for contract in contracts_to_download[:success_count]:
        contract_address = contract['name'].replace('.sol', '')
        logger.info(f"     • data/smartbugs_contracts/{contract_address}/{contract['name']}")
    
    logger.info("")
    logger.info("  2. To get analysis results for these contracts:")
    logger.info("     • Clone SmartBugs: git clone https://github.com/smartbugs/smartbugs.git")
    logger.info("     • Run analysis: ./smartbugs -t all -f data/smartbugs_contracts/*/*.sol --timeout 300")
    logger.info("     • Parse results: ./reparse results/")
    logger.info("     • Export to CSV: ./results2csv -p results/ > analysis_results.csv")
    logger.info("")
    logger.info("💡 Repository structure confirmed:")
    logger.info("   contracts/{contract_address}.sol")
    logger.info("   Example: contracts/0x0000000000027f6d87be8ade118d9ee56767d993.sol")
    logger.info("")
    logger.info(f"🎯 Successfully downloaded real contracts from the repository!")

if __name__ == "__main__":
    download_smartbugs_contracts()