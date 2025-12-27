"""
Production-Grade Feature Engineering
====================================
Creates advanced features through:
- Feature interactions (cei_violations × has_reentrancy)
- Ratios (external_calls / total_functions)
- Polynomial features (lines_of_code^2)
- Domain-specific features

Author: Ali
Date: December 22, 2024
"""

import pandas as pd
import numpy as np
from typing import List
from sklearn.preprocessing import PolynomialFeatures
import logging

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Advanced feature engineering for smart contract security.
    
    FEATURE TYPES:
    1. Interaction Features: product of related features
    2. Ratio Features: normalized metrics
    3. Polynomial Features: non-linear relationships
    4. Domain Features: security-specific patterns
    """
    
    def __init__(self, degree: int = 2):
        """
        Initialize feature engineer.
        
        Args:
            degree: Polynomial degree (default: 2 for quadratic)
        """
        self.degree = degree
        self.poly_transformer = None
        self.created_features: List[str] = []
    
    def create_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create interaction features between security indicators.
        
        EXAMPLES:
        - cei_violations × has_reentrancy → High risk if both present
        - state_after_call_count × num_external_calls → Reentrancy risk
        - has_unchecked_call × num_low_level_calls → Danger level
        
        WHY: Vulnerabilities often co-occur in patterns
        """
        logger.info("Creating interaction features...")
        
        interactions = {
            # CEI pattern interactions
            'cei_reentrancy_risk': 
                df['cei_violations'] * df.get('has_reentrancy', 0),
            
            'state_external_danger': 
                df['state_after_call_count'] * df['num_external_calls'],
            
            'unchecked_lowlevel_risk': 
                df.get('has_unchecked_call', 0) * df.get('num_low_level_calls', 0),
            
            # Complexity interactions
            'complexity_size_product': 
                df['max_cyclomatic_complexity'] * df['lines_of_code'],
            
            'functions_calls_interaction': 
                df['num_functions'] * df['num_external_calls'],
            
            # Detector interactions
            'high_severity_density': 
                df['high_severity_count'] * df['total_detector_hits'],
            
            # Guard effectiveness
            'guard_effectiveness': 
                df.get('has_reentrancy_guard', 0) * (1 - df['cei_pattern_score'])
        }
        
        for name, values in interactions.items():
            df[name] = values
            self.created_features.append(name)
        
        logger.info(f"   Created {len(interactions)} interaction features")
        return df
    
    def create_ratio_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create ratio features for normalization.
        
        EXAMPLES:
        - external_calls_ratio = external_calls / total_functions
        - complexity_per_loc = cyclomatic_complexity / lines_of_code
        - detector_density = total_detectors / lines_of_code
        
        WHY: Absolute counts misleading (100 LOC vs 10,000 LOC)
        """
        logger.info("Creating ratio features...")
        
        ratios = {
            # Call ratios
            'external_calls_ratio': 
                df['num_external_calls'] / (df['num_functions'] + 1),
            
            'low_level_calls_ratio': 
                df.get('num_low_level_calls', 0) / (df['num_external_calls'] + 1),
            
            # Complexity ratios
            'complexity_per_loc': 
                df['max_cyclomatic_complexity'] / (df['lines_of_code'] + 1),
            
            'avg_function_size': 
                df['lines_of_code'] / (df['num_functions'] + 1),
            
            # Detector ratios
            'detector_density': 
                df['total_detector_hits'] / (df['lines_of_code'] + 1),
            
            'high_severity_ratio': 
                df['high_severity_count'] / (df['total_detector_hits'] + 1),
            
            # CEI ratios
            'cei_violation_rate': 
                df['cei_violations'] / (df['num_functions'] + 1),
            
            'state_after_call_ratio': 
                df['state_after_call_count'] / (df['num_external_calls'] + 1)
        }
        
        for name, values in ratios.items():
            # Replace inf with large number, NaN with 0
            values = values.replace([np.inf, -np.inf], 999999).fillna(0)
            df[name] = values
            self.created_features.append(name)
        
        logger.info(f"   Created {len(ratios)} ratio features")
        return df
    
    def create_polynomial_features(
        self, 
        df: pd.DataFrame,
        key_features: List[str]
    ) -> pd.DataFrame:
        """
        Create polynomial features for non-linear relationships.
        
        EXAMPLE:
        - lines_of_code^2 → Quadratic growth in risk
        - cei_violations^2 → Exponential danger
        
        WHY: Risk doesn't scale linearly
        
        Args:
            key_features: List of features to polynomialize
        """
        logger.info(f"Creating polynomial features (degree={self.degree})...")
        
        # Select subset for polynomial expansion
        X_subset = df[key_features].fillna(0)
        
        # Initialize transformer
        if self.poly_transformer is None:
            self.poly_transformer = PolynomialFeatures(
                degree=self.degree,
                include_bias=False,
                interaction_only=False
            )
            poly_features = self.poly_transformer.fit_transform(X_subset)
        else:
            poly_features = self.poly_transformer.transform(X_subset)
        
        # Get feature names
        poly_names = self.poly_transformer.get_feature_names_out(key_features)
        
        # Add only new features (exclude originals)
        new_poly_names = [
            name for name in poly_names 
            if name not in key_features
        ]
        
        # Add to dataframe
        poly_df = pd.DataFrame(
            poly_features[:, len(key_features):],
            columns=new_poly_names,
            index=df.index
        )
        
        df = pd.concat([df, poly_df], axis=1)
        self.created_features.extend(new_poly_names)
        
        logger.info(f"   Created {len(new_poly_names)} polynomial features")
        return df
    
    def create_domain_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create domain-specific security features.
        
        BASED ON:
        - Security best practices
        - Historical vulnerability patterns
        - Audit experience
        """
        logger.info("Creating domain-specific features...")
        
        domain_features = {
            # Reentrancy risk score (weighted composite)
            'reentrancy_risk_score': (
                df['cei_violations'] * 0.4 +
                df['state_after_call_count'] * 0.3 +
                df.get('has_reentrancy', 0) * 10 +
                df.get('has_unchecked_call', 0) * 5 -
                df.get('has_reentrancy_guard', 0) * 15
            ),
            
            # Access control risk
            'access_control_risk': (
                df.get('has_access_control_issues', 0) * 10 +
                df.get('has_tx_origin', 0) * 8 +
                df.get('has_delegatecall_loop', 0) * 6
            ),
            
            # Code quality score (higher = better)
            'code_quality_score': (
                df.get('comment_to_code_ratio', 0) * 10 +
                (1 - df['max_cyclomatic_complexity'] / 100) * 5 +
                df.get('num_modifiers', 0) * 2 -
                df.get('num_unused_functions', 0) * 3
            ),
            
            # Contract maturity indicator
            'contract_maturity': (
                df.get('inheritance_depth', 0) * 2 +
                df.get('num_library_calls', 0) * 3 +
                df.get('num_comments', 0) / 10
            ),
            
            # Critical vulnerability flag (any high-severity pattern)
            'has_critical_pattern': (
                (df['cei_violations'] >= 2) |
                (df.get('has_reentrancy', 0) == 1) |
                (df['high_severity_count'] >= 3)
            ).astype(int)
        }
        
        for name, values in domain_features.items():
            df[name] = values
            self.created_features.append(name)
        
        logger.info(f"   Created {len(domain_features)} domain features")
        return df
    
    def engineer_features(
        self,
        df: pd.DataFrame,
        poly_features: List[str] = None
    ) -> pd.DataFrame:
        """
        Apply all feature engineering steps.
        
        Args:
            df: Input dataframe
            poly_features: Features for polynomial expansion
        
        Returns:
            DataFrame with engineered features
        """
        logger.info("\n" + "="*80)
        logger.info("FEATURE ENGINEERING PIPELINE")
        logger.info("="*80)
        
        initial_features = len(df.columns)
        
        # Step 1: Interactions
        df = self.create_interaction_features(df)
        
        # Step 2: Ratios
        df = self.create_ratio_features(df)
        
        # Step 3: Domain features
        df = self.create_domain_features(df)
        
        # Step 4: Polynomials (optional)
        if poly_features:
            df = self.create_polynomial_features(df, poly_features)
        
        final_features = len(df.columns)
        added = final_features - initial_features
        
        logger.info("\n✅ Feature Engineering Complete:")
        logger.info(f"   Initial features: {initial_features}")
        logger.info(f"   Final features:   {final_features}")
        logger.info(f"   Added:            {added}")
        logger.info(f"   Created features: {len(self.created_features)}")
        
        return df
    
    def get_feature_names(self) -> List[str]:
        """Return list of created feature names."""
        return self.created_features


# Example usage
if __name__ == "__main__":
    # Test feature engineering
    test_df = pd.DataFrame({
        'cei_violations': [0, 3, 1],
        'has_reentrancy': [0, 1, 0],
        'state_after_call_count': [0, 4, 2],
        'num_external_calls': [5, 10, 3],
        'lines_of_code': [100, 500, 200],
        'num_functions': [10, 25, 12],
        'max_cyclomatic_complexity': [5, 15, 8],
        'total_detector_hits': [2, 20, 5],
        'high_severity_count': [0, 3, 1]
    })
    
    engineer = FeatureEngineer()
    result = engineer.engineer_features(
        test_df,
        poly_features=['cei_violations', 'lines_of_code']
    )
    
    print(f"\nResult shape: {result.shape}")
    print(f"New features: {engineer.get_feature_names()[:5]}...")
