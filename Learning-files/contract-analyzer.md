"""
Contract Feature Extraction Pipeline
Converts Solidity contracts into ML-ready feature vectors

=== BIG PICTURE ===
This code analyzes smart contracts for security vulnerabilities.
Think of it like a virus scanner for blockchain code.

Flow: Solidity Contract → Slither Tool → JSON Report → This Parser → ML Features
"""

import json  # Python's built-in library for reading/writing JSON files
from pathlib import Path  # Modern way to handle file paths (better than strings)
from typing import Dict, List, Optional  # Type hints = documentation for what types functions expect
from dataclasses import dataclass  # Auto-generates __init__ and __repr__ methods
import logging  # Better than print() - can control what messages appear

# Configure logging
# level=logging.INFO means we'll see INFO, WARNING, and ERROR messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # Creates a logger specific to this module


@dataclass  # This decorator auto-creates an __init__ method from the variables below
class ContractFeatures:
    """
    Feature vector for a smart contract
    
    === WHAT IS A FEATURE VECTOR? ===
    In machine learning, we convert complex data (like code) into numbers.
    Example: "Has reentrancy bug? Yes=1, No=0"
    
    This class is like a form with checkboxes for different vulnerabilities.
    """
    # Metadata (information ABOUT the contract, not features FOR learning)
    contract_name: str  # e.g., "VulnerableBank"
    file_path: str  # Where the contract file lives
    
    # === BOOLEAN FLAGS (True/False features) ===
    # These are BINARY FEATURES - the simplest type for ML
    # Research shows: even simple yes/no questions can predict vulnerabilities!
    
    has_reentrancy: bool = False
    # REENTRANCY = when a function can be called again before it finishes
    # Famous example: The DAO hack ($50M stolen in 2016)
    # Like: withdraw() sends money BEFORE updating balance
    
    has_access_control_issues: bool = False
    # ACCESS CONTROL = who can call sensitive functions?
    # Bad: anyone can call selfdestruct() and delete the contract
    # Good: only the owner can call critical functions
    
    has_timestamp_dependency: bool = False
    # TIMESTAMP = using block.timestamp for critical logic
    # Problem: miners can manipulate timestamps by ~15 seconds
    # Dangerous in gambling/lottery contracts
    
    has_unchecked_call: bool = False
    # UNCHECKED CALL = sending ETH without checking if it succeeded
    # Like mailing a letter without tracking - you don't know if it arrived
    
    # === COUNT FEATURES (Integer features) ===
    # Instead of yes/no, these count HOW MANY issues exist
    # More issues = more dangerous contract (usually)
    
    high_severity_count: int = 0
    # High = can steal funds or break contract
    medium_severity_count: int = 0
    # Medium = risky but not immediately exploitable
    low_severity_count: int = 0
    # Low = code quality issues, not security critical
    
    # Placeholder features (not implemented yet in this version)
    num_functions: int = 0  # How many functions in the contract?
    num_external_calls: int = 0  # How many times does it call other contracts?


class SlitherParser:
    """
    Parses Slither JSON output and extracts vulnerability flags
    
    === WHAT IS SLITHER? ===
    Slither is a popular tool that analyzes Solidity code for bugs.
    It outputs a JSON file listing all the problems it found.
    This class READS that JSON and converts it to our feature format.
    
    Analogy: Slither is like spell-check, this parser reads the report.
    """
    
    # === CLASS VARIABLE (shared by all instances) ===
    # This dictionary maps Slither's detector names → our feature names
    # WHY? Slither has 90+ detectors, we group related ones together
    DETECTOR_MAPPING = {
        # REENTRANCY FAMILY (3 variants of the same vulnerability)
        'reentrancy-eth': 'has_reentrancy',  # Reentrancy that can steal ETH
        'reentrancy-no-eth': 'has_reentrancy',  # Reentrancy without ETH (still bad)
        'reentrancy-events': 'has_reentrancy',  # Low-severity: just emits events wrong
        
        # ACCESS CONTROL FAMILY
        'arbitrary-send-eth': 'has_access_control_issues',  # Anyone can send contract's ETH
        'arbitrary-send': 'has_access_control_issues',  # Old name, keep for compatibility
        'suicidal': 'has_access_control_issues',  # Anyone can destroy contract
        
        # RANDOMNESS/TIMING FAMILY
        'timestamp': 'has_timestamp_dependency',  # Uses block.timestamp unsafely
        'weak-prng': 'has_timestamp_dependency',  # Bad random number generator
        
        # UNCHECKED OPERATIONS FAMILY
        'unchecked-send': 'has_unchecked_call',  # Sends ETH without checking success
        'unchecked-lowlevel': 'has_unchecked_call',  # Low-level call without checking
        'low-level-calls': 'has_unchecked_call',  # Informational: just notifies about calls
    }
    
    def __init__(self, json_path: Path):
        """
        Constructor: loads the JSON file into memory
        
        WHY load in __init__?
        - If we have 100 contracts, we load once and parse 100 times
        - Faster than re-reading the file each time
        
        Args:
            json_path: Path to Slither's JSON output file
        """
        self.json_path = json_path  # Store the path (useful for debugging)
        
        # Open and parse the JSON file
        # 'with' statement ensures file is closed even if error occurs
        with open(json_path, 'r') as f:
            self.data = json.load(f)  # Converts JSON string → Python dictionary
        
        # Log that we successfully loaded the file
        logger.info(f"Loaded Slither output from {json_path}")
    
    def extract_features(self, contract_name: str) -> ContractFeatures:
        """
        Extract binary vulnerability flags from Slither detectors
        
        === THE CORE ALGORITHM ===
        1. Create empty feature object
        2. Loop through each bug Slither found
        3. If bug matches our mapping, flip the flag to True
        4. Count how many high/medium/low severity bugs
        
        WHY boolean features?
        - Simplest representation for machine learning
        - Research shows 75%+ accuracy even with basic features
        - Easy to interpret: "This contract HAS reentrancy" is clear
        
        Args:
            contract_name: Name of contract to analyze (e.g., "VulnerableBank")
            
        Returns:
            ContractFeatures object with all flags set
        """
        # Step 1: Create empty feature container
        features = ContractFeatures(
            contract_name=contract_name,
            file_path=str(self.json_path)
        )
        
        # Step 2: Navigate the JSON structure
        # Slither JSON format: { "results": { "detectors": [ {...}, {...} ] } }
        # .get() is safer than [] because it returns None instead of crashing
        detectors = self.data.get('results', {}).get('detectors', [])
        
        # Step 3: Loop through each detection (each bug Slither found)
        for detection in detectors:
            # Extract relevant fields from this detection
            check_name = detection.get('check', '')  # e.g., "reentrancy-eth"
            impact = detection.get('impact', '')  # e.g., "High", "Medium", "Low"
            
            # === FEATURE FLAG SETTING ===
            # Check if this detector maps to one of our features
            if check_name in self.DETECTOR_MAPPING:
                # Get the feature name (e.g., 'has_reentrancy')
                feature_name = self.DETECTOR_MAPPING[check_name]
                
                # setattr() dynamically sets object attributes
                # Equivalent to: features.has_reentrancy = True
                # WHY dynamic? So we don't need 10+ if/elif statements
                setattr(features, feature_name, True)
            
            # === SEVERITY COUNTING ===
            # Count each severity level (useful for risk scoring later)
            # Machine learning can learn: "10 medium bugs = 1 high bug"
            if impact == 'High':
                features.high_severity_count += 1
            elif impact == 'Medium':
                features.medium_severity_count += 1
            elif impact == 'Low':
                features.low_severity_count += 1
        
        # Step 4: Log what we found (helpful for debugging)
        logger.info(f"Extracted features for {contract_name}: "
                   f"{features.high_severity_count} high, "
                   f"{features.medium_severity_count} medium, "
                   f"{features.low_severity_count} low severity issues")
        
        return features


# === TEST FUNCTION ===
# Good practice: always include tests to verify code works!
def test_vulnerable_bank():
    """
    Test the parser on a known vulnerable contract
    
    === TESTING PHILOSOPHY ===
    We test on VulnerableBank because we KNOW it has bugs.
    If parser doesn't detect them, something is wrong!
    """
    json_path = Path("slither_output.json")
    
    # Safety check: does the file exist?
    if not json_path.exists():
        print("❌ Run Slither first: poetry run slither blockchain/contracts/examples/VulnerableBank.sol --json slither_output.json")
        return
    
    # Step 1: Create parser and load JSON
    parser = SlitherParser(json_path)
    
    # Step 2: Extract features for our test contract
    features = parser.extract_features("VulnerableBank")
    
    # Step 3: Display results in human-readable format
    print("\n🎯 Extracted Features:")
    print(f"  Reentrancy: {features.has_reentrancy}")
    print(f"  Access Control Issues: {features.has_access_control_issues}")
    print(f"  Timestamp Dependency: {features.has_timestamp_dependency}")
    print(f"  High Severity: {features.high_severity_count}")
    print(f"  Medium Severity: {features.medium_severity_count}")
    
    # Step 4: ASSERT statements = automated tests
    # If these fail, the program crashes (that's good! It means we caught a bug)
    assert features.has_reentrancy, "Should detect reentrancy!"
    assert features.has_access_control_issues, "Should detect access control!"
    
    print("\n✅ Parser works correctly!")


# === ENTRY POINT ===
# This block only runs when you execute this file directly
# (not when you import it as a module)
if __name__ == "__main__":
    test_vulnerable_bank()


"""
=== NEXT STEPS (How this fits into a larger system) ===

1. Feature Extraction (THIS CODE)
   - Input: Slither JSON report
   - Output: ContractFeatures object

2. Feature Engineering (Next step)
   - Convert ContractFeatures → pandas DataFrame
   - Add more features: AST analysis, code complexity, etc.

3. Model Training
   - Use DataFrame to train ML models (Random Forest, Neural Networks)
   - Learn patterns: "Contracts with reentrancy + unchecked calls = 90% vulnerable"

4. Prediction
   - New contract → Extract features → Model predicts: "70% chance vulnerable"

=== KEY CONCEPTS REVIEW ===
- Dataclass: Auto-generates boilerplate code
- Type hints: Document what types functions expect
- Logging: Better than print() for production code
- JSON parsing: .get() is safer than []
- setattr(): Dynamically set object attributes
- assert: Automated testing - crash if assumptions violated
"""