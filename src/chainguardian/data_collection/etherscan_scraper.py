# src/chainguardian/data_collection/etherscan_scraper.py

"""
Etherscan Smart Contract Scraper
=================================

Purpose: Fetch verified Solidity contracts from Etherscan API for ML training data.

Key Design Decisions:
1. Rate limiting: 4.76 calls/sec (5% buffer below 5 calls/sec limit)
2. Graceful failure: Return None instead of raising exceptions for missing contracts
3. Incremental progress: Save checkpoints every N contracts to prevent data loss
4. Production logging: All operations logged for debugging

Author: Ali - ChainGuardian AI Project
"""

# ============================================================================
# IMPORTS
# ============================================================================

import os                           # Access environment variables (.env)
import time                         # Sleep for rate limiting between requests
import json                         # JSON parsing (reserved for future metadata export)
import logging                      # Production-grade logging (better than print)
from typing import Optional, Dict, List  # Type hints for code clarity
from pathlib import Path            # Modern file path handling (cross-platform)

import requests                     # HTTP library for API calls
from dotenv import load_dotenv      # Load API keys from .env file
from tqdm import tqdm              # Progress bars for user feedback

# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================

# Load .env file from project root
# This reads ETHERSCAN_API_KEY=your_key_here into environment
load_dotenv()

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Configure logging format and level
# INFO level: Shows important events (API calls, saves, errors)
# DEBUG level would show every detail (too verbose for production)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    # Example output: 2025-12-11 17:57:30 - etherscan_scraper - INFO - Fetched Token
)
logger = logging.getLogger(__name__)  # Create logger for this module


# ============================================================================
# MAIN SCRAPER CLASS
# ============================================================================

class EtherscanScraper:
    """
    Production-grade Etherscan API client for smart contract collection.
    
    Architecture:
    -------------
    3-Layer design for separation of concerns:
    
    Layer 1 (Public API):
        - scrape_batch()          : Process multiple contracts
        - fetch_contract_source() : Get one contract's source code
        - save_contract()         : Save source code to .sol file
    
    Layer 2 (Private):
        - _make_request()         : Low-level API call with retry logic
    
    Layer 3 (Data):
        - Rate limit tracking (_last_request_time)
        - API credentials (api_key)
    
    Usage Example:
    --------------
    >>> scraper = EtherscanScraper()  # Loads key from .env
    >>> addresses = ["0x123...", "0x456..."]
    >>> files = scraper.scrape_batch(addresses)
    >>> print(f"Saved {len(files)} contracts")
    
    Rate Limiting:
    --------------
    Free tier: 5 calls/second, 100,000 calls/day
    Implementation: 0.21s delay = 4.76 calls/sec (5% safety buffer)
    Why buffer? Network jitter can cause requests to arrive early → 429 ban
    
    Error Handling:
    ---------------
    Philosophy: Fail gracefully, don't stop entire batch
    - Contract not verified → Log warning, return None, continue
    - API timeout → Retry with exponential backoff (1s, 2s, 4s)
    - Rate limit hit → Exponential backoff up to 3 attempts
    """
    
    # Class constants (shared across all instances)
    BASE_URL = "https://api.etherscan.io/v2/api"
    
    # CRITICAL: 0.21s = 4.76 calls/sec (NOT 0.20s = exactly 5 calls/sec)
    # Why? Network latency variance (10-50ms) can cause early arrivals → 429 errors
    # Production rule: Always add 5-20% safety buffer to API limits
    RATE_LIMIT_DELAY = 0.21  # seconds between requests
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Etherscan API client.
        
        Args:
            api_key (Optional[str]): Etherscan API key. If None, loads from 
                                     ETHERSCAN_API_KEY environment variable.
        
        Raises:
            ValueError: If no API key provided and not found in environment.
        
        Design Decision: Why Optional parameter?
        ----------------------------------------
        Flexibility for different use cases:
        1. Production: EtherscanScraper() → Reads from .env (secure)
        2. Testing: EtherscanScraper("test_key") → Direct injection
        3. CI/CD: EtherscanScraper(os.environ['CI_API_KEY']) → Different source
        """
        # Priority: Use passed key first, fallback to environment variable
        # The 'or' operator: If api_key is None/empty, evaluate right side
        self.api_key = api_key or os.getenv("ETHERSCAN_API_KEY")
        
        # Fail fast principle: Stop immediately if configuration is wrong
        # Better than crashing 50 API calls later with cryptic error
        if not self.api_key:
            raise ValueError(
                "Etherscan API key required. Either:\n"
                "1. Set ETHERSCAN_API_KEY in .env file, or\n"
                "2. Pass api_key parameter: EtherscanScraper(api_key='your_key')"
            )
        
        # Private variable (underscore prefix = internal use only)
        # Tracks timestamp of last API request for rate limiting
        # Initial value 0.0 = "no requests made yet"
        self._last_request_time = 0.0
        
        logger.info("EtherscanScraper initialized successfully")
    
    # ========================================================================
    # PRIVATE METHOD: LOW-LEVEL API REQUEST
    # ========================================================================
    
    def _make_request(
        self,
        params: Dict[str, str],
        max_retries: int = 3
    ) -> Dict:
        """
        Make rate-limited API request with exponential backoff retry.
        
        This is the ONLY method that actually calls Etherscan API.
        All other methods (fetch_contract_source, etc.) call this.
        
        Why centralize? DRY principle (Don't Repeat Yourself):
        - Rate limiting logic in one place
        - Retry logic in one place
        - Error handling in one place
        - Easy to modify (e.g., switch to paid tier: change RATE_LIMIT_DELAY)
        
        Args:
            params (Dict[str, str]): API query parameters
                Example: {"module": "contract", "action": "getsourcecode", "address": "0x123..."}
            max_retries (int): Maximum retry attempts on failure
        
        Returns:
            Dict: Parsed JSON response from Etherscan
                Success: {"status": "1", "result": [...]}
                Error: {"status": "0", "message": "...", "result": "..."}
        
        Raises:
            requests.RequestException: If all retries fail
        
        Rate Limiting Algorithm:
        ------------------------
        1. Check time since last request
        2. If < RATE_LIMIT_DELAY, sleep for remaining time
        3. Make request
        4. Update _last_request_time
        
        Example:
        --------
        Last request: 100.00s
        Current time: 100.15s
        Time elapsed: 0.15s
        Required delay: 0.21s
        Need to wait: 0.06s more
        """
        # ====================================================================
        # RATE LIMITING: Enforce minimum delay between requests
        # ====================================================================
        
        # Calculate elapsed time since last request
        time_since_last = time.time() - self._last_request_time
        
        # If requests are too close together, sleep for remaining time
        if time_since_last < self.RATE_LIMIT_DELAY:
            sleep_time = self.RATE_LIMIT_DELAY - time_since_last
            time.sleep(sleep_time)
        
        # Add API key to parameters (required for all Etherscan requests)
        params["apikey"] = self.api_key
        params["chainid"] = "1"
        
        # ====================================================================
        # RETRY LOOP: Exponential backoff for transient failures
        # ====================================================================
        
        # Why exponential backoff?
        # Linear backoff (1s, 1s, 1s): If server is overloaded, short waits don't help
        # Exponential (1s, 2s, 4s): Gives server time to recover
        
        for attempt in range(max_retries):  # attempt = 0, 1, 2
            try:
                # Update timestamp BEFORE request (prevents burst if request takes time)
                self._last_request_time = time.time()
                
                # Make HTTP GET request with 10 second timeout
                # Timeout prevents hanging forever on network issues
                response = requests.get(
                    self.BASE_URL, 
                    params=params, 
                    timeout=10
                )
                
                # Check HTTP status code (200 = success, 4xx = client error, 5xx = server error)
                # raise_for_status() raises exception for status >= 400
                # This triggers the except block below for retry logic
                response.raise_for_status()
                
                # Parse JSON response
                data = response.json()
                
                # ============================================================
                # ETHERSCAN-SPECIFIC ERROR HANDLING
                # ============================================================
                
                # Etherscan returns HTTP 200 even for errors!
                # Must check their custom "status" field
                # status "0" = error, status "1" = success
                
                if data.get("status") == "0":
                    # Some "errors" are expected (e.g., "No transactions found")
                    # Don't retry these - return to caller for handling
                    if data.get("message") != "No transactions found":
                        logger.warning(f"API returned error: {data.get('result')}")
                    
                    # Return error response (caller checks status field)
                    return data
                
                # Success! Return data
                return data
            
            except requests.RequestException as e:
                # ============================================================
                # RETRY LOGIC: Exponential backoff
                # ============================================================
                
                # Calculate wait time: 2^attempt seconds
                # Attempt 0: 2^0 = 1 second
                # Attempt 1: 2^1 = 2 seconds
                # Attempt 2: 2^2 = 4 seconds
                wait_time = 2 ** attempt
                
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{max_retries}): {e}. "
                    f"Retrying in {wait_time}s..."
                )
                
                # If not last attempt, wait and retry
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                else:
                    # Last attempt failed - re-raise exception
                    # Caller must handle this (usually log and skip contract)
                    logger.error(f"All {max_retries} retries exhausted")
                    raise
    
    # ========================================================================
    # PUBLIC METHOD 1: FETCH CONTRACT SOURCE CODE
    # ========================================================================
    
    def fetch_contract_source(self, address: str) -> Optional[Dict]:
        """
        Fetch verified contract source code for given address.
        
        This wraps _make_request() with contract-specific logic:
        - Validates response has source code
        - Returns None instead of raising (graceful failure)
        - Logs contract name for debugging
        
        Args:
            address (str): Ethereum contract address (0x... format, 42 chars)
        
        Returns:
            Optional[Dict]: Contract data if successful, None if failed
                Success dict contains:
                    - SourceCode: Full Solidity source code (can be multi-file JSON)
                    - ContractName: Main contract name (e.g., "ERC20Token")
                    - CompilerVersion: Solidity version (e.g., "v0.8.20+commit.a1b2c3d4")
                    - ABI: Contract ABI as JSON string
                    - OptimizationUsed: "0" or "1"
                    - Runs: Optimizer runs (e.g., "200")
                    ... plus other metadata fields
        
        None Cases (Expected, Not Errors):
        -----------------------------------
        1. Contract not verified on Etherscan
        2. Invalid address format
        3. Contract is proxy without implementation verified
        4. API temporarily unavailable (after retries)
        
        Design Decision: Why return None instead of raising exception?
        ---------------------------------------------------------------
        When scraping 100 contracts:
        - 10 not verified → Return None → Caller skips → 90 contracts collected ✅
        - 10 not verified → Raise exception → Script crashes → 0 contracts ❌
        
        Production philosophy: Maximize data collection, fail gracefully
        """
        # Construct API parameters for getsourcecode endpoint
        params = {
            "module": "contract",           # Etherscan module for contract operations
            "action": "getsourcecode",      # Action: fetch source code
            "address": address              # Target contract address
        }
        
        try:
            # Make API request (handles rate limiting + retries)
            data = self._make_request(params)
            
            # Check if API call succeeded
            # status "1" = success, status "0" = error
            if data.get("status") != "1":
                logger.error(
                    f"Failed to fetch {address}: {data.get('message', 'Unknown error')}"
                )
                return None
            
            # Extract result (API returns list with single element for getsourcecode)
            result = data["result"][0]
            
            # Validate source code exists
            # Empty SourceCode = contract not verified
            if not result.get("SourceCode"):
                logger.warning(f"Contract {address} not verified on Etherscan")
                return None
            
            # Success! Log for debugging/monitoring
            contract_name = result.get("ContractName", "Unknown")
            logger.info(f"✓ Fetched {contract_name} at {address[:10]}...")
            
            return result
        
        except Exception as e:
            # Catch any unexpected errors (shouldn't happen if _make_request works correctly)
            logger.error(f"Exception fetching {address}: {e}")
            return None
    
    # ========================================================================
    # PUBLIC METHOD 2: SAVE CONTRACT TO FILE
    # ========================================================================
    
    def save_contract(
        self, 
        address: str, 
        contract_data: Dict,
        output_dir: Path = Path("blockchain/contracts/collected")
    ) -> Optional[Path]:
        """
        Save contract source code to .sol file.
        
        File Naming Convention:
        -----------------------
        {ContractName}_{AddressPrefix}.sol
        Example: ERC20Token_0x1234567890.sol
        
        Why include address prefix?
        - Multiple contracts can have same name ("Token", "ERC20")
        - Address makes filename unique
        - 10 chars enough to identify (full address in file content)
        
        Multi-File Contracts:
        ---------------------
        Some contracts use imports (e.g., OpenZeppelin):
        
        Single file:
            pragma solidity ^0.8.0;
            contract Token { ... }
        
        Multi-file (Etherscan returns JSON):
            {{"contracts/Token.sol": {"content": "..."}, "contracts/Ownable.sol": {"content": "..."}}}
        
        Current handling: Detect with startswith("{{"), save truncated JSON
        Future improvement: Parse JSON and save all files in subdirectory
        
        Args:
            address (str): Contract address (for filename uniqueness)
            contract_data (Dict): Data from fetch_contract_source()
            output_dir (Path): Directory to save contracts (created if missing)
        
        Returns:
            Optional[Path]: Path to saved file if successful, None if failed
        
        Error Handling:
        ---------------
        - Directory creation failure → Return None
        - File write permission error → Return None
        - Disk full → Return None
        All errors logged for debugging
        """
        try:
            # ================================================================
            # DIRECTORY SETUP
            # ================================================================
            
            # Create output directory if it doesn't exist
            # parents=True: Create parent directories too (blockchain/, blockchain/contracts/, ...)
            # exist_ok=True: Don't error if directory already exists
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # ================================================================
            # FILENAME GENERATION
            # ================================================================
            
            # Get contract name from metadata (fallback to address prefix if missing)
            contract_name = contract_data.get("ContractName", address[:10])
            
            # Construct filename: ContractName_0x1234567890.sol
            # address[:10] = First 10 characters (includes 0x prefix)
            filename = f"{contract_name}_{address[:10]}.sol"
            
            # Join directory + filename using Path's / operator
            # Handles Windows (\) vs Linux (/) automatically
            filepath = output_dir / filename
            
            # ================================================================
            # SOURCE CODE EXTRACTION
            # ================================================================
            
            # Extract source code from API response
            source_code = contract_data["SourceCode"]
            
            # ================================================================
            # MULTI-FILE CONTRACT DETECTION
            # ================================================================
            
            # Check if source code is multi-file JSON format
            # Multi-file contracts start with double braces: {{...}}
            if source_code.startswith("{{"):
                logger.warning(
                    f"{contract_name} is multi-file contract. "
                    "Saving truncated version (full parsing not implemented yet)."
                )
                
                # Temporary handling: Save first 500 chars with comment
                # TODO (Day 3-4): Parse JSON and save all files properly
                source_code = (
                    f"// Multi-file contract detected\n"
                    f"// Full JSON structure (truncated to 500 chars):\n"
                    f"{source_code[:500]}...\n\n"
                    f"// TODO: Implement full multi-file extraction"
                )
            
            # ================================================================
            # FILE WRITE
            # ================================================================
            
            # Write source code to file
            # encoding="utf-8": Support all Unicode characters
            #   - Chinese/Korean comments: // 这是代币合约
            #   - Emoji in errors: revert("❌ Insufficient balance")
            #   - Math symbols: // Δx = x₂ - x₁
            # Without UTF-8: UnicodeEncodeError on non-ASCII characters
            filepath.write_text(source_code, encoding="utf-8")
            
            logger.info(f"✓ Saved {filename}")
            return filepath
        
        except Exception as e:
            # Catch file system errors (permissions, disk full, etc.)
            logger.error(f"Failed to save {address}: {e}")
            return None
    
    # ========================================================================
    # PUBLIC METHOD 3: BATCH SCRAPING WITH PROGRESS TRACKING
    # ========================================================================
    
    def scrape_batch(
        self,
        addresses: List[str],
        output_dir: Path = Path("blockchain/contracts/collected"),
        save_every: int = 10
    ) -> List[Path]:
        """
        Scrape multiple contracts with progress bar and incremental saves.
        
        This is the main entry point for production use.
        
        Features:
        ---------
        1. Progress bar (tqdm): Visual feedback for long-running operations
        2. Checkpoints: Log progress every N contracts (don't lose work on crash)
        3. Graceful failure: Skip failed contracts, continue with rest
        4. Keyboard interrupt: Ctrl+C stops cleanly, returns what was collected
        5. Summary statistics: Final report of success/failure counts
        
        Workflow for Each Contract:
        ---------------------------
        1. Fetch source code from Etherscan API
        2. If fetch fails → Log, add to failed list, continue
        3. Save to .sol file
        4. If save fails → Log, add to failed list, continue
        5. Every N contracts → Log checkpoint (for monitoring)
        
        Args:
            addresses (List[str]): List of contract addresses to scrape
            output_dir (Path): Where to save .sol files
            save_every (int): Checkpoint frequency (log every N contracts)
        
        Returns:
            List[Path]: Paths to successfully saved files
                Note: Length may be less than len(addresses) if some failed
        
        Example Usage:
        --------------
        >>> scraper = EtherscanScraper()
        >>> addresses = ["0x123...", "0x456...", "0x789..."]
        >>> files = scraper.scrape_batch(addresses, save_every=5)
        Scraping contracts: 100%|████████| 3/3 [00:01<00:00, 2.50it/s]
        >>> print(f"Saved {len(files)} contracts")
        Saved 2 contracts  # One failed, but didn't stop the batch
        
        Production Tips:
        ----------------
        - Start small: Test with 10 contracts before running 1000
        - Monitor logs: Check for patterns in failures (all same error?)
        - Rate limit buffer: If seeing 429 errors, increase RATE_LIMIT_DELAY
        - Checkpoint frequency: Lower save_every for faster feedback (but more log spam)
        """
        # ====================================================================
        # INITIALIZATION
        # ====================================================================
        
        # Track successfully saved file paths (return value)
        saved_files = []
        
        # Track failed addresses for final report
        failed_addresses = []
        
        logger.info(f"Starting batch scrape: {len(addresses)} contracts")
        
        # ====================================================================
        # MAIN SCRAPING LOOP
        # ====================================================================
        
        # enumerate(): Get both index and item (i, address)
        # tqdm(): Wrap iterable to show progress bar
        #   Output: Scraping contracts: 47/100 [===>....] 47% ETA: 0:02:15
        for i, address in enumerate(tqdm(addresses, desc="Scraping contracts")):
            try:
                # ============================================================
                # STEP 1: FETCH SOURCE CODE
                # ============================================================
                
                contract_data = self.fetch_contract_source(address)
                
                # If fetch failed (returns None), skip to next contract
                if contract_data is None:
                    failed_addresses.append(address)
                    continue  # Skip rest of loop body, go to next iteration
                
                # ============================================================
                # STEP 2: SAVE TO FILE
                # ============================================================
                
                filepath = self.save_contract(address, contract_data, output_dir)
                
                # If save succeeded, add to success list
                if filepath:
                    saved_files.append(filepath)
                else:
                    # Save failed (disk full? permissions?)
                    failed_addresses.append(address)
                
                # ============================================================
                # STEP 3: CHECKPOINT LOGGING
                # ============================================================
                
                # Modulo operator: Check if we've hit checkpoint interval
                # (i + 1) % save_every == 0 when i+1 = 10, 20, 30, ...
                # Why i+1? Because i starts at 0, so i=9 is the 10th contract
                if (i + 1) % save_every == 0:
                    logger.info(
                        f"Checkpoint {i + 1}/{len(addresses)}: "
                        f"{len(saved_files)} saved, {len(failed_addresses)} failed"
                    )
            
            except KeyboardInterrupt:
                # ============================================================
                # USER INTERRUPT HANDLING (Ctrl+C)
                # ============================================================
                
                # User pressed Ctrl+C → Stop gracefully
                # Don't lose progress: Return what we've collected so far
                logger.warning(
                    f"Scraping interrupted by user at {i + 1}/{len(addresses)}. "
                    f"Returning {len(saved_files)} collected contracts."
                )
                break  # Exit loop (returns saved_files below)
            
            except Exception as e:
                # ============================================================
                # UNEXPECTED ERROR HANDLING
                # ============================================================
                
                # Should rarely happen (fetch/save have their own try-except)
                # But catch anyway for robustness
                logger.error(f"Unexpected error for {address}: {e}")
                failed_addresses.append(address)
                continue  # Don't let one weird error kill entire batch
        
        # ====================================================================
        # FINAL SUMMARY
        # ====================================================================
        
        # Log completion statistics
        success_count = len(saved_files)
        total_count = len(addresses)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        logger.info(
            f"Batch complete: {success_count}/{total_count} contracts saved "
            f"({success_rate:.1f}% success rate)"
        )
        
        # If any failures, show first 10 for debugging
        # (Don't spam logs with 1000 failed addresses)
        if failed_addresses:
            preview = failed_addresses[:10]
            more = len(failed_addresses) - 10
            logger.warning(
                f"Failed addresses: {preview}"
                f"{f' ... and {more} more' if more > 0 else ''}"
            )
        
        return saved_files


# ============================================================================
# USAGE EXAMPLE (Run this file directly to test)
# ============================================================================

if __name__ == "__main__":
    """
    Test scraper with a few known verified contracts.
    
    Run with: poetry run python src/chainguardian/data_collection/etherscan_scraper.py
    """
    # Initialize scraper (reads API key from .env)
    scraper = EtherscanScraper()
    
    # Test with a few well-known contracts
    test_addresses = [
        "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT Token
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC Token
        "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",  # Uniswap Token
    ]
    
    print(f"\n{'='*60}")
    print(f"Testing EtherscanScraper with {len(test_addresses)} contracts")
    print(f"{'='*60}\n")
    
    # Scrape batch
    saved = scraper.scrape_batch(
        test_addresses,
        output_dir=Path("blockchain/contracts/test_collection"),
        save_every=1  # Log after each contract (for testing)
    )
    
    print(f"\n{'='*60}")
    print(f"Test complete: {len(saved)}/{len(test_addresses)} contracts saved")
    print(f"Files saved to: blockchain/contracts/test_collection/")
    print(f"{'='*60}\n")
