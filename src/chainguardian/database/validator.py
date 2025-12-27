# chainguardian/src/database/validator.py
"""
Data Validation Layer

🎓 Validates feature dictionaries before database insertion
Prevents garbage data from corrupting your dataset
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class FeatureValidator:
    """
    Validates feature data before database insertion.
    
    🎓 Think of this like Solidity require() statements
    """
    
    REQUIRED_FIELDS = ['contract_name', 'file_path']
    
    # Type validation rules
    FIELD_TYPES = {
        # Integers
        'high_severity_count': int,
        'medium_severity_count': int,
        'low_severity_count': int,
        'num_functions': int,
        'lines_of_code': int,
        'cei_violations': int,
        
        # Floats
        'risk_score_simple': float,
        'risk_score_weighted': float,
        'cei_pattern_score': float,
        
        # Booleans
        'has_reentrancy': bool,
        'has_reentrancy_guard': bool,
        'is_high_risk': bool,
        
        # Strings
        'contract_name': str,
        'failure_reason': str,
    }
    
    def validate(self, features: Dict) -> List[str]:
        """
        Validate feature dictionary.
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # 1. Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in features:
                errors.append(f"Missing required field: {field}")
        
        # 2. Check types
        for field, expected_type in self.FIELD_TYPES.items():
            if field in features:
                value = features[field]
                if value is not None and not isinstance(value, expected_type):
                    errors.append(
                        f"Field {field} must be {expected_type.__name__}, "
                        f"got {type(value).__name__}"
                    )
        
        # 3. Check ranges
        if 'lines_of_code' in features:
            loc = features['lines_of_code']
            if loc < 0 or loc > 100000:
                errors.append(f"Suspicious lines_of_code: {loc}")
        
        if 'risk_score_simple' in features:
            score = features['risk_score_simple']
            if score < 0 or score > 1:
                errors.append(f"Risk score out of bounds [0,1]: {score}")
        
        # 4. Check file exists
        if 'file_path' in features:
            from pathlib import Path
            if not Path(features['file_path']).exists():
                errors.append(f"File not found: {features['file_path']}")
        
        return errors
    
    def validate_and_log(self, features: Dict) -> bool:
        """Validate and log errors."""
        errors = self.validate(features)
        
        if errors:
            logger.error(f"Validation failed for {features.get('contract_name', 'unknown')}:")
            for error in errors:
                logger.error(f"  - {error}")
            return False
        
        return True

# Add to DatabaseManager.save_contract_and_features():
# validator = FeatureValidator()
# if not validator.validate_and_log(features_dict):
#     raise ValueError("Feature validation failed")
