"""
Hybrid Predictor v5 - FIXED FOR FEATURE ALIGNMENT
=================================================
Automatically filters features to match trained model.

Key Fix: Feature alignment between input and model expectations

Author: Ali
Date: December 22, 2024
"""

import pandas as pd
import numpy as np
import joblib
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
import shap

logger = logging.getLogger(__name__)


class HybridPredictor:
    """
    Production hybrid predictor with automatic feature alignment.
    
    CRITICAL FIX:
    - Filters input features to match model's expected features
    - Handles missing features (fills with 0)
    - Handles extra features (ignores them)
    """
    
    def __init__(
        self,
        model_path: str = "models/production_model.pkl",
        scaler_path: str = "models/production_scaler.pkl",
        metadata_path: str = "models/feature_metadata.json",
        ml_weight: float = 0.3,
        semantic_weight: float = 0.7
    ):
        """
        Initialize hybrid predictor with automatic feature alignment.
        
        Args:
            model_path: Path to trained model
            scaler_path: Path to fitted scaler
            metadata_path: Path to feature metadata JSON
            ml_weight: Weight for ML predictions (default: 0.3)
            semantic_weight: Weight for semantic analysis (default: 0.7)
        """
        logger.info("Initializing HybridPredictor...")
        
        # Load model
        self.model = joblib.load(model_path)
        logger.info(f"   ✅ Loaded model from {model_path}")
        
        # Load scaler
        self.scaler = joblib.load(scaler_path)
        logger.info(f"   ✅ Loaded scaler from {scaler_path}")
        
        # Load metadata
        with open(metadata_path, 'r') as f:
            self.metadata = json.load(f)
        
        # Get expected feature names (what model was trained on)
        self.feature_names = self.metadata['feature_names']
        logger.info(f"   ✅ Model expects {len(self.feature_names)} features")
        
        # Weights
        self.ml_weight = ml_weight
        self.semantic_weight = semantic_weight
        
        # Override thresholds
        self.override_thresholds = {
            'high_cei_violations': 3,
            'perfect_cei_with_guard': True
        }
        
        # Initialize SHAP explainer
        try:
            # Get base estimator from calibrated model
            if hasattr(self.model, 'calibrated_classifiers_'):
                base_estimator = self.model.calibrated_classifiers_[0].estimator
            else:
                base_estimator = self.model
            
            self.shap_explainer = shap.TreeExplainer(base_estimator)
            logger.info(f"   ✅ SHAP explainer initialized")
        except Exception as e:
            logger.warning(f"   ⚠️  SHAP initialization failed: {e}")
            self.shap_explainer = None
        
        # Semantic analyzer weights
        self.semantic_weights = {
            'cei_violations': 0.40,
            'cei_score_low': 0.20,
            'state_after_call': 0.30,
            'unchecked_critical': 0.20,
            'reentrancy_guard_bonus': -0.50,
        }
    
    def _align_features(self, features: Dict[str, Any]) -> pd.DataFrame:
        """
        Align input features to match model's expected features.
        
        KEY FUNCTION:
        - Takes ANY feature dict
        - Filters to model's expected features
        - Fills missing features with 0
        - Returns DataFrame with EXACT feature order
        
        Args:
            features: Dictionary of features (may have 83, 93, or any count)
        
        Returns:
            DataFrame with exactly self.feature_names columns in correct order
        """
        # Create DataFrame with only expected features
        aligned_features = {}
        
        for feature_name in self.feature_names:
            if feature_name in features:
                aligned_features[feature_name] = features[feature_name]
            else:
                # Missing feature: fill with 0 (safe default)
                aligned_features[feature_name] = 0
                logger.debug(f"Missing feature '{feature_name}' filled with 0")
        
        # Create DataFrame with single row
        df = pd.DataFrame([aligned_features])
        
        # Ensure column order matches training
        df = df[self.feature_names]
        
        return df
    
    def _calculate_semantic_score(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate semantic risk score from CEI patterns.
        
        Returns dict with:
        - score: 0-1 risk score
        - cei_violations: count
        - findings: list of human-readable findings
        """
        # Extract semantic features (with defaults if missing)
        cei_violations = features.get('cei_violations', 0)
        cei_score = features.get('cei_pattern_score', 1.0)
        state_after_call = features.get('state_after_call_count', 0)
        unchecked_critical = features.get('unchecked_calls_in_critical_context', 0)
        has_guard = features.get('has_reentrancy_guard', 0)
        
        # Calculate weighted score
        score = 0.0
        findings = []
        
        # CEI violations
        if cei_violations > 0:
            weight = self.semantic_weights['cei_violations']
            contribution = cei_violations * weight / 10  # Normalize
            score += contribution
            findings.append(f"🚨 CEI violations: {cei_violations} (+{contribution*100:.0f}% risk)")
        
        # Low CEI score
        if cei_score < 0.7:
            weight = self.semantic_weights['cei_score_low']
            contribution = (1 - cei_score) * weight
            score += contribution
            findings.append(f"⚠️  Low CEI score: {cei_score:.2f} (+{contribution*100:.0f}% risk)")
        
        # State after call
        if state_after_call > 0:
            weight = self.semantic_weights['state_after_call']
            contribution = state_after_call * weight / 10
            score += contribution
            findings.append(f"🚨 State-after-call: {state_after_call} (+{contribution*100:.0f}% risk)")
        
        # Unchecked critical calls
        if unchecked_critical > 0:
            weight = self.semantic_weights['unchecked_critical']
            contribution = unchecked_critical * weight / 5
            score += contribution
            findings.append(f"⚠️  Unchecked critical: {unchecked_critical} (+{contribution*100:.0f}% risk)")
        
        # Reentrancy guard (reduces risk)
        if has_guard:
            weight = self.semantic_weights['reentrancy_guard_bonus']
            contribution = abs(weight)
            score += weight
            findings.append(f"✅ Reentrancy guard present (-{contribution*100:.0f}% risk)")
        
        # No issues found
        if not findings:
            findings.append("✅ No CEI violations detected")
        
        # Clamp score to [0, 1]
        score = max(0.0, min(1.0, score))
        
        return {
            'score': score,
            'cei_violations': cei_violations,
            'cei_pattern_score': cei_score,
            'state_after_call_count': state_after_call,
            'findings': findings
        }
    
    def _get_shap_explanations(self, X: pd.DataFrame, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Get SHAP feature contributions for prediction.
        
        Returns:
            List of dicts with feature name and contribution
        """
        if self.shap_explainer is None:
            return []
        
        try:
            # Calculate SHAP values
            shap_values = self.shap_explainer.shap_values(X.values)
            
            # Get values for class 1 (vulnerable)
            if isinstance(shap_values, list):
                shap_values = shap_values[1]
            
            # Create feature contribution list
            contributions = []
            for i, feature in enumerate(X.columns):
                contributions.append({
                    'feature': feature,
                    'contribution': float(shap_values[0, i])
                })
            
            # Sort by absolute contribution
            contributions.sort(key=lambda x: abs(x['contribution']), reverse=True)
            
            return contributions[:top_n]
        
        except Exception as e:
            logger.warning(f"SHAP explanation failed: {e}")
            return []
    
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hybrid prediction with automatic feature alignment.
        
        WORKFLOW:
        1. Align features to model expectations (83 → 72)
        2. Scale features
        3. ML prediction
        4. Semantic analysis
        5. Hybrid ensemble
        6. Override logic
        7. SHAP explanations
        
        Args:
            features: Dict with ANY number of features
        
        Returns:
            Complete prediction result with all components
        """
        # Step 1: Align features (CRITICAL FIX!)
        X = self._align_features(features)
        
        # Step 2: Scale
        X_scaled = self.scaler.transform(X.values)
        
        # Step 3: ML prediction
        ml_proba = self.model.predict_proba(X_scaled)[0, 1]
        
        # Step 4: Semantic analysis
        semantic_result = self._calculate_semantic_score(features)
        semantic_score = semantic_result['score']
        
        # Step 5: Hybrid ensemble
        hybrid_score = (self.ml_weight * ml_proba + 
                       self.semantic_weight * semantic_score)
        
        # Step 6: Check overrides
        override_triggered = False
        override_reason = None
        
        # Override: High CEI violations → Force vulnerable
        if semantic_result['cei_violations'] >= self.override_thresholds['high_cei_violations']:
            hybrid_score = 1.0
            override_triggered = True
            override_reason = f"OVERRIDE: {semantic_result['cei_violations']} CEI violations → VULNERABLE"
        
        # Override: Perfect CEI + guard → Force safe
        elif (semantic_result['cei_violations'] == 0 and 
              features.get('has_reentrancy_guard', 0) == 1 and
              semantic_result['cei_pattern_score'] > 0.9):
            hybrid_score = 0.0
            override_triggered = True
            override_reason = "OVERRIDE: Perfect CEI + guard → SAFE"
        
        # Step 7: Final prediction
        prediction_label = "VULNERABLE" if hybrid_score > 0.5 else "SAFE"
        
        # Risk level
        if hybrid_score > 0.95:
            risk_level = "CRITICAL"
        elif hybrid_score > 0.80:
            risk_level = "HIGH"
        elif hybrid_score > 0.60:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # Step 8: SHAP explanations
        shap_contributions = self._get_shap_explanations(X)
        
        # Build result
        result = {
            'prediction': {
                'label': prediction_label,
                'confidence': float(hybrid_score),
                'risk_level': risk_level,
                'method': 'OVERRIDE' if override_triggered else 'HYBRID'
            },
            'ml_analysis': {
                'score': float(ml_proba),
                'interpretation': f"Model detects {'vulnerable' if ml_proba > 0.5 else 'safe'} patterns"
            },
            'semantic_analysis': semantic_result,
            'explainability': {
                'method': 'SHAP',
                'top_risk_factors': shap_contributions
            }
        }
        
        if override_triggered:
            result['override'] = {
                'triggered': True,
                'reason': override_reason
            }
        
        return result


# Backward compatibility: copy to original location
import shutil
original_path = Path("src/chainguardian/ml/models/hybrid_predictor.py")
fixed_path = Path("src/chainguardian/ml/models/hybrid_predictor_v5_FIXED.py")

# Backup original
if original_path.exists():
    backup_path = Path("src/chainguardian/ml/models/hybrid_predictor_BACKUP.py")
    shutil.copy(original_path, backup_path)
    logger.info(f"Backed up original to {backup_path}")

# Copy fixed version
shutil.copy(fixed_path, original_path)
logger.info(f"Updated {original_path} with feature alignment fix")
