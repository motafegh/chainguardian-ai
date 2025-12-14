"""
Etherscan Smart Contract Scraper
Production-grade API client with parallel processing
FIXED: Robust multi-file contract JSON extraction
"""

import os
import time
import json
import logging
from typing import Optional, Dict, List
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import requests
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EtherscanScraper:
    """
    Fetches verified smart contracts from Etherscan API.
    
    Features:
    - Parallel processing (5 threads by default)
    - Thread-safe rate limiting
    - Rate limiting: 4.76 calls/sec (5% buffer below 5 calls/sec limit)
    - Exponential backoff retry (1s, 2s, 4s)
    - Multi-file contract support (ALL JSON formats)
    - Vyper contract filtering
    - Progress tracking with tqdm
    - Graceful failure handling
    """
    
    BASE_URL = "https://api.etherscan.io/v2/api"
    RATE_LIMIT_DELAY = 0.21  # 4.76 calls/sec with safety buffer
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Etherscan client.
        
        Args:
            api_key: Etherscan API key (defaults to ETHERSCAN_API_KEY env var)
        
        Raises:
            ValueError: If no API key provided
        """
        self.api_key = api_key or os.getenv("ETHERSCAN_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Etherscan API key required. Either:\n"
                "1. Set ETHERSCAN_API_KEY in .env file, or\n"
                "2. Pass api_key parameter: EtherscanScraper(api_key='your_key')"
            )
        
        self._last_request_time = 0.0
        self._rate_limit_lock = Lock()  # Thread-safe rate limiting
        logger.info("EtherscanScraper initialized")
    
    def _make_request(
        self,
        params: Dict[str, str],
        max_retries: int = 3
    ) -> Dict:
        """
        Make thread-safe rate-limited API request with exponential backoff retry.
        
        Args:
            params: API query parameters
            max_retries: Maximum retry attempts
        
        Returns:
            Parsed JSON response
        
        Raises:
            requests.RequestException: If all retries fail
        """
        # Thread-safe rate limiting
        with self._rate_limit_lock:
            time_since_last = time.time() - self._last_request_time
            if time_since_last < self.RATE_LIMIT_DELAY:
                time.sleep(self.RATE_LIMIT_DELAY - time_since_last)
            
            self._last_request_time = time.time()
        
        params["apikey"] = self.api_key
        params["chainid"] = "1"
        
        # Retry loop with exponential backoff
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    self.BASE_URL,
                    params=params,
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                
                # Etherscan returns HTTP 200 even for errors
                if data.get("status") == "0":
                    if data.get("message") != "No transactions found":
                        logger.warning(f"API error: {data.get('result')}")
                
                return data
                
            except requests.RequestException as e:
                wait_time = 2 ** attempt
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{max_retries}): {e}. "
                    f"Retrying in {wait_time}s..."
                )
                
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {max_retries} retries exhausted")
                    raise
    
    def fetch_contract_source(self, address: str) -> Optional[Dict]:
        """
        Fetch verified contract source code.
        
        Args:
            address: Ethereum contract address (0x... format)
        
        Returns:
            Contract data dict with SourceCode, ContractName, CompilerVersion, etc.
            None if contract not verified or fetch failed
        """
        params = {
            "module": "contract",
            "action": "getsourcecode",
            "address": address
        }
        
        try:
            data = self._make_request(params)
            
            if data.get("status") != "1":
                logger.error(
                    f"Failed to fetch {address}: {data.get('message', 'Unknown error')}"
                )
                return None
            
            result = data["result"][0]
            
            if not result.get("SourceCode"):
                logger.warning(f"Contract {address} not verified")
                return None
            
            contract_name = result.get("ContractName", "Unknown")
            logger.debug(f"✓ Fetched {contract_name} at {address[:10]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"Exception fetching {address}: {e}")
            return None
    
    def save_contract(
        self,
        address: str,
        contract_data: Dict,
        output_dir: Path = Path("blockchain/contracts/collected")
    ) -> Optional[Path]:
        """
        Save contract source code to .sol file(s).
        
        For multi-file contracts, saves ALL files to a subdirectory.
        For single-file contracts, saves to a single .sol file.
        
        Args:
            address: Contract address (for filename uniqueness)
            contract_data: Data from fetch_contract_source()
            output_dir: Directory to save contracts
        
        Returns:
            Path to main contract file, or None if failed
        """
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            
            contract_name = contract_data.get("ContractName", address[:10])
            source_code = contract_data["SourceCode"]
            
            # ================================================================
            # FILTER: Skip Vyper contracts
            # ================================================================
            if source_code.strip().startswith('@version') or 'vyper' in source_code.lower()[:200]:
                logger.warning(f"Skipping Vyper contract: {contract_name}")
                return None
            
            # ================================================================
            # DETECT: Multi-file vs single-file contract
            # ================================================================
            is_multi_file = False
            sources = {}
            
            if source_code.startswith("{{") or source_code.startswith("{"):
                try:
                    # Parse JSON
                    if source_code.startswith("{{"):
                        json_str = source_code[1:-1]
                    else:
                        json_str = source_code
                    
                    json_data = json.loads(json_str)
                    
                    # Extract sources from various formats
                    if "sources" in json_data:
                        sources = json_data["sources"]
                    elif any(key.endswith('.sol') for key in json_data.keys()):
                        sources = json_data
                    
                    if sources and len(sources) > 0:
                        is_multi_file = True
                        logger.debug(f"{contract_name}: Multi-file contract ({len(sources)} files)")
                        
                except json.JSONDecodeError:
                    # Not JSON, treat as single file
                    pass
            
            # ================================================================
            # SAVE: Multi-file contract (create directory)
            # ================================================================
            if is_multi_file:
                # Create subdirectory for this contract
                contract_dir = output_dir / f"{contract_name}_{address[:10]}"
                contract_dir.mkdir(parents=True, exist_ok=True)
                
                main_file = None
                saved_count = 0
                
                # Save all source files
                for filename, file_data in sources.items():
                    try:
                        # Extract content from various structures
                        if isinstance(file_data, dict):
                            content = file_data.get("content", file_data.get("Content", ""))
                        else:
                            content = file_data
                        
                        if not content or not content.strip():
                            logger.warning(f"Empty content for {filename} in {contract_name}")
                            continue
                        
                        # Clean filename (remove paths like "contracts/")
                        clean_filename = filename.split('/')[-1]
                        if not clean_filename.endswith('.sol'):
                            clean_filename += '.sol'
                        
                        file_path = contract_dir / clean_filename
                        file_path.write_text(content, encoding="utf-8")
                        saved_count += 1
                        
                        # First file is main contract
                        if main_file is None:
                            main_file = file_path
                        
                        # Or use file matching contract name
                        if contract_name in clean_filename:
                            main_file = file_path
                            
                    except Exception as e:
                        logger.warning(f"Failed to save {filename} for {contract_name}: {e}")
                
                if main_file and saved_count > 0:
                    logger.debug(f"✓ Saved {contract_name}: {saved_count} files to {contract_dir.name}/")
                    return main_file
                else:
                    logger.error(f"Failed to save any files for {contract_name}")
                    return None
            
            # ================================================================
            # SAVE: Single-file contract
            # ================================================================
            else:
                # Validate single-file Solidity code
                if not source_code or not source_code.strip():
                    logger.error(f"{contract_name}: Empty source code")
                    return None
                
                if "pragma solidity" not in source_code.lower() and "contract " not in source_code.lower():
                    logger.warning(f"{contract_name}: Invalid Solidity code")
                    return None
                
                filename = f"{contract_name}_{address[:10]}.sol"
                filepath = output_dir / filename
                filepath.write_text(source_code, encoding="utf-8")
                logger.debug(f"✓ Saved {filename}")
                
                return filepath
                
        except Exception as e:
            logger.error(f"Failed to save {address}: {e}")
            return None

    
    def scrape_batch(
        self,
        addresses: List[str],
        output_dir: Path = Path("blockchain/contracts/collected"),
        save_every: int = 25,
        max_workers: int = 5
    ) -> List[Path]:
        """
        Scrape multiple contracts with parallel processing.
        
        Args:
            addresses: List of contract addresses
            output_dir: Where to save .sol files
            save_every: Checkpoint logging frequency
            max_workers: Number of parallel threads (default 5)
        
        Returns:
            List of successfully saved file paths
        """
        logger.info(f"")
        logger.info(f"{'='*70}")
        logger.info(f"Starting parallel batch scrape: {len(addresses)} contracts")
        logger.info(f"Using {max_workers} parallel workers")
        
        # Estimated time with parallelization
        estimated_time = len(addresses) * self.RATE_LIMIT_DELAY / max_workers
        logger.info(f"Estimated scraping time: ~{estimated_time:.0f}s")
        logger.info(f"{'='*70}")
        logger.info(f"")
        
        saved_files = []
        failed_addresses = []
        completed = 0
        
        def fetch_and_save(address):
            """Fetch and save one contract (runs in thread pool)"""
            try:
                # Fetch source code
                contract_data = self.fetch_contract_source(address)
                if contract_data is None:
                    return None, address
                
                # Save to file
                filepath = self.save_contract(address, contract_data, output_dir)
                if filepath:
                    return filepath, None
                else:
                    return None, address
                    
            except Exception as e:
                logger.error(f"Unexpected error for {address}: {e}")
                return None, address
        
        # Thread pool with progress bar
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            futures = {
                executor.submit(fetch_and_save, address): address
                for address in addresses
            }
            
            # Process results with tqdm progress bar
            with tqdm(total=len(addresses), desc="Scraping contracts", ncols=100) as pbar:
                for future in as_completed(futures):
                    completed += 1
                    pbar.update(1)
                    
                    filepath, failed_addr = future.result()
                    
                    if filepath:
                        saved_files.append(filepath)
                    elif failed_addr:
                        failed_addresses.append(failed_addr)
                    
                    # Checkpoint logging
                    if completed % save_every == 0:
                        logger.info(
                            f"   Checkpoint [{completed}/{len(addresses)}]: "
                            f"{len(saved_files)} saved, {len(failed_addresses)} failed"
                        )
        
        # Final summary
        logger.info(f"")
        logger.info(f"{'='*70}")
        
        success_count = len(saved_files)
        total_count = len(addresses)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        logger.info(
            f"✓ Scraping complete: {success_count}/{total_count} contracts saved "
            f"({success_rate:.1f}% success rate)"
        )
        
        if failed_addresses:
            preview = failed_addresses[:5]
            more = len(failed_addresses) - 5
            logger.warning(
                f"Failed addresses (showing first 5): {preview}"
                f"{f' ... and {more} more' if more > 0 else ''}"
            )
        
        logger.info(f"Files saved to: {output_dir}")
        logger.info(f"{'='*70}")
        logger.info(f"")
        
        return saved_files


if __name__ == "__main__":
    """Test scraper with known verified contracts"""
    
    scraper = EtherscanScraper()
    
    test_addresses = [
        "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC (multi-file)
        "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",  # UNI
        "0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAI
        "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",  # WBTC
    ]
    
    print(f"\n{'='*70}")
    print(f"Testing Parallel EtherscanScraper with {len(test_addresses)} contracts")
    print(f"{'='*70}\n")
    
    saved = scraper.scrape_batch(
        test_addresses,
        output_dir=Path("blockchain/contracts/test_collection"),
        save_every=2,
        max_workers=3  # Test with 3 workers
    )
    
    print(f"\n{'='*70}")
    print(f"Test complete: {len(saved)}/{len(test_addresses)} contracts saved")
    print(f"Check files at: blockchain/contracts/test_collection/")
    print(f"{'='*70}\n")
