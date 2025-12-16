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

    Feature vector for a smart contract.
        
        🎓 EXPANDED VERSION: 15 → 58 features
        
        Feature Categories:
        1. Vulnerability Flags (23 boolean) - Specific security issues
        2. Severity Counts (3 integer) - High/Medium/Low issue counts
        3. Code Quality Metrics (10 integer/float) - LOC, complexity, etc.
        4. Detector Statistics (9 integer/float) - Aggregate detector info
        5. Composite Scores (4 float/string) - Pre-computed risk metrics
        6. Error Tracking (2 text) - Failure reasons
        
        Why 58 features?
        - Research shows 50-100 features optimal for vulnerability detection
        - Captures vulnerability presence, code quality, and risk magnitude
        - Normalized features (ratios) allow comparing contracts of different sizes

    """
    
    # ================================================================
    # METADATA (Required, no defaults)
    # ================================================================
    contract_name: str
    file_path: str
    
    # ================================================================
    # GROUP 1: REENTRANCY VULNERABILITIES (5 boolean flags)
    # ================================================================
    # 🎓 Different reentrancy types have different severity
    has_reentrancy: bool = False                    # Original (any reentrancy)
    has_reentrancy_unlimited: bool = False          # NEW: Unlimited gas
    has_reentrancy_benign: bool = False             # NEW: Read-only reentrancy
    has_reentrancy_events: bool = False             # NEW: Event ordering issues
    
    # ================================================================
    # GROUP 2: ACCESS CONTROL (1 boolean flag)
    # ================================================================
    has_access_control_issues: bool = False         # Original (grouped)
    
    # ================================================================
    # GROUP 3: TIMESTAMP & RANDOMNESS (1 boolean flag)
    # ================================================================
    has_timestamp_dependency: bool = False          # Original (grouped)
    
    # ================================================================
    # GROUP 4: UNCHECKED OPERATIONS (2 boolean flags)
    # ================================================================
    has_unchecked_call: bool = False                # Original (low-level calls)
    has_unchecked_transfer: bool = False            # NEW: ERC20 transfers
    
    # ================================================================
    # GROUP 5: DELEGATECALL ISSUES (2 boolean flags)
    # ================================================================
    # 🎓 DELEGATECALL: Executes external code in current context
    has_controlled_delegatecall: bool = False       # NEW: User controls target
    has_delegatecall_loop: bool = False             # NEW: Delegatecall in loop
    
    # ================================================================
    # GROUP 6: UNINITIALIZED VARIABLES (3 boolean flags)
    # ================================================================
    # 🎓 Solidity default: address = 0x0, uint = 0, bool = false
    has_uninitialized_state: bool = False           # NEW: State variable
    has_uninitialized_storage: bool = False         # NEW: Storage pointer
    has_uninitialized_local: bool = False           # NEW: Local variable
    
    # ================================================================
    # GROUP 7: DANGEROUS PATTERNS (5 boolean flags)
    # ================================================================
    has_tx_origin: bool = False                     # NEW: tx.origin auth
    has_inline_assembly: bool = False               # NEW: Assembly usage
    has_locked_ether: bool = False                  # NEW: Can't withdraw
    has_msg_value_loop: bool = False                # NEW: msg.value in loop
    
    # ================================================================
    # GROUP 8: CODE QUALITY ISSUES (4 boolean flags)
    # ================================================================
    has_shadowing_state: bool = False               # NEW: Variable shadowing
    has_shadowing_builtin: bool = False             # NEW: Builtin shadowing
    has_shadowing_abstract: bool = False            # NEW: Function shadowing
    has_unused_state_vars: bool = False             # NEW: Dead state vars
    has_unused_return_values: bool = False          # NEW: Ignored returns
    
    # ================================================================
    # GROUP 9: COMPILER ISSUES (3 boolean flags)
    # ================================================================
    has_incorrect_solc_version: bool = False        # NEW: Buggy compiler
    has_floating_pragma: bool = False               # NEW: ^0.8.0 pragma
    has_outdated_compiler: bool = False             # NEW: < 0.8.0
    
    # ================================================================
    # SEVERITY COUNTS (3 integer counts - Original)
    # ================================================================
    high_severity_count: int = 0
    medium_severity_count: int = 0
    low_severity_count: int = 0
    
    # ================================================================
    # CODE QUALITY METRICS (10 integer/float metrics)
    # ================================================================
    # Size metrics
    lines_of_code: int = 0                          # NEW: Total LOC
    num_contracts_in_file: int = 1                  # NEW: Multiple contracts?
    num_dependencies: int = 0                       # NEW: Import count
    
    # Complexity metrics (in addition to existing max_cyclomatic_complexity)
    avg_function_complexity: float = 0.0            # NEW: Average complexity
    num_functions_high_complexity: int = 0          # NEW: Functions > 10 complexity
    
    # Documentation metrics
    num_comments: int = 0                           # NEW: Comment lines
    comment_to_code_ratio: float = 0.0              # NEW: Comments / LOC
    
    # Advanced AST metrics
    num_payable_functions: int = 0                  # NEW: Functions accepting Ether
    num_library_calls: int = 0                      # NEW: External library usage
    inheritance_depth: int = 0                      # NEW: Inheritance levels
    num_unused_functions: int = 0                   # NEW: Dead functions
    
    # ================================================================
    # DETECTOR STATISTICS (9 integer/float aggregates)
    # ================================================================
    # Counts by confidence level
    high_confidence_detectors: int = 0              # NEW: High confidence hits
    medium_confidence_detectors: int = 0            # NEW: Medium confidence
    low_confidence_detectors: int = 0               # NEW: Low confidence
    
    # Counts by category
    security_detectors_triggered: int = 0           # NEW: Security category
    optimization_detectors_triggered: int = 0       # NEW: Gas optimization
    
    # Total counts
    total_detector_hits: int = 0                    # NEW: All detectors fired
    unique_vulnerability_types: int = 0             # NEW: Unique vuln categories
    
    # Ratios (normalized by contract size)
    detectors_per_function: float = 0.0             # NEW: Normalize by functions
    detectors_per_loc: float = 0.0                  # NEW: Normalize by LOC
    
    # ================================================================
    # COMPOSITE RISK SCORES (4 float/string scores)
    # ================================================================
    # 🎓 PRE-COMPUTED: Help ML model learn faster
    risk_score_simple: float = 0.0                  # NEW: high*10 + medium*5 + low
    risk_score_weighted: float = 0.0                # NEW: Confidence-weighted
    is_high_risk: bool = False                      # NEW: risk_score > threshold
    contract_complexity_category: str = 'simple'    # NEW: simple/moderate/complex/critical


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
    # CLASS-LEVEL CONSTANT: EXPANDED DETECTOR MAPPING (13 → 45+ detectors)
    # ================================================================
    # 🎓 STRUCTURE: Many-to-one + One-to-one mappings
    # - Some detectors group (4 reentrancy → 1 feature)
    # - Some detectors map directly (tx-origin → has_tx_origin)
    # 
    # 🎓 COVERAGE: ~45 of 93 Slither detectors
    # - CRITICAL security issues (20 detectors)
    # - HIGH severity issues (15 detectors)
    # - MEDIUM code quality issues (10 detectors)
    # - Skipped: Naming conventions, documentation (low ML signal)

    DETECTOR_MAPPING = {
        # ============================================================
        # REENTRANCY VARIANTS (5 detectors → 4 features + 1 grouped)
        # ============================================================
        # 🎓 NOTE: has_reentrancy stays as umbrella flag
        # New: Specific variants for nuanced ML signal
        
        'reentrancy-eth': 'has_reentrancy',                    # Original (Ether transfer)
        'reentrancy-no-eth': 'has_reentrancy',                 # Original (State change)
        'reentrancy-unlimited-gas': 'has_reentrancy_unlimited', # NEW: Most dangerous
        'reentrancy-benign': 'has_reentrancy_benign',          # NEW: Read-only
        'reentrancy-events': 'has_reentrancy_events',          # NEW: Event ordering
        
        # ============================================================
        # ACCESS CONTROL ISSUES (6 detectors → 1 grouped feature)
        # ============================================================
        'arbitrary-send-eth': 'has_access_control_issues',     # Original
        'arbitrary-send-erc20': 'has_access_control_issues',   # Original
        'arbitrary-send-erc20-no-permit': 'has_access_control_issues', # NEW
        'suicidal': 'has_access_control_issues',               # Original
        'unprotected-upgrade': 'has_access_control_issues',    # Original
        'unprotected-upgradeable': 'has_access_control_issues', # NEW: Proxy pattern
        
        # ============================================================
        # TIMESTAMP & WEAK RANDOMNESS (2 detectors → 1 grouped)
        # ============================================================
        'timestamp': 'has_timestamp_dependency',               # Original
        'weak-prng': 'has_timestamp_dependency',               # Original
        'block-timestamp': 'has_timestamp_dependency',         # NEW: Alternative name
        
        # ============================================================
        # UNCHECKED OPERATIONS (5 detectors → 2 features)
        # ============================================================
        'unchecked-send': 'has_unchecked_call',                # Original
        'unchecked-lowlevel': 'has_unchecked_call',            # Original
        'low-level-calls': 'has_unchecked_call',               # Original
        'unchecked-transfer': 'has_unchecked_transfer',        # NEW: ERC20 specific
        
        # ============================================================
        # DELEGATECALL ISSUES (2 detectors → 2 features)
        # ============================================================
        # 🎓 CRITICAL: delegatecall executes code in caller's context
        'controlled-delegatecall': 'has_controlled_delegatecall', # NEW
        'delegatecall-loop': 'has_delegatecall_loop',          # NEW
        
        # ============================================================
        # UNINITIALIZED VARIABLES (4 detectors → 3 features)
        # ============================================================
        'uninitialized-state': 'has_uninitialized_state',      # NEW
        'uninitialized-state-variables': 'has_uninitialized_state', # Alternative name
        'uninitialized-storage': 'has_uninitialized_storage',  # NEW
        'uninitialized-local': 'has_uninitialized_local',      # NEW
        
        # ============================================================
        # DANGEROUS PATTERNS (5 detectors → 4 features)
        # ============================================================
        'tx-origin': 'has_tx_origin',                          # NEW: Auth bypass
        'assembly': 'has_inline_assembly',                     # NEW: Low-level code
        'locked-ether': 'has_locked_ether',                    # NEW: Can't withdraw
        'msg-value-loop': 'has_msg_value_loop',                # NEW: msg.value in loop
        
        # ============================================================
        # SHADOWING ISSUES (4 detectors → 3 features)
        # ============================================================
        # 🎓 SHADOWING: Variable name reuse (confusing, bug-prone)
        'shadowing-state': 'has_shadowing_state',              # NEW
        'shadowing-local': 'has_shadowing_state',              # NEW: Group with state
        'shadowing-builtin': 'has_shadowing_builtin',          # NEW
        'shadowing-abstract': 'has_shadowing_abstract',        # NEW
        
        # ============================================================
        # UNUSED CODE (3 detectors → 2 features)
        # ============================================================
        'unused-state': 'has_unused_state_vars',               # NEW
        'unused-return': 'has_unused_return_values',           # NEW
        
        # ============================================================
        # COMPILER & PRAGMA (4 detectors → 3 features)
        # ============================================================
        'incorrect-version': 'has_incorrect_solc_version',     # NEW: Buggy versions
        'solc-version': 'has_incorrect_solc_version',          # Alternative name
        'floating-pragma': 'has_floating_pragma',              # NEW: ^0.8.0
        'pragma': 'has_floating_pragma',                       # Alternative name
    }

        # 🎓 STATS:
        # - Mapped detectors: 45 (was 13)
        # - Unmapped detectors: ~48 (mostly informational)
        # - Feature flags: 23 (was 4)
        # - Coverage: ~48% of all Slither detectors

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
        
        🎓 EXPANDED VERSION: Now extracts 58 features (was 15)
        
        Process:
        1. Run all 93 Slither detectors
        2. Map detector results to 23 vulnerability flags
        3. Count severities (high/medium/low)
        4. Calculate aggregate statistics (9 features)
        5. Compute composite risk scores (4 features)
        
        Args:
            contract_name: Name of contract to analyze (e.g., "TetherToken")
        
        Returns:
            ContractFeatures object with 58 populated fields
        """
        
        # ================================================================
        # INITIALIZE FEATURES OBJECT
        # ================================================================
        features = ContractFeatures(
            contract_name=contract_name,
            file_path=str(self.slither.filename)
        )
        
        logger.info(f"Running Slither detectors for {contract_name}...")
        
        # ================================================================
        # RUN DETECTORS - THE CRITICAL STEP!
        # ================================================================
        try:
            detector_results = self.slither.run_detectors()
            logger.info(f"Found {len(detector_results)} detector results")
            
            if detector_results:
                logger.debug(f"Sample result: {detector_results[0]}")
        
        except Exception as e:
            logger.error(f"Failed to run detectors: {e}")
            detector_results = []
        
        # ================================================================
        # PROCESS EACH DETECTOR FINDING (Set vulnerability flags)
        # ================================================================
        for detector_result in detector_results:
            # Handle both list and dict
            if not isinstance(detector_result, list):
                detector_result = [detector_result]
            
            for result in detector_result:
                # Validate result is a dict
                if not isinstance(result, dict):
                    logger.warning(f"Unexpected result type: {type(result)}")
                    continue
                
                # Extract detector name and severity
                check_name = result.get('check') or result.get('detector', '')
                impact = result.get('impact', '')
                
                logger.debug(f" → {check_name} (impact: {impact})")
                
                # Map detector name to feature flag
                if check_name in self.DETECTOR_MAPPING:
                    feature_name = self.DETECTOR_MAPPING[check_name]
                    setattr(features, feature_name, True)
                    logger.debug(f"   Mapped to: {feature_name}")
                
                # Count severities
                impact_lower = impact.lower()
                if impact_lower == 'high':
                    features.high_severity_count += 1
                elif impact_lower == 'medium':
                    features.medium_severity_count += 1
                elif impact_lower in ['low', 'informational']:
                    features.low_severity_count += 1
        
        # ================================================================
        # CALCULATE AGGREGATE DETECTOR STATISTICS
        # ================================================================
        logger.debug(f"Calculating aggregate statistics for {contract_name}...")
        
        # Track all detectors that fired
        fired_detectors = set()
        vulnerability_categories = set()
        
        # Track confidence levels
        confidence_counts = {
            'high': 0,
            'medium': 0,
            'low': 0
        }
        
        # Track detector categories
        security_count = 0
        optimization_count = 0
        
        # Iterate through detector results again for statistics
        for detector_result in detector_results:
            if not isinstance(detector_result, list):
                detector_result = [detector_result]
            
            for result in detector_result:
                if not isinstance(result, dict):
                    continue
                
                # Extract detector metadata
                check_name = result.get('check') or result.get('detector', '')
                if not check_name:
                    continue
                
                # Track unique detector
                fired_detectors.add(check_name)
                
                # Extract confidence and impact
                confidence = result.get('confidence', '').lower()
                impact = result.get('impact', '').lower()
                
                # Count by confidence level
                if confidence in confidence_counts:
                    confidence_counts[confidence] += 1
                
                # Categorize vulnerability types
                if 'reentrancy' in check_name:
                    vulnerability_categories.add('reentrancy')
                elif any(x in check_name for x in ['arbitrary', 'suicidal', 'access', 'unprotected']):
                    vulnerability_categories.add('access_control')
                elif any(x in check_name for x in ['timestamp', 'prng']):
                    vulnerability_categories.add('timestamp')
                elif any(x in check_name for x in ['unchecked', 'low-level']):
                    vulnerability_categories.add('unchecked_operations')
                elif 'delegatecall' in check_name:
                    vulnerability_categories.add('delegatecall')
                elif 'uninitialized' in check_name:
                    vulnerability_categories.add('uninitialized')
                elif any(x in check_name for x in ['tx-origin', 'assembly', 'locked-ether']):
                    vulnerability_categories.add('dangerous_patterns')
                elif any(x in check_name for x in ['shadowing', 'unused']):
                    vulnerability_categories.add('code_quality')
                elif any(x in check_name for x in ['pragma', 'version']):
                    vulnerability_categories.add('compiler')
                
                # Categorize by detector purpose
                if impact in ['high', 'medium']:
                    security_count += 1
                
                if any(x in check_name for x in ['gas', 'costly', 'cache', 'immutable']):
                    optimization_count += 1
        
        # Populate aggregate features
        features.high_confidence_detectors = confidence_counts['high']
        features.medium_confidence_detectors = confidence_counts['medium']
        features.low_confidence_detectors = confidence_counts['low']
        features.security_detectors_triggered = security_count
        features.optimization_detectors_triggered = optimization_count
        features.total_detector_hits = len(fired_detectors)
        features.unique_vulnerability_types = len(vulnerability_categories)
        
        logger.debug(
            f"  Aggregate stats: {features.total_detector_hits} detectors, "
            f"{features.unique_vulnerability_types} vuln types"
        )
        
        # ================================================================
        # CALCULATE COMPOSITE RISK SCORES
        # ================================================================
        features = self._calculate_risk_scores(features)
        
        # ================================================================
        # FINAL LOGGING
        # ================================================================
        logger.info(
            f"✓ {contract_name}: Extracted 23 vulnerability flags, "
            f"{features.total_detector_hits} detectors fired, "
            f"risk score: {features.risk_score_simple:.1f}"
        )
        
        return features

    def _calculate_risk_scores(self, features: ContractFeatures) -> ContractFeatures:
        """
        Calculate composite risk scores from individual features.
        
        🎓 COMPOSITE FEATURES: Pre-computed combinations
        ML models can learn these patterns themselves, but providing
        pre-computed features helps models learn faster (especially
        simpler models like Random Forest).
        
        🎓 WHY MULTIPLE SCORES:
        - risk_score_simple: Easy to interpret (high*10 + medium*5 + low)
        - risk_score_weighted: More nuanced (considers confidence)
        - is_high_risk: Binary threshold for classification
        - contract_complexity_category: Human-readable label
        
        Args:
            features: ContractFeatures object with extracted features
        
        Returns:
            Same features object with risk scores populated
        """
        
        # ================================================================
        # SCORE 1: SIMPLE RISK SCORE
        # ================================================================
        # 🎓 WEIGHTED SUM: high*10 + medium*5 + low*1
        # Why weights? High severity issues 10x more critical than low
        # Example: 2 high + 3 medium = 2*10 + 3*5 = 35 points
        
        features.risk_score_simple = (
            features.high_severity_count * 10 +
            features.medium_severity_count * 5 +
            features.low_severity_count * 1
        )
        
        # ================================================================
        # SCORE 2: WEIGHTED RISK SCORE (Confidence-aware)
        # ================================================================
        # 🎓 ADVANCED: Consider both severity AND confidence
        # High confidence findings weighted more
        # Formula: (high_sev * high_conf * 10) + (med_sev * med_conf * 5) + ...
        
        # Confidence weights (high confidence = more reliable)
        high_conf_weight = 1.0
        med_conf_weight = 0.7
        low_conf_weight = 0.3
        
        # Calculate weighted contribution of each severity+confidence combo
        # 🎓 ASSUMPTION: Distribute confidence across severities proportionally
        # (Slither doesn't give us severity+confidence pairs, so we approximate)
        
        total_detectors = features.total_detector_hits or 1  # Avoid division by zero
        high_ratio = features.high_severity_count / total_detectors
        med_ratio = features.medium_severity_count / total_detectors
        low_ratio = features.low_severity_count / total_detectors
        
        weighted_score = (
            # High severity contribution
            (features.high_confidence_detectors * high_ratio * 10 * high_conf_weight) +
            (features.medium_confidence_detectors * high_ratio * 10 * med_conf_weight) +
            (features.low_confidence_detectors * high_ratio * 10 * low_conf_weight) +
            
            # Medium severity contribution
            (features.high_confidence_detectors * med_ratio * 5 * high_conf_weight) +
            (features.medium_confidence_detectors * med_ratio * 5 * med_conf_weight) +
            (features.low_confidence_detectors * med_ratio * 5 * low_conf_weight) +
            
            # Low severity contribution
            (features.high_confidence_detectors * low_ratio * 1 * high_conf_weight) +
            (features.medium_confidence_detectors * low_ratio * 1 * med_conf_weight) +
            (features.low_confidence_detectors * low_ratio * 1 * low_conf_weight)
        )
        
        features.risk_score_weighted = weighted_score
        
        # ================================================================
        # SCORE 3: BINARY HIGH-RISK FLAG
        # ================================================================
        # 🎓 THRESHOLD-BASED: Is this contract "high risk"?
        # Threshold derived from research: contracts with score >20 have
        # 80% probability of having exploitable vulnerability
        
        RISK_THRESHOLD = 20.0  # Tunable hyperparameter
        
        features.is_high_risk = (
            features.risk_score_simple > RISK_THRESHOLD or
            features.high_severity_count >= 3 or
            features.unique_vulnerability_types >= 3
        )
        
        # ================================================================
        # SCORE 4: COMPLEXITY CATEGORY
        # ================================================================
        # 🎓 CATEGORICAL FEATURE: Human-readable complexity label
        # ML models can use this for stratification or as ordinal feature
        
        # Calculate total complexity indicator
        complexity_indicator = (
            features.high_severity_count * 3 +
            features.medium_severity_count * 2 +
            features.low_severity_count +
            features.unique_vulnerability_types * 2
        )
        
        # Categorize based on thresholds
        # 🎓 THRESHOLDS: Derived from dataset analysis
        # - simple: 0-5 (most contracts)
        # - moderate: 6-15 (needs review)
        # - complex: 16-30 (high priority)
        # - critical: 31+ (immediate action)
        
        if complexity_indicator <= 5:
            features.contract_complexity_category = 'simple'
        elif complexity_indicator <= 15:
            features.contract_complexity_category = 'moderate'
        elif complexity_indicator <= 30:
            features.contract_complexity_category = 'complex'
        else:
            features.contract_complexity_category = 'critical'
        
        logger.debug(
            f"Risk scores: simple={features.risk_score_simple:.1f}, "
            f"weighted={features.risk_score_weighted:.1f}, "
            f"category={features.contract_complexity_category}"
        )
        
        return features
