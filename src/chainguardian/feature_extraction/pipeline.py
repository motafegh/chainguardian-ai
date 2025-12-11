"""
Unified Feature Extraction Pipeline
====================================

🎯 PURPOSE: Orchestrate the entire feature extraction process

This is the ORCHESTRATOR layer - it coordinates multiple components:
- Version detection (regex on source code)
- Compiler switching (solc-select subprocess)
- Static analysis (Slither detectors)
- AST analysis (code structure metrics)
- Data formatting (pandas DataFrame)

📖 LEARNING OBJECTIVES:
- Understand orchestration vs implementation
- Learn multi-version dependency management
- Practice subprocess management
- See design patterns: Builder, Strategy, Facade
- Understand stateful vs stateless design

🔑 KEY INNOVATION:
Auto-detects Solidity version from pragma and switches compiler
This allows analyzing contracts from 2016-2025 (Solidity 0.4.x → 0.8.x)

🐛 CRITICAL BUG FIXED:
Detectors must be manually registered before running Slither
They don't auto-load! Took 3 hours to debug this.

Author: Ali - ChainGuardian AI Project
Day: 1-2
"""

from pathlib import Path  # Modern file handling
from typing import Dict, Optional  # Type hints for clarity
import pandas as pd  # DataFrame for ML-ready format
import logging  # Production logging, not print()
import re  # Regular expressions for pragma parsing
import subprocess  # Run external commands (solc-select)
from slither import Slither  # Static analysis tool

# 🎓 IMPORT PATTERN: Import module, not individual classes
# Why? Avoids naming collisions with our own classes
# We access as: detector_module.ReentrancyEth
import slither.detectors.all_detectors as detector_module

# 🎓 INTERNAL IMPORTS: Our own modules
from chainguardian.feature_extraction.contract_analyzer import SlitherAnalyzer, ContractFeatures
from chainguardian.feature_extraction.ast_analyzer import ASTFeatureExtractor

# 🎓 LOGGING: Production-grade logging, not print()
# Why logging > print()?
# - Can enable/disable by level (DEBUG, INFO, WARNING, ERROR)
# - Can redirect to files
# - Includes timestamps automatically
# - Can filter by module name
logger = logging.getLogger(__name__)  # __name__ = "chainguardian.feature_extraction.pipeline"


class FeaturePipeline:
    """
    End-to-end pipeline: Contract → Feature Vector → ML-ready format
    
    🎓 DESIGN PATTERN: Facade Pattern
    Provides simple interface to complex subsystem:
    - Hides Slither complexity
    - Hides solc-select complexity
    - Hides pandas complexity
    User just calls: pipeline.analyze_contract()
    
    🎓 DESIGN PATTERN: Builder Pattern
    Accumulates data over multiple calls:
    - Call analyze_contract() multiple times
    - Each call adds to self.features list
    - Finally: to_dataframe() builds final dataset
    
    WHY: ML models need consistent feature vectors across all contracts
    
    CAPABILITIES:
    - Automatically handles multiple Solidity versions (0.4.x → 0.8.x)
    - Registers and runs all 93 Slither detectors
    - Combines vulnerability features + code structure features
    - Exports to pandas DataFrame for scikit-learn/XGBoost
    """
    
    def __init__(self):
        """
        Initialize with empty feature list.
        
        🎓 DESIGN DECISION: Stateful Object
        Alternative: Make each method static, return features, collect externally
        Trade-off: Current approach is simpler but less flexible
        
        WHY STATEFUL: We'll collect features from multiple contracts into a dataset
        Each analyze_contract() call appends to self.features list
        
        🎓 TYPE HINT: list[Dict]
        Python 3.9+ syntax (older: List[Dict[str, Any]])
        Tells IDE: "This is a list of dictionaries"
        Benefits: Autocomplete, type checking, documentation
        """
        self.features: list[Dict] = []
    
    def _detect_solidity_version(self, contract_path: Path) -> str:
        """
        Extract Solidity version from pragma statement using regex.
        
        🎓 PROBLEM: Solidity has 12 major versions (0.4.0 → 0.8.31)
        Each version has breaking changes (like Python 2 → 3)
        Old contracts won't compile with new compilers
        
        🎓 SOLUTION: Parse pragma statement to find required version
        
        🎓 REGEX PATTERN BREAKDOWN:
        r'pragma\s+solidity\s+[\^=~]?([\d.]+)'
        
        - r'...' = Raw string (backslashes don't escape)
        - pragma = Literal text "pragma"
        - \s+ = One or more whitespace chars (space, tab, newline)
        - solidity = Literal text "solidity"
        - [\^=~]? = Optional version operator (^, =, or ~)
        - ([\d.]+) = Capture group: digits and dots (e.g., "0.5.12")
        
        🎓 EXAMPLES:
        ----------------
        pragma solidity ^0.4.17;  → Captures "0.4.17"
        pragma solidity =0.5.12;  → Captures "0.5.12"
        pragma solidity ^0.8.0;   → Captures "0.8.0"
        pragma solidity 0.6.12;   → Captures "0.6.12"
        
        Args:
            contract_path: Path to .sol file
            
        Returns:
            Version string (e.g., "0.5.12")
            Falls back to "0.8.31" if no pragma found
        """
        try:
            # 🎓 PATHLIB: Modern file reading
            # Path.read_text() = open(), read(), close() in one call
            # encoding="utf-8" handles Unicode (emoji, non-English comments)
            content = contract_path.read_text(encoding="utf-8")
            
            # 🎓 REGEX SEARCH: Find first match in string
            # re.search() returns Match object or None
            match = re.search(
                r'pragma\s+solidity\s+[\^=~]?([\d.]+)',
                content
            )
            
            if match:
                # 🎓 CAPTURE GROUP: Extract matched substring
                # .group(0) = entire match ("pragma solidity ^0.4.17")
                # .group(1) = first capture group ("0.4.17")
                version = match.group(1)
                
                # 🎓 LOGGING LEVEL: INFO
                # Use INFO for significant events (not DEBUG for noise)
                logger.info(f"Detected Solidity version: {version} in {contract_path.name}")
                return version
            else:
                # 🎓 DEFENSIVE FALLBACK: Old contracts sometimes lack pragma
                # Default to latest stable version
                logger.warning(
                    f"No pragma found in {contract_path.name}, "
                    f"defaulting to 0.8.31"
                )
                return "0.8.31"
                
        except Exception as e:
            # 🎓 BROAD EXCEPTION CATCH: Could be file not found, encoding error, etc.
            # Log error but don't crash - return safe default
            logger.error(f"Failed to detect version for {contract_path}: {e}")
            return "0.8.31"
    
    def _set_solc_version(self, version: str) -> bool:
        """
        Switch to specific Solidity compiler version using solc-select.
        
        🎓 PROBLEM: Need multiple Solidity compilers installed simultaneously
        - USDT uses 0.4.17 (2018)
        - USDC uses 0.4.24 (2018)
        - UNI uses 0.5.16 (2020)
        - DAI uses 0.5.12 (2019)
        
        🎓 SOLUTION: solc-select (version manager for Solidity compilers)
        Similar to: nvm (Node.js), pyenv (Python), rustup (Rust)
        
        🎓 HOW IT WORKS:
        - Installs compilers to: ~/.solc-select/artifacts/
        - Creates symlink: /usr/bin/solc → ~/.solc-select/artifacts/solc-0.5.12
        - When you run "solc", it uses the symlinked version
        
        🎓 SUBPROCESS: Run external command from Python
        Alternative: os.system() (old, avoid), shell=True (dangerous)
        
        Args:
            version: Solidity version to use (e.g., "0.5.12")
            
        Returns:
            True if switch successful
            False if version not installed
        """
        try:
            # 🎓 SUBPROCESS.RUN: Modern way to run external commands
            # Arguments:
            # - ["solc-select", "use", "0.5.12"] = Command + args (list, not string!)
            # - capture_output=True = Capture stdout/stderr (don't print to terminal)
            # - text=True = Decode bytes to string (not b'...')
            # - check=True = Raise exception if exit code != 0
            result = subprocess.run(
                ["solc-select", "use", version],
                capture_output=True,  # Get output for logging
                text=True,  # Decode as UTF-8 string
                check=True  # Raise CalledProcessError if fails
            )
            
            # 🎓 LOGGING: Always log external command success
            logger.info(f"✓ Switched to Solidity {version}")
            return True
            
        except subprocess.CalledProcessError as e:
            # 🎓 SPECIFIC EXCEPTION: subprocess.CalledProcessError
            # Raised when: check=True and exit code != 0
            # Contains: .returncode, .stdout, .stderr
            
            # 🎓 HELPFUL ERROR MESSAGE: Tell user HOW to fix
            # Good error messages = teaching moments
            logger.error(
                f"Failed to switch to Solidity {version}. "
                f"Install it with: solc-select install {version}\n"
                f"Error: {e.stderr}"  # Show actual error from solc-select
            )
            return False
    
    def analyze_contract(
        self, 
        contract_path: Path, 
        contract_name: str
    ) -> Dict:
        """
        Extract ALL features from a single contract.
        
        🎓 THIS IS THE HEART OF THE PIPELINE
        This method coordinates 6 different operations into one workflow
        
        🎓 DESIGN PATTERN: Template Method Pattern
        Defines algorithm structure, delegates steps to other classes
        
        🐛 CRITICAL FIX: Detector Registration
        Detectors must be manually registered before running Slither!
        They don't auto-load. Spent 3 hours debugging this.
        
        Workflow (7 steps):
        -------------------
        1. Detect required Solidity version from pragma (regex)
        2. Switch compiler to that version (subprocess)
        3. Create Slither object (compiles contract, builds AST)
        4. Register all 93 detectors (CRITICAL! manual step)
        5. Extract vulnerability features via SlitherAnalyzer
        6. Extract code structure features via ASTFeatureExtractor
        7. Combine into single 15-feature dict
        
        🎓 RETURN VALUE: Dict with 15 features
        Could use dataclass, but dict is more flexible for now
        
        Args:
            contract_path: Path to .sol file
            contract_name: Name of main contract to analyze (e.g., "TetherToken")
        
        Returns:
            Dict with 15 features (2 metadata + 7 vulnerability + 6 code structure)
        """
        # 🎓 LOGGING: Always log start of major operations
        logger.info(f"Analyzing {contract_name} from {contract_path}")
        
        # 🎓 INITIALIZE RESULT DICT: Start with metadata
        # We'll add vulnerability and AST features later
        combined_features = {
            'contract_name': contract_name,
            'file_path': str(contract_path),  # Path → str for CSV export
        }
        
        try:
            # ================================================================
            # STEP 1: DETECT REQUIRED SOLIDITY VERSION
            # ================================================================
            # 🎓 WHY: Can't compile 0.4.x contract with 0.8.x compiler
            # Breaking changes in every major version
            # ================================================================
            
            required_version = self._detect_solidity_version(contract_path)
            
            # ================================================================
            # STEP 2: SWITCH COMPILER TO THAT VERSION
            # ================================================================
            # 🎓 WHY: Ensure Slither uses correct compiler
            # solc-select changes symlink: /usr/bin/solc → correct version
            # ================================================================
            
            if not self._set_solc_version(required_version):
                # 🎓 EARLY RETURN: Raise exception to trigger error handling
                # Alternative: Return None and check in caller
                # Trade-off: Exceptions are clearer for error flow
                raise Exception(
                    f"Solidity {required_version} not installed. "
                    f"Run: solc-select install {required_version}"
                )
            
            # ================================================================
            # STEP 3: CREATE SLITHER OBJECT (COMPILE CONTRACT)
            # ================================================================
            # 🎓 SLITHER COMPILATION PROCESS:
            # 1. Calls solc compiler (from PATH)
            # 2. Parses compiler output (AST JSON)
            # 3. Builds internal representation (Contract objects)
            # 4. NO detectors run yet! Just compilation.
            # ================================================================
            
            slither = Slither(
                str(contract_path),  # Slither wants string, not Path
                solc="solc",  # Use solc from PATH (managed by solc-select)
                solc_disable_warnings=True  # Suppress noisy warnings
            )
            
            # ================================================================
            # STEP 4: REGISTER DETECTORS (CRITICAL!)
            # ================================================================
            # 🐛 THE BUG WE FIXED:
            # Slither doesn't auto-load detectors!
            # You must manually register each detector class.
            # Without this, slither.run_detectors() returns empty list!
            #
            # 🎓 DEBUGGING PROCESS:
            # 1. Noticed detector_results was always []
            # 2. Checked Slither docs (vague)
            # 3. Inspected slither.detectors (empty list!)
            # 4. Found register_detector() method
            # 5. Realized: Must call for each detector
            # 6. But how to get list of all detectors?
            # 7. Explored slither.detectors.all_detectors module
            # 8. Used dir() to see module contents
            # 9. Filtered for uppercase names (class convention)
            # 10. Success! 93 detectors registered.
            # ================================================================
            
            logger.debug(f"Registering detectors...")
            
            # 🎓 INTROSPECTION: Get all attributes from module
            # dir(detector_module) returns list of names (strings)
            # ['ABIEncoderV2Array', 'ArbitrarySendEth', ..., '__builtins__', '__file__']
            
            # 🎓 FILTERING: Extract only class names
            # Convention: Classes start with uppercase, modules/functions lowercase
            # We want: ReentrancyEth, ArbitrarySendEth
            # Not: __builtins__, __file__, __name__
            detector_classes = [
                getattr(detector_module, name)  # Get actual class object, not string
                for name in dir(detector_module)  # All attribute names
                if name[0].isupper()  # Filter: starts with uppercase
            ]
            
            # 🎓 WHY getattr()?
            # We have: name = "ReentrancyEth" (string)
            # We need: detector_module.ReentrancyEth (class object)
            # getattr(detector_module, "ReentrancyEth") = detector_module.ReentrancyEth
            
            # 🎓 REGISTRATION LOOP: Register each detector with Slither
            # This populates slither.detectors list
            for detector_class in detector_classes:
                slither.register_detector(detector_class)
            
            # 🎓 VALIDATION: Log how many registered (should be ~93)
            logger.info(f"✓ Registered {len(slither.detectors)} detectors")
            
            # ================================================================
            # STEP 5: EXTRACT VULNERABILITY FEATURES
            # ================================================================
            # 🎓 DELEGATION: Pass Slither object to specialized analyzer
            # SlitherAnalyzer knows how to:
            # - Run detectors (slither.run_detectors())
            # - Parse results (nested list of dicts)
            # - Map detector names to feature flags
            # - Count severities
            # ================================================================
            
            vuln_analyzer = SlitherAnalyzer(slither)
            vuln_features = vuln_analyzer.extract_features(contract_name)
            
            # 🎓 DICT UPDATE: Merge vulnerability features into main dict
            # vuln_features is a ContractFeatures dataclass
            # We extract just the vulnerability fields
            combined_features.update({
                'has_reentrancy': vuln_features.has_reentrancy,
                'has_access_control_issues': vuln_features.has_access_control_issues,
                'has_timestamp_dependency': vuln_features.has_timestamp_dependency,
                'has_unchecked_call': vuln_features.has_unchecked_call,
                'high_severity_count': vuln_features.high_severity_count,
                'medium_severity_count': vuln_features.medium_severity_count,
                'low_severity_count': vuln_features.low_severity_count,
            })
            
            # ================================================================
            # STEP 6: EXTRACT AST FEATURES (CODE STRUCTURE)
            # ================================================================
            # 🎓 AST = Abstract Syntax Tree
            # Tree representation of code structure
            # Allows analyzing code without executing it
            #
            # We extract:
            # - How many functions? (complexity indicator)
            # - How many external calls? (attack surface)
            # - How many state variables? (storage cost)
            # - Cyclomatic complexity (code complexity metric)
            # ================================================================
            
            ast_extractor = ASTFeatureExtractor(contract_path)
            ast_features = ast_extractor.extract_features(contract_name)
            
            # 🎓 DICT UPDATE: Merge AST features
            # ast_features is already a dict, so just update
            combined_features.update(ast_features)
            
            # 🎓 SUCCESS LOGGING: Log completion with metrics
            logger.info(
                f"✓ Extracted {len(combined_features)} features for {contract_name}"
            )
            
        except Exception as e:
            # ================================================================
            # ERROR HANDLING: GRACEFUL DEGRADATION
            # ================================================================
            # 🎓 STRATEGY: Don't crash entire pipeline on one contract failure
            # Instead: Return default values (zeros/False)
            # Result: Partial dataset > no dataset
            #
            # 🎓 WHY: ML training can handle some missing data
            # Better to have 95/100 contracts than 0/100
            # ================================================================
            
            logger.error(f"Analysis failed for {contract_name}: {e}")
            
            # 🎓 DEFAULT VALUES: All zeros/False
            # Indicates: "We couldn't analyze this contract"
            # ML interpretation: Probably safe (no vulnerabilities found)
            # Alternative: Use NaN (missing value), but complicates ML
            combined_features.update({
                'has_reentrancy': False,
                'has_access_control_issues': False,
                'has_timestamp_dependency': False,
                'has_unchecked_call': False,
                'high_severity_count': 0,
                'medium_severity_count': 0,
                'low_severity_count': 0,
                'num_functions': 0,
                'num_external_calls': 0,
                'num_state_vars': 0,
                'num_modifiers': 0,
                'max_cyclomatic_complexity': 0,
                'num_low_level_calls': 0,
            })
        
        # 🎓 STATE MUTATION: Add to internal list
        # This allows calling analyze_contract() multiple times
        # Then: to_dataframe() converts entire list to DataFrame
        self.features.append(combined_features)
        
        return combined_features
    
    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert collected features to pandas DataFrame.
        
        🎓 PANDAS: Python Data Analysis Library
        DataFrame = Table with rows and columns (like Excel/SQL)
        
        WHY PANDAS:
        - ML libraries (scikit-learn, XGBoost) expect pandas input
        - Easy data manipulation (.mean(), .sum(), .groupby())
        - Built-in CSV export (.to_csv())
        - Visualization support (.plot())
        
        🎓 DATA STRUCTURE TRANSFORMATION:
        From: list[dict] = [{'has_reentrancy': True, ...}, ...]
        To: DataFrame with columns: [has_reentrancy, has_access_control, ...]
        
        Returns:
            pandas DataFrame with all collected features
            Columns: 15 features
            Rows: One per contract
        """
        # 🎓 VALIDATION: Check if any features collected
        if not self.features:
            logger.warning("No features collected yet")
            return pd.DataFrame()  # Empty DataFrame (0 rows, 0 columns)
        
        # 🎓 PANDAS CONSTRUCTOR: Convert list of dicts to DataFrame
        # Magic: Automatically uses dict keys as column names!
        # Each dict becomes one row
        df = pd.DataFrame(self.features)
        
        # 🎓 LOGGING: Report dataset shape
        # shape = (rows, columns) tuple
        logger.info(
            f"Created DataFrame with {len(df)} contracts and "
            f"{len(df.columns)} features"
        )
        return df
    
    def save_dataset(self, output_path: Path):
        """
        Save features as CSV for ML training.
        
        🎓 CSV FORMAT: Comma-Separated Values
        Universal format for ML:
        - pandas can read it
        - Excel can open it
        - Human-readable (text file)
        - No dependencies (not pickle, not parquet)
        
        Example CSV output:
        -------------------
        contract_name,has_reentrancy,num_functions,...
        TetherToken,False,13,...
        SafeBank,False,5,...
        
        Args:
            output_path: Where to save CSV file
        """
        df = self.to_dataframe()
        
        # 🎓 PANDAS CSV EXPORT:
        # index=False: Don't save row numbers (0, 1, 2, ...)
        # Why? Row numbers are meaningless, would confuse ML model
        df.to_csv(output_path, index=False)
        
        logger.info(f"Saved dataset to {output_path}")
