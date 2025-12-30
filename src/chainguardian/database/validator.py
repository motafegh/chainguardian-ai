# chainguardian/src/database/validator.py
"""
Data Validation Layer - Quality Control for ML Datasets

🎓 CRITICAL FOR ML SUCCESS:
"Garbage in, garbage out" - Your model is only as good as your training data!

This validator is the gatekeeper that prevents bad data from corrupting your dataset.

Why validation matters:
1. Type safety: Prevent runtime errors (e.g., float where int expected)
2. Range validation: Catch outliers (e.g., 1 million lines of code)
3. Missing data: Ensure required fields are present
4. Data quality: Flag suspicious values before they affect training

Think of this like input validation in smart contracts - you wouldn't deploy
a token contract without require() checks, so don't train ML models without
data validation!

PRODUCTION BEST PRACTICES:
- Validate at data ingestion (catch errors early)
- Log validation failures for debugging
- Track validation metrics (% of data rejected)
- Gradually tighten rules as you understand your data
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class FeatureValidator:
    """
    Validates feature dictionaries before database insertion.

    🎓 DEFENSE IN DEPTH:
    Similar to Solidity's require() statements at function entry:

    function transfer(address to, uint256 amount) public {
        require(to != address(0), "Invalid address");
        require(amount > 0, "Invalid amount");
        require(balanceOf[msg.sender] >= amount, "Insufficient balance");
        // ... rest of logic
    }

    This validator does the same for feature data:
    - Check required fields exist
    - Check types are correct
    - Check ranges are reasonable
    - Check files exist

    FAIL FAST: Better to reject bad data than to train on garbage!
    """
    
    # ========================================================================
    # VALIDATION RULES
    # ========================================================================

    # 🎓 Required fields: Contract MUST have these
    # Like constructor parameters in Solidity - can't create contract without them
    REQUIRED_FIELDS = ['contract_name', 'file_path']

    # 🎓 Type validation: Ensure Python types match expected types
    # Why? Prevents runtime errors when converting to SQL types
    # Example: If num_functions is a string "5", SQL INSERT will fail
    FIELD_TYPES = {
        # ========== Integers (counts, whole numbers) ==========
        'high_severity_count': int,
        'medium_severity_count': int,
        'low_severity_count': int,
        'num_functions': int,
        'lines_of_code': int,
        'cei_violations': int,
        'num_external_calls': int,

        # ========== Floats (scores, ratios, percentages) ==========
        'risk_score_simple': float,
        'risk_score_weighted': float,
        'cei_pattern_score': float,
        'avg_function_complexity': float,
        'comment_to_code_ratio': float,

        # ========== Booleans (yes/no flags) ==========
        'has_reentrancy': bool,
        'has_reentrancy_guard': bool,
        'is_high_risk': bool,
        'has_access_control_issues': bool,

        # ========== Strings (text data) ==========
        'contract_name': str,
        'failure_reason': str,
        'compiler_version': str,
    }
    
    def validate(self, features: Dict) -> List[str]:
        """
        Validate feature dictionary before database insertion.

        🎓 VALIDATION PIPELINE:
        1. Check required fields (existence check)
        2. Check types (type safety)
        3. Check ranges (business logic validation)
        4. Check file exists (referential integrity)

        Returns:
            List of error messages (empty list if valid)

        Example:
            validator = FeatureValidator()
            errors = validator.validate(feature_dict)
            if errors:
                print(f"Validation failed: {errors}")
            else:
                db.save_contract_and_features(feature_dict)
        """
        errors = []

        # ====================================================================
        # STEP 1: Required field validation
        # ====================================================================
        # 🎓 Like require() in Solidity - fail fast if critical data missing
        for field in self.REQUIRED_FIELDS:
            if field not in features:
                errors.append(f"Missing required field: {field}")

        # ====================================================================
        # STEP 2: Type validation
        # ====================================================================
        # 🎓 Prevent type errors before they hit the database
        # Example: lines_of_code="500" instead of 500 would cause SQL error
        for field, expected_type in self.FIELD_TYPES.items():
            if field in features:
                value = features[field]
                # Allow None values (nullable fields)
                if value is not None and not isinstance(value, expected_type):
                    errors.append(
                        f"Field {field} must be {expected_type.__name__}, "
                        f"got {type(value).__name__} (value: {value})"
                    )

        # ====================================================================
        # STEP 3: Range validation (business logic)
        # ====================================================================
        # 🎓 Catch suspicious outliers that indicate parsing errors

        # Lines of code sanity check
        if 'lines_of_code' in features:
            loc = features['lines_of_code']
            # Most contracts: 10-10,000 LOC
            # Extreme outliers (>100k) usually indicate parsing errors
            if loc < 0 or loc > 100000:
                errors.append(
                    f"Suspicious lines_of_code: {loc} "
                    "(expected 0-100,000, extreme values indicate parsing error)"
                )

        # Risk score validation (must be probability: 0-1)
        if 'risk_score_simple' in features:
            score = features['risk_score_simple']
            if score < 0 or score > 1:
                errors.append(
                    f"Risk score out of bounds [0,1]: {score} "
                    "(scores are probabilities, must be 0.0-1.0)"
                )

        # CEI pattern score validation
        if 'cei_pattern_score' in features:
            score = features['cei_pattern_score']
            if score < 0 or score > 1:
                errors.append(f"CEI pattern score out of bounds [0,1]: {score}")

        # Function count sanity check
        if 'num_functions' in features:
            count = features['num_functions']
            if count < 0 or count > 1000:
                errors.append(
                    f"Suspicious num_functions: {count} "
                    "(most contracts have 1-200 functions)"
                )

        # ====================================================================
        # STEP 4: File existence validation
        # ====================================================================
        # 🎓 Verify file path points to real file (referential integrity)
        if 'file_path' in features:
            from pathlib import Path
            file_path = features['file_path']
            if file_path and not Path(file_path).exists():
                errors.append(f"File not found: {file_path}")

        return errors
    
    def validate_and_log(self, features: Dict) -> bool:
        """
        Validate and log errors (convenience method).

        🎓 PRODUCTION USAGE:
        Use this method in production pipelines for automatic logging

        Args:
            features: Feature dictionary to validate

        Returns:
            True if valid, False if validation errors found

        Example:
            validator = FeatureValidator()
            if validator.validate_and_log(features_dict):
                db.save_contract_and_features(features_dict)
            else:
                # Errors already logged, skip this contract
                failed_contracts.append(features_dict['contract_name'])
        """
        errors = self.validate(features)

        if errors:
            contract_name = features.get('contract_name', 'unknown')
            logger.error(f"❌ Validation failed for contract: {contract_name}")
            for error in errors:
                logger.error(f"  - {error}")
            return False

        # Validation passed
        logger.debug(f"✅ Validation passed for: {features.get('contract_name', 'unknown')}")
        return True


# ============================================================================
# INTEGRATION EXAMPLE
# ============================================================================
# 🎓 How to integrate this validator into DatabaseManager:
#
# In manager.py, add to save_contract_and_features():
#
#     def save_contract_and_features(self, features_dict: Dict) -> int:
#         # Validate before saving
#         validator = FeatureValidator()
#         if not validator.validate_and_log(features_dict):
#             raise ValueError(f"Feature validation failed for {features_dict.get('contract_name')}")
#
#         # Proceed with saving (validation passed)
#         with self._get_cursor() as cursor:
#             # ... rest of save logic
#
# This ensures NO invalid data ever reaches the database!
# ============================================================================
