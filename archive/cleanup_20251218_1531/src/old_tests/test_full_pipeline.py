"""
Full Pipeline Test: Scrape → Extract Features → Save Dataset
=============================================================

🎯 PURPOSE: End-to-end integration test for ChainGuardian AI data collection

This combines Day 1 (feature extraction) + Day 2 (scraper) into
a complete data collection workflow.

📖 LEARNING OBJECTIVES:
- Understand ETL (Extract-Transform-Load) pipeline design
- Learn error handling strategies for production systems
- Practice working with external APIs and compilers
- See how to handle multi-version software dependencies

Workflow:
1. Scrape contracts from Etherscan (EXTRACT)
2. Detect Solidity version from pragma (PREPARE)
3. Switch compiler to correct version (SETUP)
4. Use Slither to discover contract names (DISCOVER)
5. Intelligently select main contract (FILTER)
6. Run Slither analysis (ANALYZE)
7. Extract 15 features (TRANSFORM)
8. Export to CSV (LOAD)

🔑 KEY CONCEPTS DEMONSTRATED:
- ETL pipeline architecture
- Graceful degradation (partial success > total failure)
- Multi-version compiler orchestration
- Heuristic-based filtering (filename matching, keyword filtering)
- Progress tracking and logging

Author: Ali - ChainGuardian AI Project
Day: 2
"""

from pathlib import Path  # Modern Python file handling (better than os.path)

from chainguardian.data_collection.etherscan_scraper import EtherscanScraper
from chainguardian.feature_extraction.pipeline import FeaturePipeline
from slither import Slither  # Static analysis tool for Solidity


def main():
    """
    Run full scrape + feature extraction pipeline.
    
    🎓 DESIGN PATTERN: Pipeline Pattern
    Each step transforms data and passes to next step.
    If one step fails, we continue with remaining items.
    
    🎓 ERROR HANDLING STRATEGY: Fail-Safe
    - Individual contract failure doesn't stop the pipeline
    - Log errors but continue processing
    - Return partial results (some data > no data)
    
    This is the integration test that validates our entire
    data collection system works end-to-end.
    """
    
    print("\n" + "="*60)
    print("FULL PIPELINE TEST: Scrape + Feature Extraction")
    print("="*60 + "\n")
    
    # ================================================================
    # STEP 1: SCRAPE CONTRACTS FROM ETHERSCAN
    # ================================================================
    # 🎓 ETL STAGE: EXTRACT
    # We're pulling raw data from external source (Etherscan API)
    # ================================================================
    
    print("Step 1: Scraping contracts from Etherscan...\n")
    
    # 🎓 DEPENDENCY INJECTION: EtherscanScraper reads API key from .env
    # Why? Keeps secrets out of code, easy to switch environments
    scraper = EtherscanScraper()
    
    # 🎓 PRODUCTION DATA: These are REAL contracts managing billions of dollars
    # Why use real contracts for testing?
    # - Validates our code works on production data
    # - Provides diverse Solidity versions (0.4.17 → 0.8.x)
    # - Tests edge cases (multiple contracts per file, libraries, etc.)
    test_addresses = [
        "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT (Tether) - 0.4.17
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC (Circle) - 0.4.24
        "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",  # UNI (Uniswap) - 0.5.16
        "0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAI (MakerDAO) - 0.5.12
        "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",  # WBTC (Wrapped Bitcoin) - 0.4.11
    ]
    
    # 🎓 BATCH PROCESSING: Process multiple items with progress tracking
    # save_every=2: Checkpoint every 2 contracts (log progress)
    # Why checkpoints? If API rate limit hits, we don't lose all progress
    saved_files = scraper.scrape_batch(
        test_addresses,
        output_dir=Path("blockchain/contracts/collected"),
        save_every=2  # Log after every 2 contracts
    )
    
    print(f"\n✓ Scraped {len(saved_files)} contracts\n")
    
    # ================================================================
    # STEP 2: EXTRACT FEATURES FROM EACH CONTRACT
    # ================================================================
    # 🎓 ETL STAGE: TRANSFORM
    # We're converting raw Solidity code → structured feature vectors
    # ================================================================
    
    print("Step 2: Running Slither analysis (this takes 30-60s)...\n")
    
    # 🎓 STATEFUL OBJECT: FeaturePipeline accumulates results internally
    # Each analyze_contract() call appends to self.features list
    # Alternative design: Return features and collect in list here
    # Trade-off: Current design is simpler but less flexible
    pipeline = FeaturePipeline()
    
    # ================================================================
    # ANALYZE EACH SCRAPED CONTRACT
    # ================================================================
    # 🎓 ITERATION PATTERN: Process list of items with error handling
    # ================================================================
    
    for filepath in saved_files:
        try:
            # ============================================================
            # DISCOVER CONTRACT NAMES USING SLITHER
            # ============================================================
            # 🎓 PROBLEM: .sol files can contain multiple contracts
            # - Libraries (SafeMath, AddressUtils)
            # - Base contracts (Ownable, Pausable)
            # - Interfaces (IERC20)
            # - Main contract (TetherToken) ← We want this!
            #
            # 🎓 WHY NOT REGEX?
            # ❌ Comments can contain "contract" keyword
            # ❌ String literals can contain "contract"
            # ❌ Doesn't distinguish interface vs implementation
            # ✅ Slither already parsed AST, gives us accurate list
            # ============================================================
            
            print(f"Analyzing {filepath.stem}...")
            
            try:
                # ========================================================
                # DETECT VERSION BEFORE CREATING TEMP SLITHER
                # ========================================================
                # 🎓 PROBLEM: Slither uses solc from PATH
                # If wrong version installed, compilation fails
                # 🎓 SOLUTION: Detect version → Switch compiler → Compile
                # ========================================================
                
                # 🎓 METHOD REUSE: Don't Repeat Yourself (DRY principle)
                # We already wrote version detection in pipeline.py
                # So we call pipeline._detect_solidity_version()
                # (Yes, it's "private" by convention, but Python allows it)
                required_version = pipeline._detect_solidity_version(filepath)
                
                # 🎓 EXTERNAL TOOL: solc-select manages multiple Solidity compilers
                # It switches the 'solc' symlink to point to correct version
                # Similar to: nvm (Node.js), pyenv (Python), rustup (Rust)
                pipeline._set_solc_version(required_version)
                
                # 🎓 TEMPORARY SLITHER OBJECT: Why create another one?
                # - We only need contract names (lightweight operation)
                # - The full analysis happens in pipeline.analyze_contract()
                # - Creating temp Slither is cheap (no detector registration)
                temp_slither = Slither(
                    str(filepath),                 # Slither wants string, not Path
                    solc="solc",                   # Use solc from PATH (managed by solc-select)
                    solc_disable_warnings=True     # Suppress noisy compiler warnings
                )
                
                # 🎓 SLITHER DATA STRUCTURE:
                # temp_slither.contracts is a list of Contract objects
                # Each Contract has: .name, .functions, .state_variables, etc.
                # We extract just the names using list comprehension
                contract_names = [c.name for c in temp_slither.contracts]
                
                # 🎓 VALIDATION: Sanity check before proceeding
                # Files SHOULD have contracts, but might be empty or invalid
                if not contract_names:
                    print(f"  ⚠ No contracts found in {filepath.name}, skipping\n")
                    continue  # Skip to next file in loop
                
                # ========================================================
                # SELECT MAIN CONTRACT (HEURISTIC ALGORITHM)
                # ========================================================
                # 🎓 PROBLEM: Which contract should we analyze?
                # Files often have 5-10 contracts, but only 1 is "main"
                #
                # 🎓 HEURISTIC: A practical approach that usually works
                # Not guaranteed to be perfect, but good enough
                #
                # 🎓 STRATEGY 1: Filename matching (most reliable)
                # Developers name files after main contract:
                # - "TetherToken_0xABC.sol" → Main contract is "TetherToken"
                # - "UniswapV2Pair.sol" → Main contract is "UniswapV2Pair"
                # ========================================================
                
                # Extract contract name from filename
                # "TetherToken_0xdAC17F95.sol" → "TetherToken"
                # split('_')[0] removes the address part
                filename_base = filepath.stem.split('_')[0]
                
                main_contract = None
                
                # Try exact match with filename first (case-insensitive)
                # This catches: TetherToken, FiatTokenProxy, Uni, Dai, WBTC
                for name in contract_names:
                    if name.lower() == filename_base.lower():
                        main_contract = name
                        break  # Found it! Exit loop early
                
                # ========================================================
                # STRATEGY 2: KEYWORD FILTERING + POSITION HEURISTIC
                # ========================================================
                # 🎓 FALLBACK: If filename doesn't match any contract
                # (Rare, but happens with proxy contracts or renamed files)
                #
                # 🎓 OBSERVATION: In Solidity files, structure is usually:
                # 1. Import statements
                # 2. Libraries (SafeMath, LibNote)
                # 3. Interfaces (IERC20, IProxy)
                # 4. Base contracts (Ownable, Pausable)
                # 5. Main contract ← LAST! (Solidity convention)
                # ========================================================
                
                if not main_contract:
                    # 🎓 BLACKLIST: Known library/base contract names
                    # These appear in almost all contracts but aren't "main"
                    skip_keywords = [
                        'safemath',      # OpenZeppelin math library
                        'ownable',       # Ownership management base
                        'libnote',       # DAI library for events
                        'addressutils',  # Address helper functions
                        'pausable',      # Emergency stop functionality
                        'erc20basic',    # Basic ERC20 interface
                    ]
                    
                    # 🎓 LIST COMPREHENSION: Pythonic filtering
                    # Equivalent to:
                    # filtered = []
                    # for n in contract_names:
                    #     if n.lower() not in skip_keywords:
                    #         filtered.append(n)
                    filtered = [
                        n for n in contract_names
                        if n.lower() not in skip_keywords
                    ]
                    
                    # 🎓 HEURISTIC: Pick last remaining contract
                    # Why last? Solidity convention: define helpers first, main last
                    # 🎓 DEFENSIVE: If everything filtered (rare), use last original
                    main_contract = filtered[-1] if filtered else contract_names[-1]
                
                # 🎓 LOGGING: Always log what was found and what was chosen
                # Helps debug when heuristic picks wrong contract
                print(f"  → Found contracts: {contract_names}")
                print(f"  → Using main contract: {main_contract}")
                
            except Exception as e:
                # ========================================================
                # ERROR HANDLING: Distinguish error types
                # ========================================================
                # 🎓 ERRORS WE EXPECT:
                # - Compilation errors (old Solidity syntax, missing imports)
                # - Parse errors (corrupted file, encoding issues)
                # - Slither bugs (rare, but happens)
                #
                # 🎓 STRATEGY: Log specific error, continue to next file
                # ========================================================
                
                error_msg = str(e)
                
                # 🎓 STRING MATCHING: Identify compilation errors
                # Slither throws generic Exception, so we inspect message
                if "Invalid compilation" in error_msg or "Expected identifier" in error_msg:
                    print(f"  ⚠ Compilation error (incompatible syntax), skipping\n")
                else:
                    print(f"  ⚠ Parse failed: {e}\n")
                
                continue  # Skip this contract, move to next
            
            # ============================================================
            # RUN FULL FEATURE EXTRACTION
            # ============================================================
            # 🎓 DELEGATION PATTERN: Pass work to specialized class
            # pipeline.analyze_contract() handles:
            # 1. Version detection (again, for safety)
            # 2. Compiler switching
            # 3. Slither compilation with detector registration
            # 4. Vulnerability feature extraction
            # 5. AST feature extraction
            # 6. Feature dict creation and storage
            # ============================================================
            
            pipeline.analyze_contract(
                contract_path=filepath,
                contract_name=main_contract  # ← Result from our heuristic selection!
            )
            
            print()  # Blank line for readability between contracts
            
        except KeyboardInterrupt:
            # ============================================================
            # USER INTERRUPTION: Ctrl+C pressed
            # ============================================================
            # 🎓 GRACEFUL SHUTDOWN: Save progress before exiting
            # Without this, user loses all work when they Ctrl+C
            # ============================================================
            print("\n⚠ Interrupted by user. Saving progress...\n")
            break  # Exit for loop, but continue to save step
            
        except Exception as e:
            # ============================================================
            # UNEXPECTED ERROR: Something we didn't anticipate
            # ============================================================
            # 🎓 DEFENSIVE PROGRAMMING: Catch everything else
            # Log error, print traceback (for debugging), continue
            # ============================================================
            print(f"  ⚠ Failed {filepath.name}: {e}\n")
            
            # 🎓 DEBUGGING: Print full stack trace
            # This helps diagnose issues during development
            import traceback
            traceback.print_exc()
            
            continue  # Don't let one error stop entire batch
    
    print(f"✓ Extracted features from {len(pipeline.features)} contracts\n")
    
    # ================================================================
    # STEP 3: SAVE DATASET TO CSV
    # ================================================================
    # 🎓 ETL STAGE: LOAD
    # We're persisting transformed data to disk for ML training
    # ================================================================
    
    print("Step 3: Saving dataset...\n")
    
    # 🎓 PATHLIB: Modern Python file operations
    # Advantages over os.path:
    # - Chainable operations: path / "subdir" / "file.csv"
    # - Built-in exists(), mkdir(), read_text(), etc.
    # - Works on Windows, Mac, Linux
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)  # Create if doesn't exist, no error if exists
    
    # 🎓 NAMING CONVENTION: Descriptive filenames with context
    # "scraped" = source (not manually created)
    # "contracts" = data type
    # "features" = content (not raw source code)
    output_path = data_dir / "scraped_contracts_features.csv"
    pipeline.save_dataset(str(output_path))
    
    print(f"✓ Dataset saved to: {output_path}")
    
    # ================================================================
    # STEP 4: DISPLAY SUMMARY STATISTICS
    # ================================================================
    # 🎓 DATA VALIDATION: Sanity check results make sense
    # Quick visual inspection before closing
    # ================================================================
    
    # 🎓 PANDAS: Convert to DataFrame for analysis
    # DataFrame gives us:
    # - Column operations (.sum(), .mean())
    # - Easy aggregation
    # - CSV export
    df = pipeline.to_dataframe()
    
    print("\n" + "="*60)
    print("PIPELINE COMPLETE")
    print("="*60)
    print(f"Contracts scraped: {len(saved_files)}")
    print(f"Features extracted: {len(pipeline.features)}")
    print(f"Dataset shape: {df.shape}")  # (rows, columns)
    
    # 🎓 SUMMARY STATISTICS: High-level overview
    # Helps validate pipeline found reasonable results
    if len(df) > 0:
        print(f"\nVulnerabilities found:")
        # .sum() on boolean columns = count of True values
        print(f"  - Reentrancy: {df['has_reentrancy'].sum()}")
        print(f"  - Access control: {df['has_access_control_issues'].sum()}")
        print(f"  - Unchecked calls: {df['has_unchecked_call'].sum()}")
        print(f"  - Timestamp dependency: {df['has_timestamp_dependency'].sum()}")
        
        print(f"\nSeverity distribution:")
        # .sum() on numeric columns = total count
        print(f"  - High severity: {df['high_severity_count'].sum()} issues")
        print(f"  - Medium severity: {df['medium_severity_count'].sum()} issues")
        print(f"  - Low severity: {df['low_severity_count'].sum()} issues")
        
        print(f"\nCode metrics (averages):")
        # .mean() computes average across all contracts
        print(f"  - Functions per contract: {df['num_functions'].mean():.1f}")
        print(f"  - External calls per contract: {df['num_external_calls'].mean():.1f}")
        print(f"  - State variables per contract: {df['num_state_vars'].mean():.1f}")
        print(f"  - Max complexity: {df['max_cyclomatic_complexity'].mean():.1f}")
        
        print(f"\nSample data (first contract):")
        # .iloc[0] = first row, .to_dict() = convert to dict for readability
        print(df.iloc[0].to_dict())
    else:
        print("\n⚠ No contracts successfully analyzed!")
    
    print("="*60 + "\n")


# ============================================================================
# SCRIPT ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    """
    🎓 PYTHON IDIOM: if __name__ == "__main__"
    
    This allows the file to be:
    1. RUN as a script: python test_full_pipeline.py
    2. IMPORTED as a module: from test_full_pipeline import main
    
    When imported, __name__ = "test_full_pipeline" (not "__main__")
    So main() doesn't execute automatically
    
    When run directly, __name__ = "__main__"
    So main() executes
    
    Why? Allows reusing code without side effects
    
    Run the full pipeline when script is executed directly.
    
    Usage:
        poetry run python src/chainguardian/data_collection/test_full_pipeline.py
    
    Expected runtime: 20-40 seconds (depends on contract complexity)
    Expected output: CSV file with 5 contracts, 15 features each
    
    Requirements:
        - ETHERSCAN_API_KEY in .env (get from etherscan.io/myapikey)
        - solc-select installed with versions: 0.4.17, 0.4.24, 0.5.12, 0.5.16, 0.8.x
        - Slither installed (via poetry add slither-analyzer)
    
    🎓 WHAT YOU LEARNED:
    ✅ ETL pipeline design (Extract-Transform-Load)
    ✅ Error handling strategies (fail-safe, graceful degradation)
    ✅ Heuristic algorithms (filename matching, keyword filtering)
    ✅ Multi-version compiler orchestration
    ✅ Production data processing
    ✅ Python idioms (pathlib, list comprehensions, if __name__)
    """
    main()
