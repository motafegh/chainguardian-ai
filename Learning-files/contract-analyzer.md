"""
Contract Feature Extraction Pipeline  
Converts Solidity contracts into ML-ready feature vectors  

=== BIG PICTURE ===  
This code analyzes smart contracts for security vulnerabilities.  
Think of it like a virus scanner for blockchain code.  

Flow: Solidity Contract → Slither Tool → JSON Report → This Parser → ML Features  
"""

import json                     # Built-in library for handling JSON data (Slither's output format)
from pathlib import Path        # Modern, cross-platform way to handle file paths (safer than raw strings)
from typing import Dict, List, Optional  # Type hints: improve readability and catch bugs early
from dataclasses import dataclass       # Auto-generates common methods for data-only classes
import logging                  # Professional alternative to print(); supports log levels and filtering

# Configure logging to show messages of INFO severity and above (e.g., progress, warnings, errors)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # Logger scoped to this module (cleaner in larger projects)


@dataclass
# This is a data container (not a logic-heavy class).
# @dataclass saves us from writing repetitive code for:
#   • Constructor (__init__)
#   • Debug-friendly string representation (__repr__)
#   • Value-based equality comparison (__eq__)
# All fields are public and meant to be immutable after creation (unless explicitly modified).
class ContractFeatures:
    """
    Feature vector for a smart contract — a structured summary of security-relevant properties.
    
    In machine learning, raw code can't be used directly. Instead, we convert it into a 
    numeric "feature vector." This class is the blueprint for that vector, using simple 
    boolean flags and counts that ML models can learn from.
    """
    
    # --- METADATA (context about the contract, not used as ML features) ---
    contract_name: str   # e.g., "VulnerableBank" — helps identify the contract during debugging
    file_path: str       # Full path to the original Solidity file (useful for tracing issues)

    # --- BOOLEAN FEATURES (binary signals: 1 = vulnerability present, 0 = absent) ---
    # These capture high-impact security patterns. Even simple yes/no signals can be powerful for ML.
    has_reentrancy: bool = False
        # Reentrancy: function calls external code before updating internal state.
        # Example: withdraw() sends ETH before deducting balance → allows recursive re-entry.
        # Historic impact: The DAO hack (2016, ~$50M lost).

    has_access_control_issues: bool = False
        # Missing or weak access control: sensitive functions (e.g., selfdestruct, owner-only actions)
        # can be called by unauthorized users. A root cause of many exploits.

    has_timestamp_dependency: bool = False
        # Reliance on block.timestamp for critical logic (e.g., randomness, deadlines).
        # Risk: miners can manipulate timestamp by ~15 seconds → unfair outcomes in games/lotteries.

    has_unchecked_call: bool = False
        # ETH or low-level calls sent without checking return status.
        # Like mailing cash without confirmation — failure goes unnoticed.

    # --- COUNT-BASED FEATURES (numeric signals: how many issues of each severity?) ---
    # More issues generally correlate with higher risk. ML models can learn weighted combinations.
    high_severity_count: int = 0    # Critical bugs: direct fund loss or contract breakage
    medium_severity_count: int = 0  # Risky patterns: may become exploitable under certain conditions
    low_severity_count: int = 0     # Code quality issues (e.g., unused variables); not security-critical

    # --- PLACEHOLDER FEATURES (for future expansion) ---
    # These are initialized but not yet populated by the parser. Easy to extend later.
    num_functions: int = 0          # Total public/internal functions (proxy for complexity)
    num_external_calls: int = 0     # Calls to other contracts (higher = more attack surface)


class SlitherParser:
    """
    Translates Slither's JSON vulnerability report into a structured ContractFeatures object.
    
    Slither is a static analysis tool that scans Solidity code and outputs a JSON file listing
    detected issues. This class parses that output and maps Slither's detector names to our
    standardized security features.
    
    Analogy: Slither is the "doctor" diagnosing symptoms; this parser is the "lab technician"
    converting notes into a standardized patient chart.
    """

    # Maps Slither detector names → our standardized feature flags.
    # Why group multiple detectors under one flag?
    #   • Reentrancy has variants (with/without ETH, event-related) — all indicate the same core flaw.
    #   • Reduces noise and aligns with how ML models generalize patterns.
    DETECTOR_MAPPING = {
        # Reentrancy family — all indicate unsafe external call ordering
        'reentrancy-eth': 'has_reentrancy',
        'reentrancy-no-eth': 'has_reentrancy',
        'reentrancy-events': 'has_reentrancy',
        
        # Access control flaws — allow unauthorized actions
        'arbitrary-send-eth': 'has_access_control_issues',  # Can send contract's ETH to anyone
        'arbitrary-send': 'has_access_control_issues',      # Legacy name (still used in older Slither)
        'suicidal': 'has_access_control_issues',            # Anyone can selfdestruct the contract
        
        # Unsafe time/randomness usage
        'timestamp': 'has_timestamp_dependency',            # Uses block.timestamp unsafely
        'weak-prng': 'has_timestamp_dependency',            # Weak pseudo-random number generator
        
        # Unchecked external operations
        'unchecked-send': 'has_unchecked_call',             # ETH send without success check
        'unchecked-lowlevel': 'has_unchecked_call',         # Low-level call without return check
        'low-level-calls': 'has_unchecked_call',            # Informational — still indicates risk
    }

    def __init__(self, json_path: Path):
        """
        Load and parse Slither's JSON output file.
        
        We load the entire file once in __init__ (not during feature extraction) for efficiency:
        - If analyzing multiple contracts from one report, we avoid re-reading the disk.
        - Keeps parsing logic separate from I/O.
        """
        self.json_path = json_path
        # Use 'with' for safe file handling: file closes automatically, even if error occurs
        with open(json_path, 'r') as f:
            self.data = json.load(f)  # Converts JSON text → Python dict/list structure
        logger.info(f"Loaded Slither output from {json_path}")

    def extract_features(self, contract_name: str) -> ContractFeatures:
        """
        Extract security features for a specific contract from the Slither report.
        
        Core logic:
        1. Initialize an empty feature vector.
        2. Scan all detectors Slither triggered.
        3. For each detector:
            - If it matches our mapping, set the corresponding boolean flag to True.
            - Also tally severity counts (High/Medium/Low).
        4. Return the fully populated feature object.
        
        Why use setattr() instead of if/elif chains?
        - Cleaner, more maintainable code.
        - Adding new detectors only requires updating DETECTOR_MAPPING, not logic.
        """
        # Step 1: Create feature container with metadata
        features = ContractFeatures(
            contract_name=contract_name,
            file_path=str(self.json_path)
        )

        # Step 2: Safely navigate Slither's JSON structure
        # Use .get() to avoid KeyError if structure changes (defensive programming)
        detectors = self.data.get('results', {}).get('detectors', [])

        # Step 3: Process each detected issue
        for detection in detectors:
            check_name = detection.get('check', '')      # Slither's detector ID (e.g., "reentrancy-eth")
            impact = detection.get('impact', '')         # Severity level: "High", "Medium", or "Low"

            # Map detector to feature flag (if recognized)
            if check_name in self.DETECTOR_MAPPING:
                feature_name = self.DETECTOR_MAPPING[check_name]
                setattr(features, feature_name, True)    # Dynamically set has_xxx = True

            # Count issues by severity (useful for risk scoring or weighted models)
            if impact == 'High':
                features.high_severity_count += 1
            elif impact == 'Medium':
                features.medium_severity_count += 1
            elif impact == 'Low':
                features.low_severity_count += 1

        # Log summary for visibility during batch processing
        logger.info(
            f"Extracted features for {contract_name}: "
            f"{features.high_severity_count} high, "
            f"{features.medium_severity_count} medium, "
            f"{features.low_severity_count} low severity issues"
        )
        return features


# === TEST HARNESS ===
# Tests are critical for security tooling: if the parser misses a known bug,
# the entire ML pipeline becomes unreliable.
def test_vulnerable_bank():
    """
    End-to-end test using a contract with known vulnerabilities.
    
    Why test on VulnerableBank?
    - It's a canonical example with documented reentrancy and access control flaws.
    - If our parser doesn't flag these, the mapping or logic is broken.
    
    Note: This test assumes you've already run:
        slither blockchain/contracts/examples/VulnerableBank.sol --json slither_output.json
    """
    json_path = Path("slither_output.json")
    
    # Guard clause: prevent confusing errors if Slither hasn't been run
    if not json_path.exists():
        print("❌ Missing Slither output. Run:")
        print("   poetry run slither blockchain/contracts/examples/VulnerableBank.sol --json slither_output.json")
        return

    # Parse and extract
    parser = SlitherParser(json_path)
    features = parser.extract_features("VulnerableBank")

    # Display human-readable results
    print("\n🎯 Extracted Features:")
    print(f"  Reentrancy: {features.has_reentrancy}")
    print(f"  Access Control Issues: {features.has_access_control_issues}")
    print(f"  Timestamp Dependency: {features.has_timestamp_dependency}")
    print(f"  High Severity: {features.high_severity_count}")
    print(f"  Medium Severity: {features.medium_severity_count}")

    # Automated correctness checks — fail fast if assumptions are violated
    assert features.has_reentrancy, "VulnerableBank must trigger reentrancy detection!"
    assert features.has_access_control_issues, "VulnerableBank must have access control flaws!"

    print("\n✅ Parser works correctly!")


# === SCRIPT ENTRY POINT ===
# This ensures the test only runs when executing this file directly (not when imported as a module).
if __name__ == "__main__":
    test_vulnerable_bank()


"""
=== DESIGN TAKEAWAYS ===

1. **Separation of Concerns**  
   - Slither does static analysis.  
   - This parser does structured extraction.  
   - Future: a separate module will handle ML training.

2. **Extensibility**  
   - New detectors? Just add to DETECTOR_MAPPING.  
   - New features? Add fields to ContractFeatures + parsing logic.

3. **Defensive Programming**  
   - Use .get() instead of [] to avoid crashes on unexpected JSON.  
   - Asserts and logging catch issues early.

4. **ML Readiness**  
   - Boolean + integer features are ideal for most classifiers (e.g., Random Forest, XGBoost).  
   - Feature names are self-documenting for model interpretability.

This pipeline turns expert security knowledge (encoded in Slither) into data that machines can learn from.
"""