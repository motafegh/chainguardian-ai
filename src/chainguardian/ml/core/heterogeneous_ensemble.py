# (Paste the entire heterogeneous_ensemble.py content here)
"""
Heterogeneous Ensemble System for ChainGuardian AI
===================================================
Combines multiple ML algorithms with proper calibration and uncertainty estimation.
Implements Platt scaling (sigmoid) for better probability calibration on small datasets.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import VotingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import StratifiedKFold
from sklearn.base import BaseEstimator, ClassifierMixin
import joblib
import logging
from typing import Dict, List, Tuple, Optional, Any
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)
# ============================================================================
# MODULE-LEVEL FALLBACK CONFIGS (for pickle compatibility)
# ============================================================================

class HeterogeneousEnsemble(BaseEstimator, ClassifierMixin):
    """
    Advanced heterogeneous ensemble with:
    1. Multiple algorithm types
    2. Platt scaling calibration
    3. Bootstrap uncertainty estimation
    4. Dynamic weighting
    """
    
    def __init__(self, config, feature_names: List[str]):
        """
        Initialize ensemble system.
        
        Args:
            config: Configuration object
            feature_names: Feature names for interpretability
        """
        self.config = config
        self.feature_names = feature_names
        self.models = {}
        self.calibrated_models = {}
        self.is_fitted = False
        
        # FIX: Ensure config has required structure
        self._validate_and_fix_config()
        
        # Initialize base models
        self._initialize_models()
        
        logger.info("Heterogeneous Ensemble initialized")

    def _validate_and_fix_config(self):
        """Ensure config has all required attributes with proper defaults."""
        # Ensure ensemble config exists
        if not hasattr(self.config, 'ensemble'):
            logger.warning("No ensemble config found, creating defaults")
            from chainguardian.ml.core.config_manager import EnsembleConfig, CalibrationMethod
            self.config.ensemble = EnsembleConfig(
                enabled=True,
                calibration_method=CalibrationMethod.SIGMOID,
                initial_weights={
                    'xgboost': 0.4,
                    'random_forest': 0.3,
                    'lightgbm': 0.2,
                    'logistic_regression': 0.1
                }
            )
        
        # Ensure calibration_method is Enum
        if hasattr(self.config.ensemble, 'calibration_method'):
            if isinstance(self.config.ensemble.calibration_method, str):
                from chainguardian.ml.core.config_manager import CalibrationMethod
                try:
                    self.config.ensemble.calibration_method = CalibrationMethod(
                        self.config.ensemble.calibration_method.lower()
                    )
                except ValueError:
                    logger.warning("Invalid calibration method, using SIGMOID")
                    self.config.ensemble.calibration_method = CalibrationMethod.SIGMOID
        
        # Ensure uncertainty config exists (use proper dataclass!)
        if not hasattr(self.config.ensemble, 'uncertainty'):
            from chainguardian.ml.core.config_manager import UncertaintyConfig
            self.config.ensemble.uncertainty = UncertaintyConfig()  # ← Proper dataclass!
            logger.info("Created default uncertainty config")
        elif isinstance(self.config.ensemble.uncertainty, dict):
            # If loaded as dict from YAML, convert to dataclass
            from chainguardian.ml.core.config_manager import UncertaintyConfig
            self.config.ensemble.uncertainty = UncertaintyConfig(**self.config.ensemble.uncertainty)

    def _initialize_models(self):
        """Initialize base models with default or provided parameters."""
        # XGBoost
        self.models['xgboost'] = {
            'model': None,
            'weight': self.config.ensemble.initial_weights.get('xgboost', 0.4),
            'calibrated': False
        }
        
        # Random Forest
        self.models['random_forest'] = {
            'model': None,
            'weight': self.config.ensemble.initial_weights.get('random_forest', 0.3),
            'calibrated': False
        }
        
        # LightGBM
        self.models['lightgbm'] = {
            'model': None,
            'weight': self.config.ensemble.initial_weights.get('lightgbm', 0.2),
            'calibrated': False
        }
        
        # Logistic Regression (simple baseline)
        self.models['logistic_regression'] = {
            'model': None,
            'weight': self.config.ensemble.initial_weights.get('logistic_regression', 0.1),
            'calibrated': False
        }
    
    def fit(self, X: np.ndarray, y: np.ndarray, 
            sample_weight: Optional[np.ndarray] = None) -> 'HeterogeneousEnsemble':
        """
        Train the ensemble with individual model calibration.
        
        Args:
            X: Training features
            y: Training labels
            sample_weight: Optional sample weights
            
        Returns:
            Self for chaining
        """
        logger.info("Training heterogeneous ensemble...")
        # FIX: Store training data for later refitting
        self.X_train = X.copy()
        self.y_train = y.copy()
        # 1. Train individual models
        self._train_individual_models(X, y, sample_weight)
        
        # 2. Calibrate each model using Platt scaling (sigmoid)
        if self.config.ensemble.calibration_method.value == "sigmoid":
            self._calibrate_models(X, y)
        
        # 3. Create voting ensemble
        self._create_voting_ensemble()
        
        # 4. Train the voting ensemble
        self.ensemble.fit(X, y)
        
        self.is_fitted = True
        logger.info("Ensemble training completed")
        
        return self
    
    def _train_individual_models(self, X: np.ndarray, y: np.ndarray, 
                                 sample_weight: Optional[np.ndarray] = None):
        """Train each model type with appropriate parameters."""
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.linear_model import LogisticRegression
        import xgboost as xgb
        import lightgbm as lgb
        
        # XGBoost
        logger.info("  Training XGBoost...")
        xgb_model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1
        )
        xgb_model.fit(X, y, sample_weight=sample_weight)
        self.models['xgboost']['model'] = xgb_model
        
        # Random Forest
        logger.info("  Training Random Forest...")
        rf_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
            class_weight='balanced'
        )
        rf_model.fit(X, y, sample_weight=sample_weight)
        self.models['random_forest']['model'] = rf_model
        
        # LightGBM
        logger.info("  Training LightGBM...")
        lgb_model = lgb.LGBMClassifier(
            n_estimators=200,
            num_leaves=31,
            learning_rate=0.05,
            random_state=42,
            n_jobs=-1
        )
        lgb_model.fit(X, y, sample_weight=sample_weight)
        self.models['lightgbm']['model'] = lgb_model
        
        # Logistic Regression
        logger.info("  Training Logistic Regression...")
        lr_model = LogisticRegression(
            C=0.1,
            penalty='l1',
            solver='saga',
            random_state=42,
            max_iter=1000
        )
        lr_model.fit(X, y, sample_weight=sample_weight)
        self.models['logistic_regression']['model'] = lr_model
    
    def _calibrate_models(self, X: np.ndarray, y: np.ndarray):
        """
        Calibrate each model using Platt scaling (sigmoid).
        More appropriate for small datasets than isotonic regression.
        """
        logger.info("Calibrating models with Platt scaling...")
        
        # Use 5-fold CV for calibration
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        
        for name, model_info in self.models.items():
            if model_info['model'] is not None:
                logger.info(f"  Calibrating {name}...")
                
                # Use config's calibration method (now a proper Enum)
                calibration_method = self.config.ensemble.calibration_method.value  # Enum → string

                calibrated = CalibratedClassifierCV(
                    estimator=model_info['model'],
                    method=calibration_method,  # ← Uses config value
                    cv=cv,
                    n_jobs=-1
                )

                logger.info(f"   Using calibration: {calibration_method}")

                
                # Fit the calibrator
                calibrated.fit(X, y)
                
                # Store calibrated model
                self.calibrated_models[name] = calibrated
                model_info['calibrated'] = True
    
    def _create_voting_ensemble(self):
        """Create voting ensemble from calibrated models."""
        # Prepare estimators for VotingClassifier
        estimators = []
        for name, model_info in self.models.items():
            if model_info['calibrated'] and name in self.calibrated_models:
                estimators.append((name, self.calibrated_models[name]))
            elif model_info['model'] is not None:
                estimators.append((name, model_info['model']))
        
        # Create weights array
        weights = [self.models[name]['weight'] for name, _ in estimators]
        
        # Create voting ensemble
        self.ensemble = VotingClassifier(
            estimators=estimators,
            voting='soft',  # Weighted average of probabilities
            weights=weights,
            n_jobs=-1
        )
        
        logger.info(f"Created voting ensemble with {len(estimators)} models")
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict probabilities with uncertainty estimation.
        
        Args:
            X: Feature matrix
            
        Returns:
            Tuple of (mean_probabilities, uncertainty_estimates)
        """
        if not self.is_fitted:
            raise ValueError("Ensemble not fitted. Call fit() first.")
        
        # Get predictions from voting ensemble
        probas = self.ensemble.predict_proba(X)
        
        if self.config.ensemble.uncertainty.enable_bootstrap:
            uncertainty = self._estimate_uncertainty(X)
            return probas, uncertainty
        else:
            return probas, np.zeros((X.shape[0],))
    
    def _estimate_uncertainty(self, X: np.ndarray) -> np.ndarray:
        """
        Estimate prediction uncertainty using bootstrap.
        
        Args:
            X: Feature matrix
            
        Returns:
            Uncertainty estimates (standard deviation of predictions)
        """
        n_samples = X.shape[0]
        n_bootstrap = self.config.ensemble.uncertainty.n_bootstrap_samples
        
        # Store predictions from each bootstrap sample
        bootstrap_predictions = np.zeros((n_bootstrap, n_samples))
        
        # Simple bootstrap uncertainty estimation
        # In production, consider more sophisticated methods
        for i in range(n_bootstrap):
            # Get predictions from each model in ensemble
            model_predictions = []
            
            for name, model_info in self.models.items():
                if model_info['model'] is not None:
                    if model_info['calibrated']:
                        pred = self.calibrated_models[name].predict_proba(X)[:, 1]
                    else:
                        pred = model_info['model'].predict_proba(X)[:, 1]
                    model_predictions.append(pred)
            
            # Average predictions
            if model_predictions:
                bootstrap_predictions[i] = np.mean(model_predictions, axis=0)
        
        # Calculate uncertainty as standard deviation
        uncertainty = np.std(bootstrap_predictions, axis=0)
        
        return uncertainty
    
    def predict_with_uncertainty(self, X: np.ndarray, 
                                 threshold: float = 0.5) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Make predictions with confidence intervals.
        
        Args:
            X: Feature matrix
            threshold: Classification threshold
            
        Returns:
            Tuple of (predictions, probabilities, confidence_intervals)
        """
        probas, uncertainty = self.predict_proba(X)
        
        # Make binary predictions
        predictions = (probas[:, 1] > threshold).astype(int)
        
        # Calculate confidence intervals
        z_score = 1.96  # 95% confidence
        lower_bound = np.maximum(0, probas[:, 1] - z_score * uncertainty)
        upper_bound = np.minimum(1, probas[:, 1] + z_score * uncertainty)
        
        confidence_intervals = np.column_stack([lower_bound, upper_bound])
        
        return predictions, probas, confidence_intervals
    
    def get_model_contributions(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Get contribution of each model to final prediction.
        
        Args:
            X: Feature matrix
            
        Returns:
            Dictionary with model contributions
        """
        contributions = {}
        
        for name, model_info in self.models.items():
            if model_info['model'] is not None:
                if model_info['calibrated']:
                    pred = self.calibrated_models[name].predict_proba(X)[:, 1]
                else:
                    pred = model_info['model'].predict_proba(X)[:, 1]
                
                contributions[name] = pred * model_info['weight']
        
        return contributions
    
    def optimize_weights(self, X_val: np.ndarray, y_val: np.ndarray) -> Dict[str, float]:
        """
        Optimize ensemble weights on validation data.
        
        Args:
            X_val: Validation features
            y_val: Validation labels
            
        Returns:
            Optimized weights
        """
        from scipy.optimize import minimize
        
        # Get predictions from each model
        model_predictions = {}
        for name, model_info in self.models.items():
            if model_info['model'] is not None:
                if model_info['calibrated']:
                    pred = self.calibrated_models[name].predict_proba(X_val)[:, 1]
                else:
                    pred = model_info['model'].predict_proba(X_val)[:, 1]
                model_predictions[name] = pred
        
        # Objective function: minimize negative ROC AUC
        def objective(weights):
            # Normalize weights
            weights = np.maximum(weights, 0)
            weights = weights / weights.sum()
            
            # Weighted ensemble prediction
            weighted_pred = np.zeros_like(y_val, dtype=float)
            for i, (name, pred) in enumerate(model_predictions.items()):
                weighted_pred += weights[i] * pred
            
            # Calculate ROC AUC
            from sklearn.metrics import roc_auc_score
            try:
                auc = roc_auc_score(y_val, weighted_pred)
                return -auc  # Minimize negative AUC
            except:
                return 1.0  # Bad score if AUC calculation fails
        
        # Initial weights
        initial_weights = np.array([info['weight'] for info in self.models.values() 
                                   if info['model'] is not None])
        
        # Optimize
        bounds = [(0, 1) for _ in range(len(initial_weights))]
        result = minimize(objective, initial_weights, bounds=bounds, 
                         method='L-BFGS-B', options={'maxiter': 100})
        
        # Update weights
        optimized_weights = result.x / result.x.sum()
        
        # Map back to model names
        model_names = [name for name, info in self.models.items() 
                      if info['model'] is not None]
        
        new_weights = {}
        for i, name in enumerate(model_names):
            new_weights[name] = optimized_weights[i]
            self.models[name]['weight'] = optimized_weights[i]
        
        logger.info(f"Optimized weights: {new_weights}")
        
        # Recreate ensemble with new weights
        self._create_voting_ensemble()
        # FIX: Refit the voting classifier with the same training data
        # This is necessary because VotingClassifier needs to be fitted
        self.ensemble.fit(self.X_train, self.y_train)
        logger.info("Refitted ensemble with optimized weights")
        return new_weights
    
    def save(self, path: str):
        """Save ensemble to disk."""
        save_dict = {
            'models': self.models,
            'calibrated_models': self.calibrated_models,
            'ensemble': self.ensemble,
            'feature_names': self.feature_names,
            'is_fitted': self.is_fitted
        }
        joblib.dump(save_dict, path)
        logger.info(f"Ensemble saved to {path}")
    
    @classmethod
    def load(cls, path: str, config):
        """Load ensemble from disk."""
        data = joblib.load(path)
        
        # Create new instance
        ensemble = cls(config, data['feature_names'])
        ensemble.models = data['models']
        ensemble.calibrated_models = data['calibrated_models']
        ensemble.ensemble = data['ensemble']
        ensemble.is_fitted = data['is_fitted']
        
        logger.info(f"Ensemble loaded from {path}")
        return ensemble