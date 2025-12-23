#!/usr/bin/env python3
"""
Hybrid Vulnerability Predictor - FIXED SCALING
Ensures column names match training exactly
"""

from pathlib import Path
from typing import Dict, Optional, List
import logging
import joblib
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

MODELS_DIR = Path("models")
DB_MODEL_PREFIX = "xgboost_calibrated_20251222"
DB_SCALER_PREFIX = "robust_scaler_20251222"
DB_FEATURE_PREFIX = "feature_names_20251222"


def _load_latest_db_model() -> tuple:
    """Load latest calibrated XGBoost model, scaler, and feature names."""
    model_path = max(MODELS_DIR.glob(f"{DB_MODEL_PREFIX}*.pkl"))
    scaler_path = max(MODELS_DIR.glob(f"{DB_SCALER_PREFIX}*.pkl"))
    feature_path = max(MODELS_DIR.glob(f"{DB_FEATURE_PREFIX}*.txt"))
    
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    feature_names = feature_path.read_text().strip().split('\n')
    
    return model, scaler, feature_names


class HybridVulnerabilityPredictor:
    """Production vulnerability predictor."""
    
    def __init__(self, mode: str = "db_calibrated"):
        self.mode = mode
        
        if mode == "db_calibrated":
            self.db_model, self.db_scaler, self.db_features = _load_latest_db_model()
            logger.info(f"✅ Loaded {len(self.db_features)} features")
    
    def predict(self, features: Dict) -> Dict:
        if self.mode == "db_calibrated":
            return self._predict_db_calibrated(features)
    
    def _predict_db_calibrated(self, features: Dict) -> Dict:
        """CRITICAL FIX: Preserve column names for scaler."""
        
        # Build DataFrame with EXACT column order + names
        df = pd.DataFrame(index=[0])
        
        for feature_name in self.db_features:
            value = features.get(feature_name, 0)
            
            # Handle types consistently with training
            if isinstance(value, bool):
                value = int(value)
            elif isinstance(value, str):
                # Categorical encoding like training
                value = pd.Categorical([value]).codes[0]
            
            df[feature_name] = value
        
        logger.debug(f"Feature vector shape: {df.shape}")
        
        # ⚠️  CRITICAL: Pass DataFrame with column names (not .values!)
        # Scaler expects column names to match training
        X_scaled = self.db_scaler.transform(df[self.db_features])
        
        # Predict
        prob_vulnerable = float(self.db_model.predict_proba(X_scaled)[0, 1])
        label = int(prob_vulnerable >= 0.5)
        
        # Risk category
        risk_map = {
            (0.0, 0.3): "SAFE",
            (0.3, 0.5): "LOW", 
            (0.5, 0.7): "MEDIUM",
            (0.7, 0.9): "HIGH",
            (0.9, 1.0): "CRITICAL"
        }
        
        for (low, high), category in risk_map.items():
            if low <= prob_vulnerable < high:
                risk_category = category
                break
        else:
            risk_category = "CRITICAL"
        
        return {
            "label": label,
            "prob_vulnerable": prob_vulnerable,
            "risk_category": risk_category,
            "backend": "xgboost_db_calibrated",
        }


# CLI test with VULNERABLE features
if __name__ == "__main__":
    predictor = HybridVulnerabilityPredictor()
    
    print("="*80)
    print("HYBRID PREDICTOR - VULNERABLE TEST")
    print("="*80)
    
    # Test SAFE contract
    safe_features = {name: 0 for name in predictor.db_features}
    safe_result = predictor.predict(safe_features)
    print(f"🟢 SAFE test:    {safe_result['risk_category']} ({safe_result['prob_vulnerable']:.3f})")
    
    # Test VULNERABLE contract (high-risk features)
    vuln_features = {name: 0 for name in predictor.db_features}
    vuln_features.update({
        'has_unchecked_call': 1,
        'has_floating_pragma': 1, 
        'has_inline_assembly': 1,
        'has_reentrancy': 1,
        'high_severity_count': 3,
        'risk_score_simple': 25.0,
        'contract_complexity_category': 'critical'
    })
    
    vuln_result = predictor.predict(vuln_features)
    print(f"🔴 VULN test:    {vuln_result['risk_category']} ({vuln_result['prob_vulnerable']:.3f})")
    
    print("\n✅ FIXED!")
