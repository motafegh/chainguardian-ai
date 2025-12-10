"""
Contract Feature Extraction Pipeline
Converts Solidity contracts into ML-ready feature vectors
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ContractFeatures:
    """
    Feature vector for a smart contract
    WHY: Structured data makes it easier to convert to pandas DataFrame later
    """
    # Metadata
    contract_name: str
    file_path: str
    
    # Slither detector results (vulnerability indicators)
    has_reentrancy: bool = False
    has_access_control_issues: bool = False
    has_timestamp_dependency: bool = False
    has_unchecked_call: bool = False
    
    # Counts from Slither detectors
    high_severity_count: int = 0
    medium_severity_count: int = 0
    low_severity_count: int = 0
    
    # Will add AST features next
    num_functions: int = 0
    num_external_calls: int = 0


class SlitherParser:
    """
    Parses Slither JSON output and extracts vulnerability flags
    """
    
    # Map Slither detector names to feature flags
    # Source: https://github.com/crytic/slither/wiki/Detector-Documentation
    DETECTOR_MAPPING = {
        'reentrancy-eth': 'has_reentrancy',
        'reentrancy-no-eth': 'has_reentrancy',
        'reentrancy-events': 'has_reentrancy',  # Added: low-severity variant
        'arbitrary-send-eth': 'has_access_control_issues',  # FIXED: was 'arbitrary-send'
        'arbitrary-send': 'has_access_control_issues',  # Keep old name for compatibility
        'suicidal': 'has_access_control_issues',
        'timestamp': 'has_timestamp_dependency',
        'weak-prng': 'has_timestamp_dependency',
        'unchecked-send': 'has_unchecked_call',
        'unchecked-lowlevel': 'has_unchecked_call',
        'low-level-calls': 'has_unchecked_call',  # Added: informational variant
    }
    
    def __init__(self, json_path: Path):
        """
        WHY: Load JSON once, parse multiple times if needed
        """
        self.json_path = json_path
        with open(json_path, 'r') as f:
            self.data = json.load(f)
        
        logger.info(f"Loaded Slither output from {json_path}")
    
    def extract_features(self, contract_name: str) -> ContractFeatures:
        """
        Extract binary vulnerability flags from Slither detectors
        
        WHY: Boolean features are simple but effective for initial ML models
        Research shows even basic flags achieve 75%+ accuracy (arxiv.org/abs/1908.09878)
        """
        features = ContractFeatures(
            contract_name=contract_name,
            file_path=str(self.json_path)
        )
        
        # Get detector results (array of findings)
        detectors = self.data.get('results', {}).get('detectors', [])
        
        for detection in detectors:
            check_name = detection.get('check', '')
            impact = detection.get('impact', '')
            
            # Set vulnerability flags
            if check_name in self.DETECTOR_MAPPING:
                feature_name = self.DETECTOR_MAPPING[check_name]
                setattr(features, feature_name, True)
            
            # Count severities (useful for risk scoring)
            if impact == 'High':
                features.high_severity_count += 1
            elif impact == 'Medium':
                features.medium_severity_count += 1
            elif impact == 'Low':
                features.low_severity_count += 1
        
        logger.info(f"Extracted features for {contract_name}: "
                   f"{features.high_severity_count} high, "
                   f"{features.medium_severity_count} medium, "
                   f"{features.low_severity_count} low severity issues")
        
        return features
