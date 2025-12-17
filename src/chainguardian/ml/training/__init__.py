"""
Vulnerability Classifier - Unified model interface.

Supports: Logistic Regression, Random Forest, XGBoost, Voting Ensemble
"""

from typing import Dict, Optional
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
import logging

logger = logging.getLogger(__name__)

class VulnerabilityClassifier:
    """Unified interface for all vulnerability detection models."""
    
    SUPPORTED_MODELS = ['logistic', 'random_forest', 'xgboost', 'ensemble']
    
    def __init__(self, model_type: str = 'random_forest', **kwargs):
        if model_type not in self.SUPPORTED_MODELS:
            raise ValueError(f"model_type must be one of {self.SUPPORTED_MODELS}")
        
        self.model_type = model_type
        self.model = self._create_model(**kwargs)
        self.feature_names = None
        self.is_fitted = False
        logger.info(f"Initialized {model_type} classifier")
    
    def _create_model(self, **kwargs) -> BaseEstimator:
        """Create model based on type."""
        
        if self.model_type == 'logistic':
            from sklearn.linear_model import LogisticRegression
            default_params = {
                'max_iter': 1000,
                'random_state': 42,
                'class_weight': 'balanced',
                'solver': 'lbfgs'
            }
            default_params.update(kwargs)
            return LogisticRegression(**default_params)
        
        elif self.model_type == 'random_forest':
            from sklearn.ensemble import RandomForestClassifier
            default_params = {
                'n_estimators': 100,
                'max_depth': 15,
                'min_samples_split': 5,
                'min_samples_leaf': 2,
                'random_state': 42,
                'class_weight': 'balanced',
                'n_jobs': -1
            }
            default_params.update(kwargs)
            return RandomForestClassifier(**default_params)
        
        elif self.model_type == 'xgboost':
            import xgboost as xgb
            default_params = {
                'n_estimators': 100,
                'max_depth': 6,
                'learning_rate': 0.1,
                'random_state': 42,
                'n_jobs': -1,
                'eval_metric': 'logloss'
            }
            default_params.update(kwargs)
            return xgb.XGBClassifier(**default_params)
        
        elif self.model_type == 'ensemble':
            from sklearn.ensemble import VotingClassifier
            from sklearn.linear_model import LogisticRegression
            from sklearn.ensemble import RandomForestClassifier
            import xgboost as xgb
            
            lr = LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced')
            rf = RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42, class_weight='balanced', n_jobs=-1)
            xgb_model = xgb.XGBClassifier(n_estimators=100, max_depth=6, random_state=42, n_jobs=-1)
            
            return VotingClassifier(
                estimators=[('lr', lr), ('rf', rf), ('xgb', xgb_model)],
                voting='soft',
                n_jobs=-1
            )
    
    def fit(self, X, y):
        """Train model."""
        if isinstance(X, pd.DataFrame):
            self.feature_names = list(X.columns)
        
        logger.info(f"Training {self.model_type} on {len(X)} samples...")
        self.model.fit(X, y)
        self.is_fitted = True
        logger.info(f"✓ Training complete")
        return self
    
    def predict(self, X):
        """Predict class labels."""
        if not self.is_fitted:
            raise ValueError("Model not fitted yet. Call fit() first.")
        return self.model.predict(X)
    
    def predict_proba(self, X):
        """Predict class probabilities."""
        if not self.is_fitted:
            raise ValueError("Model not fitted yet. Call fit() first.")
        return self.model.predict_proba(X)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores."""
        if not self.is_fitted:
            raise ValueError("Model not fitted yet")
        
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
        elif hasattr(self.model, 'coef_'):
            importances = np.abs(self.model.coef_[0])
        elif self.model_type == 'ensemble':
            rf_model = self.model.named_estimators_['rf']
            importances = rf_model.feature_importances_
        else:
            return {}
        
        if self.feature_names:
            return dict(zip(self.feature_names, importances))
        else:
            return {f"feature_{i}": imp for i, imp in enumerate(importances)}
