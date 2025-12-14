"""
Contract Feature Extraction from Slither Analysis
==================================================

🎯 PURPOSE: Transform Slither detector results → ML feature vector

This is the ADAPTER layer - it translates Slither's output format
into our standardized feature representation for ML models.

📖 LEARNING OBJECTIVES:
- Understand dataclasses for structured data
- Learn many-to-one mapping (multiple detectors → one feature)
- Practice nested data structure parsing
- See defensive programming patterns
- Understand setattr() dynamic attribute setting

🔑 KEY INNOVATION:
Direct extraction from Slither object (no intermediate JSON files)
Faster and more reliable than file-based approaches

🐛 CRITICAL BUG FIXED:
Slither returns List[List[Dict]], not List[Dict]!
Must flatten nested structure before processing.

Author: Ali - ChainGuardian AI Project
Day: 1
"""

from typing import Dict  # Type hints for function signatures
from dataclasses import dataclass  # Cleaner than manual __init__
import logging  # Production logging
from slither import Slither  # Static analysis tool

# 🎓 LOGGER: Module-level logger
# Each module gets its own logger for filtering
logger = logging.getLogger(__name__)


@dataclass
class ContractFeatures:
    """
    Feature vector for a smart contract.
    
    🎓 DATACLASS: Python 3.7+ feature (cleaner than traditional class)
    Automatically generates:
    - __init__() method
    - __repr__() method (nice printing)
    - __eq__() method (equality comparison)
    
    🎓 WHY DATACLASS:
    Without:
        class ContractFeatures:
            def __init__(self, contract_name, file_path, has_reentrancy=False, ...):
                self.contract_name = contract_name
                self.file_path = file_path
                self.has_reentrancy = has_reentrancy
                # ... 10 more lines!
    
    With dataclass:
        @dataclass
        class ContractFeatures:
            contract_name: str
            file_path: str
            has_reentrancy: bool = False
            # Done! Much cleaner.
    
    🎓 FEATURE DESIGN PHILOSOPHY:
    We use BOOLEAN flags for vulnerabilities (not counts)
    Why? ML models learn better from "has_reentrancy: True/False"
    than from "reentrancy_count: 0-10" (too much variance)
    
    WHY: Structured data makes it easier to convert to pandas DataFrame later
    DataFrame expects consistent columns across all rows
    """
    
    # ================================================================
    # METADATA (Required, no defaults)
    # ================================================================
    # 🎓 NO DEFAULT VALUE: These must be provided in constructor
    # ContractFeatures("MyContract", "/path") ← Must provide these
    
    contract_name: str  # "TetherToken", "SafeBank", etc.
    file_path: str      # Full path for traceability
    
    # ================================================================
    # VULNERABILITY INDICATORS (Boolean flags)
    # ================================================================
    # 🎓 DEFAULT VALUE: = False
    # These are optional, default to False (no vulnerability)
    # ContractFeatures("MyContract", "/path") ← These default to False
    
    # 🎓 REENTRANCY: Classic Ethereum vulnerability
    # Example: The DAO hack (2016) - $60M stolen
    # Function calls external contract before updating state
    has_reentrancy: bool = False
    
    # 🎓 ACCESS CONTROL: Functions callable by wrong parties
    # Example: Parity multi-sig hack (2017) - $150M frozen
    # Critical functions missing onlyOwner modifier
    has_access_control_issues: bool = False
    
    # 🎓 TIMESTAMP DEPENDENCY: Logic depends on block.timestamp
    # Miners can manipulate timestamps by ~15 seconds
    # Example: Using timestamp for randomness (predictable!)
    has_timestamp_dependency: bool = False
    
    # 🎓 UNCHECKED CALL: Ignoring return value of external calls
    # Example: King of the Ether (2016) - funds stuck
    # transfer() fails but code continues executing
    has_unchecked_call: bool = False
    
    # ================================================================
    # SEVERITY COUNTS (How many issues of each severity)
    # ================================================================
    # 🎓 WHY COUNT SEVERITIES:
    # ML features: "Contract has 3 HIGH, 5 MEDIUM, 10 LOW issues"
    # Gives model sense of overall code quality
    # High severity = exploitable, Medium = bad practice, Low = info
    
    high_severity_count: int = 0    # Exploitable vulnerabilities
    medium_severity_count: int = 0  # Bad practices
    low_severity_count: int = 0     # Code smells, informational


class SlitherAnalyzer:
    """
    Extracts vulnerability features from Slither analysis results.
    
    🎓 DESIGN PATTERN: Adapter Pattern
    Translates Slither's format → Our feature format
    
    🎓 RESPONSIBILITY: Single Responsibility Principle
    This class does ONE thing: Extract vulnerability features
    It doesn't:
    - Compile contracts (Slither does that)
    - Extract AST features (ASTFeatureExtractor does that)
    - Save to CSV (FeaturePipeline does that)
    
    FIXED: Properly runs Slither detectors and extracts results
    """
    
    # ================================================================
    # CLASS-LEVEL CONSTANT: DETECTOR MAPPING
    # ================================================================
    # 🎓 WHY CLASS CONSTANT:
    # - Shared across all instances (saves memory)
    # - Defined once, used many times
    # - Easy to modify (change mapping in one place)
    # - Clearly documents which detectors we care about
    #
    # 🎓 MANY-TO-ONE MAPPING:
    # Problem: Slither has 93 detectors, we want 4 features
    # Solution: Map multiple detectors to same feature
    #
    # Example: 4 reentrancy detectors → 1 has_reentrancy feature
    # Why? ML model doesn't need to know reentrancy variant
    # Just: "Does this contract have reentrancy?" Yes/No
    # ================================================================
    
    DETECTOR_MAPPING = {
        # ============================================================
        # REENTRANCY VARIANTS (4 detectors → 1 feature)
        # ============================================================
        # 🎓 REENTRANCY TYPES:
        # - reentrancy-eth: Ether transfer in reentrancy
        # - reentrancy-no-eth: State change in reentrancy (no Ether)
        # - reentrancy-events: Event emission in reentrancy
        # - reentrancy-benign: Benign reentrancy (low risk)
        #
        # All map to: has_reentrancy = True
        'reentrancy-eth': 'has_reentrancy',
        'reentrancy-no-eth': 'has_reentrancy',
        'reentrancy-events': 'has_reentrancy',
        'reentrancy-benign': 'has_reentrancy',
        
        # ============================================================
        # ACCESS CONTROL ISSUES (4 detectors → 1 feature)
        # ============================================================
        # 🎓 ACCESS CONTROL TYPES:
        # - arbitrary-send-eth: Anyone can send Ether from contract
        # - arbitrary-send-erc20: Anyone can transfer tokens
        # - suicidal: Anyone can destroy contract
        # - unprotected-upgrade: Upgrade function lacks access control
        'arbitrary-send-eth': 'has_access_control_issues',
        'arbitrary-send-erc20': 'has_access_control_issues',
        'suicidal': 'has_access_control_issues',
        'unprotected-upgrade': 'has_access_control_issues',
        
        # ============================================================
        # TIMESTAMP DEPENDENCY (2 detectors → 1 feature)
        # ============================================================
        # 🎓 TIMESTAMP ISSUES:
        # - timestamp: Uses block.timestamp in logic
        # - weak-prng: Uses timestamp for randomness (predictable!)
        'timestamp': 'has_timestamp_dependency',
        'weak-prng': 'has_timestamp_dependency',
        
        # ============================================================
        # UNCHECKED CALLS (3 detectors → 1 feature)
        # ============================================================
        # 🎓 UNCHECKED CALL TYPES:
        # - unchecked-send: Ignores send() return value
        # - unchecked-lowlevel: Ignores call() return value
        # - low-level-calls: Uses call() instead of transfer()
        'unchecked-send': 'has_unchecked_call',
        'unchecked-lowlevel': 'has_unchecked_call',
        'low-level-calls': 'has_unchecked_call',
    }
    
    # 🎓 NOTE: 93 detectors, but we only map ~13
    # Why? Others are informational (naming, code style, etc.)
    # We focus on SECURITY vulnerabilities for ML training
    
    def __init__(self, slither: Slither):
        """
        Initialize with Slither object.
        
        🎓 DEPENDENCY INJECTION: Receive Slither object from caller
        Alternative: Create Slither inside this class
        Trade-off: Injection allows reusing compiled Slither object
        
        🎓 TYPE HINT: slither: Slither
        Tells IDE: "This parameter must be a Slither object"
        Benefits: Autocomplete, type checking, documentation
        
        Args:
            slither: Slither analysis object (already compiled)
        """
        # 🎓 INSTANCE VARIABLE: Store for use in other methods
        self.slither = slither
        
        # 🎓 LOGGING: Log initialization for debugging
        logger.info(f"Initialized SlitherAnalyzer for {slither.filename}")
    
    def extract_features(self, contract_name: str) -> ContractFeatures:
        """
        Extract vulnerability features from Slither detector results.
        
        🎓 THIS IS THE CORE LOGIC OF THIS CLASS
        
        🐛 BUG WE FIXED: Nested list structure
        Slither returns: List[List[Dict]], not List[Dict]!
        Example:
        [
            [{'check': 'reentrancy-eth', ...}],  # Detector 1 results
            [{'check': 'timestamp', ...}],        # Detector 2 results
            []                                     # Detector 3 (no findings)
        ]
        
        We must flatten: Outer loop (detectors) + Inner loop (findings)
        
        🎓 ALGORITHM:
        1. Run all detectors (slither.run_detectors())
        2. Flatten nested results
        3. For each finding:
           a. Extract detector name ('reentrancy-eth')
           b. Look up our feature name ('has_reentrancy')
           c. Set feature flag to True
           d. Count severity
        4. Return ContractFeatures object
        
        FIXED: Now properly runs detectors and extracts results
        
        How Slither Detectors Work:
        ---------------------------
        1. Slither loads contract AST (already done in __init__)
        2. run_detectors() executes all enabled detectors
        3. Returns nested list of dicts: [[{...}], [{...}], ...]
        
        Each finding dict contains:
        {
            'check': 'reentrancy-eth',          # Detector name
            'impact': 'High',                    # Severity
            'confidence': 'Medium',              # How sure Slither is
            'description': 'Reentrancy in withdraw()...',
            'elements': [...]                    # Code locations
        }
        
        Args:
            contract_name: Name of contract to analyze (e.g., "TetherToken")
        
        Returns:
            ContractFeatures object with filled-in vulnerability flags
        """
        # ================================================================
        # INITIALIZE FEATURES OBJECT
        # ================================================================
        # 🎓 DATACLASS CONSTRUCTION:
        # Must provide required fields (contract_name, file_path)
        # Optional fields default to False/0
        features = ContractFeatures(
            contract_name=contract_name,
            file_path=str(self.slither.filename)  # Path → str
        )
        
        logger.info(f"Running Slither detectors for {contract_name}...")
        
        # ================================================================
        # RUN DETECTORS - THE CRITICAL STEP!
        # ================================================================
        # 🎓 SLITHER API: run_detectors()
        # This executes all registered detectors
        # Returns: List[List[Dict]] (nested structure!)
        # ================================================================
        
        try:
            # 🎓 IMPORTANT: This actually executes all Slither detectors
            # Slither iterates through self.detectors list
            # Each detector analyzes contract and returns findings
            # Results are accumulated into nested list
            
            # 🎓 EXAMPLE RETURN VALUE:
            # [
            #   [  # Detector 1: reentrancy-eth
            #     {
            #       'check': 'reentrancy-eth',
            #       'impact': 'High',
            #       'confidence': 'Medium',
            #       'description': 'Reentrancy in withdraw()...',
            #       'elements': [...]
            #     }
            #   ],
            #   [  # Detector 2: timestamp
            #     {
            #       'check': 'timestamp',
            #       'impact': 'Low',
            #       'confidence': 'Medium',
            #       'description': 'Uses block.timestamp...',
            #       'elements': [...]
            #     }
            #   ],
            #   []  # Detector 3: No findings
            # ]
            detector_results = self.slither.run_detectors()
            
            # 🎓 LOGGING: Always log results count
            logger.info(f"Found {len(detector_results)} detector results")
            
            # 🎓 DEBUG LOGGING: Inspect first result to verify structure
            # Helps catch API changes or unexpected formats
            if detector_results:
                logger.debug(f"Sample result: {detector_results[0]}")
            
        except Exception as e:
            # 🎓 ERROR HANDLING: Don't crash on detector failure
            # Some detectors might fail on weird contracts
            logger.error(f"Failed to run detectors: {e}")
            detector_results = []  # Empty list = no findings
        
        # ================================================================
        # PROCESS EACH DETECTOR FINDING
        # ================================================================
        # 🐛 THE BUG: Slither returns List[List[Dict]], not List[Dict]
        # 
        # 🎓 FLATTENING STRATEGY:
        # Outer loop: Iterate detectors (detector_results)
        # Inner loop: Iterate findings per detector (detector_result)
        #
        # 🎓 WHY NESTED:
        # Slither groups findings by detector for reporting
        # We don't care about grouping, just all findings
        # ================================================================
        
        # 🎓 OUTER LOOP: Each detector's results
        for detector_result in detector_results:
            # ============================================================
            # DEFENSIVE PROGRAMMING: Handle both list and dict
            # ============================================================
            # 🎓 USUALLY: detector_result is a list
            # But some Slither versions return dict directly
            # We handle both cases to be safe
            
            if not isinstance(detector_result, list):
                # If it's a dict, wrap in list: {'check': ...} → [{'check': ...}]
                detector_result = [detector_result]
            
            # ============================================================
            # INNER LOOP: Each finding within detector results
            # ============================================================
            for result in detector_result:
                # ========================================================
                # VALIDATION: Ensure result is a dict
                # ========================================================
                # 🎓 TYPE CHECK: Result should be dict
                # If not, something is wrong with Slither output
                if not isinstance(result, dict):
                    logger.warning(f"Unexpected result type: {type(result)}")
                    continue  # Skip this result, try next
                
                # ========================================================
                # EXTRACT DETECTOR NAME AND SEVERITY
                # ========================================================
                # 🎓 DICT.GET(): Safe dictionary access
                # result.get('check') returns None if key missing
                # result['check'] would crash with KeyError
                #
                # 🎓 FALLBACK: result.get('check') or result.get('detector', '')
                # Different Slither versions use 'check' or 'detector'
                # We try both, default to empty string if neither exists
                check_name = result.get('check') or result.get('detector', '')
                impact = result.get('impact', '')  # 'High', 'Medium', 'Low', etc.
                
                # 🎓 DEBUG LOGGING: Track each finding
                # Helps verify detectors are actually running
                logger.debug(f"  → {check_name} (impact: {impact})")
                
                # ========================================================
                # MAP DETECTOR NAME TO FEATURE FLAG
                # ========================================================
                # 🎓 LOOKUP: Check if we care about this detector
                # Not all 93 detectors are mapped
                # We only map security-critical ones
                if check_name in self.DETECTOR_MAPPING:
                    # Get feature name from mapping
                    # Example: 'reentrancy-eth' → 'has_reentrancy'
                    feature_name = self.DETECTOR_MAPPING[check_name]
                    
                    # 🎓 SETATTR: Dynamic attribute setting
                    # setattr(obj, 'attr', value) = obj.attr = value
                    # Why dynamic? feature_name is a variable, not literal
                    # Can't write: features.feature_name = True
                    # Must write: setattr(features, feature_name, True)
                    setattr(features, feature_name, True)
                    
                    # 🎓 DEBUG: Confirm mapping worked
                    logger.debug(f"    Mapped to: {feature_name}")
                
                # ========================================================
                # COUNT SEVERITIES
                # ========================================================
                # 🎓 STRING NORMALIZATION: .lower()
                # Slither might return 'High', 'high', or 'HIGH'
                # We normalize to lowercase for consistent comparison
                impact_lower = impact.lower()
                
                # 🎓 SEVERITY BUCKETS:
                # High: Exploitable vulnerabilities
                # Medium: Bad practices, potential issues
                # Low/Informational: Code smells, style issues
                if impact_lower == 'high':
                    features.high_severity_count += 1
                elif impact_lower == 'medium':
                    features.medium_severity_count += 1
                elif impact_lower in ['low', 'informational']:
                    # 🎓 LIST MEMBERSHIP: Clean way to check multiple values
                    # Alternative: impact_lower == 'low' or impact_lower == 'informational'
                    features.low_severity_count += 1
        
        # ================================================================
        # LOG SUMMARY
        # ================================================================
        # 🎓 ALWAYS LOG RESULTS: Helps validate extraction worked
        logger.info(
            f"Extracted vulnerability features for {contract_name}: "
            f"{features.high_severity_count} high, "
            f"{features.medium_severity_count} medium, "
            f"{features.low_severity_count} low"
        )
        
        return features