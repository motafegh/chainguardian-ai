import requests
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_github_tree():
    """Get the entire tree structure from OpenZeppelin GitHub."""
    api_url = "https://api.github.com/repos/OpenZeppelin/openzeppelin-contracts/git/trees/master?recursive=1"
    
    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        tree_data = response.json()
        
        # Filter for .sol files in contracts directory
        sol_files = [
            item['path'] for item in tree_data.get('tree', [])
            if item['path'].startswith('contracts/') and item['path'].endswith('.sol')
        ]
        
        # Remove 'contracts/' prefix
        return [path[10:] for path in sol_files]
    
    except Exception as e:
        logger.error(f"Failed to fetch GitHub tree: {e}")
        return []

def download_all_openzeppelin():
    """Download ALL OpenZeppelin contracts."""
    logger.info("Fetching OpenZeppelin contract list from GitHub...")
    all_contracts = get_github_tree()
    
    if not all_contracts:
        logger.error("No contracts found. Using fallback list.")
        all_contracts = OPENZEPPELIN_CONTRACTS + ADDITIONAL_PATHS
    
    logger.info(f"Found {len(all_contracts)} contracts to download")
    
    output_dir = Path("data/safe_contracts/openzeppelin_all")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    successful = 0
    base_url = "https://raw.githubusercontent.com/OpenZeppelin/openzeppelin-contracts/master/contracts"
    
    for i, contract_path in enumerate(all_contracts, 1):
        url = f"{base_url}/{contract_path}"
        output_file = output_dir / contract_path.replace("/", "_")
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                output_file.write_text(response.text, encoding='utf-8')
                successful += 1
                if i % 10 == 0:
                    logger.info(f"Downloaded {i}/{len(all_contracts)}...")
        except Exception as e:
            logger.error(f"Failed {contract_path}: {e}")
    
    logger.info(f"\n✅ Downloaded {successful}/{len(all_contracts)} contracts")
    logger.info(f"Output: {output_dir.absolute()}")

if __name__ == "__main__":
    download_all_openzeppelin()