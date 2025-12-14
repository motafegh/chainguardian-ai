# src/chainguardian/data_collection/etherscan_scraper.py

"""
Enhanced Etherscan Scraper with Async Support and Advanced Caching
"""

import os
import time
import json
import logging
import asyncio
import aiohttp
import hashlib
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import concurrent.futures
from threading import Lock
import requests
from dotenv import load_dotenv
from tqdm import tqdm
import pickle

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EtherscanScraper:
    """
    Production-grade Etherscan API client with parallel and async processing capabilities.
    """
    
    BASE_URL = "https://api.etherscan.io/v2/api"
    RATE_LIMIT_DELAY = 0.21  # seconds between requests
    
    def __init__(self, api_key: Optional[str] = None, max_workers: int = 5, cache_dir: Path = Path("cache")):
        """
        Initialize scraper with parallel processing and caching support.
        
        Args:
            api_key: Etherscan API key
            max_workers: Maximum number of concurrent requests
            cache_dir: Directory to cache contract data
        """
        self.api_key = api_key or os.getenv("ETHERSCAN_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Etherscan API key required. Either:\n"
                "1. Set ETHERSCAN_API_KEY in .env file, or\n"
                "2. Pass api_key parameter: EtherscanScraper(api_key='your_key')"
            )
        
        self.max_workers = max_workers
        self._last_request_time = 0.0
        self._lock = Lock()  # Thread-safe access to _last_request_time
        
        # Initialize cache
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "etherscan_cache.pkl"
        
        # Load existing cache if available
        self.contract_cache = {}
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'rb') as f:
                    self.contract_cache = pickle.load(f)
                logger.info(f"Loaded {len(self.contract_cache)} contracts from cache")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
        
        # Create session for connection pooling
        self.session = requests.Session()
        
        logger.info(f"EtherscanScraper initialized with {max_workers} workers")
    
    def _get_cache_key(self, address: str) -> str:
        """Generate cache key for contract address"""
        return f"contract_{address.lower()}"
    
    def _save_cache(self):
        """Save contract cache to disk"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.contract_cache, f)
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _make_request(self, params: Dict[str, str], max_retries: int = 3) -> Dict:
        """
        Make rate-limited API request with retry logic.
        Thread-safe implementation for concurrent access.
        """
        with self._lock:
            # Check time since last request (thread-safe)
            time_since_last = time.time() - self._last_request_time
            
            if time_since_last < self.RATE_LIMIT_DELAY:
                sleep_time = self.RATE_LIMIT_DELAY - time_since_last
                time.sleep(sleep_time)
            
            # Update timestamp (thread-safe)
            self._last_request_time = time.time()
        
        # Add API key to parameters
        params["apikey"] = self.api_key
        params["chainid"] = "1"
        
        # Retry logic
        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    self.BASE_URL, 
                    params=params, 
                    timeout=10
                )
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("status") == "0":
                    if data.get("message") != "No transactions found":
                        logger.warning(f"API returned error: {data.get('result')}")
                    return data
                
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
        Fetch verified contract source code for given address.
        Uses cache if available.
        """
        # Check cache first
        cache_key = self._get_cache_key(address)
        if cache_key in self.contract_cache:
            logger.debug(f"Using cached data for {address[:10]}...")
            return self.contract_cache[cache_key]
        
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
                logger.warning(f"Contract {address} not verified on Etherscan")
                return None
            
            contract_name = result.get("ContractName", "Unknown")
            logger.info(f"✓ Fetched {contract_name} at {address[:10]}...")
            
            # Cache the result
            self.contract_cache[cache_key] = result
            
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
        Save contract source code to .sol file.
        """
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            
            contract_name = contract_data.get("ContractName", address[:10])
            filename = f"{contract_name}_{address[:10]}.sol"
            filepath = output_dir / filename
            
            source_code = contract_data["SourceCode"]
            
            if source_code.startswith("{{"):
                logger.warning(
                    f"{contract_name} is multi-file contract. "
                    "Saving truncated version (full parsing not implemented yet)."
                )
                
                source_code = (
                    f"// Multi-file contract detected\n"
                    f"// Full JSON structure (truncated to 500 chars):\n"
                    f"{source_code[:500]}...\n\n"
                    f"// TODO: Implement full multi-file extraction"
                )
            
            filepath.write_text(source_code, encoding="utf-8")
            
            logger.info(f"✓ Saved {filename}")
            return filepath
        
        except Exception as e:
            logger.error(f"Failed to save {address}: {e}")
            return None
    
    def scrape_batch(
        self,
        addresses: List[str],
        output_dir: Path = Path("blockchain/contracts/collected"),
        save_every: int = 10
    ) -> List[Path]:
        """
        Scrape multiple contracts with parallel processing.
        """
        saved_files = []
        failed_addresses = []
        
        logger.info(f"Starting batch scrape: {len(addresses)} contracts")
        
        # Process contracts in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all fetch tasks
            future_to_address = {
                executor.submit(self.fetch_contract_source, address): address 
                for address in addresses
            }
            
            # Process completed tasks as they finish
            for future in tqdm(
                concurrent.futures.as_completed(future_to_address), 
                total=len(addresses),
                desc="Scraping contracts"
            ):
                address = future_to_address[future]
                
                try:
                    contract_data = future.result()
                    
                    if contract_data is None:
                        failed_addresses.append(address)
                        continue
                    
                    # Save contract
                    filepath = self.save_contract(address, contract_data, output_dir)
                    
                    if filepath:
                        saved_files.append(filepath)
                    else:
                        failed_addresses.append(address)
                    
                    # Checkpoint logging
                    if len(saved_files) % save_every == 0:
                        logger.info(
                            f"Checkpoint: {len(saved_files)} saved, "
                            f"{len(failed_addresses)} failed"
                        )
                        
                        # Save cache periodically
                        self._save_cache()
                
                except Exception as e:
                    logger.error(f"Unexpected error for {address}: {e}")
                    failed_addresses.append(address)
        
        # Save cache at the end
        self._save_cache()
        
        # Final summary
        success_count = len(saved_files)
        total_count = len(addresses)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        logger.info(
            f"Batch complete: {success_count}/{total_count} contracts saved "
            f"({success_rate:.1f}% success rate)"
        )
        
        if failed_addresses:
            preview = failed_addresses[:10]
            more = len(failed_addresses) - 10
            logger.warning(
                f"Failed addresses: {preview}"
                f"{f' ... and {more} more' if more > 0 else ''}"
            )
        
        return saved_files
    
    async def scrape_batch_async(
        self,
        addresses: List[str],
        output_dir: Path = Path("blockchain/contracts/collected"),
        save_every: int = 10
    ) -> List[Path]:
        """
        Asynchronous version of batch scraping for even better performance.
        """
        saved_files = []
        failed_addresses = []
        
        logger.info(f"Starting async batch scrape: {len(addresses)} contracts")
        
        # Create a semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def fetch_and_save(address):
            async with semaphore:
                # Check cache first
                cache_key = self._get_cache_key(address)
                if cache_key in self.contract_cache:
                    contract_data = self.contract_cache[cache_key]
                else:
                    # Fetch contract data
                    params = {
                        "module": "contract",
                        "action": "getsourcecode",
                        "address": address,
                        "apikey": self.api_key,
                        "chainid": "1"
                    }
                    
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(
                                self.BASE_URL, 
                                params=params, 
                                timeout=10
                            ) as response:
                                response.raise_for_status()
                                data = await response.json()
                                
                                if data.get("status") != "1":
                                    logger.error(
                                        f"Failed to fetch {address}: {data.get('message', 'Unknown error')}"
                                    )
                                    return None, address
                                
                                result = data["result"][0]
                                
                                if not result.get("SourceCode"):
                                    logger.warning(f"Contract {address} not verified on Etherscan")
                                    return None, address
                                
                                contract_data = result
                                
                                # Cache the result
                                self.contract_cache[cache_key] = contract_data
                    
                    except Exception as e:
                        logger.error(f"Exception fetching {address}: {e}")
                        return None, address
                
                # Save contract
                output_dir.mkdir(parents=True, exist_ok=True)
                
                contract_name = contract_data.get("ContractName", address[:10])
                filename = f"{contract_name}_{address[:10]}.sol"
                filepath = output_dir / filename
                
                source_code = contract_data["SourceCode"]
                
                if source_code.startswith("{{"):
                    logger.warning(
                        f"{contract_name} is multi-file contract. "
                        "Saving truncated version (full parsing not implemented yet)."
                    )
                    
                    source_code = (
                        f"// Multi-file contract detected\n"
                        f"// Full JSON structure (truncated to 500 chars):\n"
                        f"{source_code[:500]}...\n\n"
                        f"// TODO: Implement full multi-file extraction"
                    )
                
                filepath.write_text(source_code, encoding="utf-8")
                
                logger.info(f"✓ Saved {filename}")
                return filepath, address
        
        # Process all contracts concurrently
        tasks = [fetch_and_save(address) for address in addresses]
        
        # Process results as they complete
        for i, (filepath, address) in enumerate(
            tqdm(
                asyncio.as_completed(tasks), 
                total=len(addresses),
                desc="Scraping contracts (async)"
            )
        ):
            try:
                filepath, address = await i
                
                if filepath:
                    saved_files.append(filepath)
                else:
                    failed_addresses.append(address)
                
                # Checkpoint logging
                if len(saved_files) % save_every == 0:
                    logger.info(
                        f"Checkpoint: {len(saved_files)} saved, "
                        f"{len(failed_addresses)} failed"
                    )
                    
                    # Save cache periodically
                    self._save_cache()
            
            except Exception as e:
                logger.error(f"Unexpected error in async processing: {e}")
        
        # Save cache at the end
        self._save_cache()
        
        # Final summary
        success_count = len(saved_files)
        total_count = len(addresses)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        logger.info(
            f"Async batch complete: {success_count}/{total_count} contracts saved "
            f"({success_rate:.1f}% success rate)"
        )
        
        return saved_files