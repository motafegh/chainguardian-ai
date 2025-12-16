"""
Base class for SmartBugs tool parsers

🎓 Design Pattern: Strategy Pattern + Template Method
Each tool has different JSON format, but same parsing workflow

Similar to Solidity:
abstract contract BaseParser {
    function parse() public virtual returns (Features);
}
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class BaseToolParser(ABC):
    """
    Abstract base class for tool report parsers.
    
    🎓 Why inheritance here?
    All tools have same workflow but different JSON formats:
    1. Load JSON file
    2. Parse tool-specific format
    3. Extract standard features
    4. Return feature dict
    
    Similar to ERC20:
    - Interface defines what methods exist (transfer, balanceOf)
    - Each implementation handles details differently
    """
    
    def __init__(self, report_path: Path):
        """
        Initialize parser with path to JSON report.
        
        Args:
            report_path: Path to tool's JSON output file
        """
        self.report_path = report_path
        self.tool_name = self.__class__.__name__.replace('Parser', '').lower()
    
    def parse(self) -> Dict:
        """
        Parse tool report and extract features.
        
        🎓 Template Method Pattern:
        Defines the algorithm skeleton, subclasses fill in details
        
        Returns:
            Dictionary with extracted features
        """
        try:
            # Step 1: Load JSON
            report_data = self._load_json()
            
            if not report_data:
                return self._get_empty_features()
            
            # Step 2: Check if tool ran successfully
            if not self._is_successful(report_data):
                logger.debug(f"{self.tool_name}: Tool execution failed")
                return self._get_empty_features()
            
            # Step 3: Extract features (subclass implements this)
            features = self._extract_features(report_data)
            
            # Step 4: Add metadata
            features[f'{self.tool_name}_executed'] = True
            features[f'{self.tool_name}_execution_time'] = report_data.get('execution_time')
            
            return features
            
        except Exception as e:
            logger.error(f"{self.tool_name} parse error: {e}")
            return self._get_empty_features()
    
    def _load_json(self) -> Optional[Dict]:
        """
        Load and parse JSON file.
        
        🎓 Common logic - same for all tools
        """
        try:
            if not self.report_path.exists():
                logger.debug(f"{self.tool_name}: Report not found: {self.report_path}")
                return None
            
            with open(self.report_path, 'r') as f:
                return json.load(f)
                
        except json.JSONDecodeError as e:
            logger.error(f"{self.tool_name}: Invalid JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"{self.tool_name}: Load error: {e}")
            return None
    
    @abstractmethod
    def _extract_features(self, report_data: Dict) -> Dict:
        """
        Extract features from parsed report.
        
        🎓 Abstract method - each subclass implements differently
        Each tool has different JSON structure
        
        Args:
            report_data: Parsed JSON report
            
        Returns:
            Dictionary with tool-specific features
        """
        pass
    
    @abstractmethod
    def _is_successful(self, report_data: Dict) -> bool:
        """
        Check if tool executed successfully.
        
        🎓 Each tool has different success indicator
        Mythril: "success": true
        Slither: "results" key exists
        etc.
        """
        pass
    
    @abstractmethod
    def _get_empty_features(self) -> Dict:
        """
        Return empty feature dict when tool fails.
        
        🎓 Each tool returns different features
        Must specify defaults for ML pipeline
        """
        pass


class VulnerabilityDetector:
    """
    Helper class to detect vulnerability types.
    
    🎓 Maps tool-specific names to standardized vulnerability types
    
    Example:
    - Mythril calls it "Reentrancy"
    - Slither calls it "reentrancy-eth"
    - Securify calls it "DAOConstantGas"
    
    All should map to: "reentrancy"
    """
    
    VULNERABILITY_MAPPINGS = {
        'reentrancy': [
            'reentrancy', 'reentrant', 'dao', 'call-loop',
            'reentrancy-eth', 'reentrancy-no-eth', 'reentrancy-benign'
        ],
        'access_control': [
            'access', 'unprotected', 'arbitrary-send', 'suicidal',
            'tx-origin', 'missing-protection', 'authorization'
        ],
        'arithmetic': [
            'integer', 'overflow', 'underflow', 'divide',
            'weak-prng', 'incorrect-shift'
        ],
        'timestamp': [
            'timestamp', 'time', 'block.timestamp', 'now',
            'time-manipulation'
        ],
        'unchecked_call': [
            'unchecked', 'low-level-calls', 'call-without-check',
            'send', 'call.value'
        ]
    }
    
    @classmethod
    def detect_vulnerability_type(cls, issue_name: str) -> Optional[str]:
        """
        Map tool-specific issue name to standard vulnerability type.
        
        Args:
            issue_name: Tool's name for the issue (e.g., "reentrancy-eth")
            
        Returns:
            Standardized type (e.g., "reentrancy") or None
        """
        issue_lower = issue_name.lower()
        
        for vuln_type, keywords in cls.VULNERABILITY_MAPPINGS.items():
            if any(keyword in issue_lower for keyword in keywords):
                return vuln_type
        
        return None