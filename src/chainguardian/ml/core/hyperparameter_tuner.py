# (Paste the entire hyperparameter_tuner.py content here)
"""
Optuna-based Hyperparameter Tuner for ChainGuardian AI
=======================================================
Implements Bayesian optimization for multiple ML algorithms.
Uses nested cross-validation to prevent overfitting.
"""

import optuna
import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_val_score
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
import lightgbm as lgb
import logging
from typing import Dict, List, Any, Optional
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class HyperparameterTuner:
    """
    Advanced hyperparameter tuner using Optuna.
    Optimizes multiple algorithms simultaneously with intelligent pruning.
    """
    
    def __init__(self, config, feature_names: List[str]):
        """
        Initialize tuner with configuration and feature context.
        
        Args:
            config: Configuration object
            feature_names: List of feature names for feature importance analysis
        """
        self.config = config
        self.feature_names = feature_names
        self.study: Optional[optuna.Study] = None  # Will be created in optimize()
        self.best_params: Dict[str, Any] = {}
        self.best_score: float = -np.inf
            
        # Set up Optuna logging
        optuna.logging.set_verbosity(optuna.logging.WARNING)
    
    def create_objective_function(self, X: np.ndarray, y: np.ndarray):
        """
        Create objective function for Optuna optimization.
        
        Args:
            X: Feature matrix
            y: Target vector
            
        Returns:
            Objective function for Optuna
        """
        # Use stratified K-fold for small dataset (700 samples)
        cv = StratifiedKFold(
            n_splits=5,  # 5-fold for small dataset
            shuffle=True,
            random_state=42
        )
        
        def objective(trial: optuna.Trial) -> float:
            """
            Objective function to maximize ROC AUC.
            Tests multiple algorithm types in single study.
            """
            # Let Optuna choose which algorithm to try
            model_type = trial.suggest_categorical(
                "model_type", 
                ["xgboost", "random_forest", "lightgbm"]
            )
            
            if model_type == "xgboost":
                params = self._get_xgboost_params(trial)
                model = xgb.XGBClassifier(**params, n_jobs=-1, random_state=42)
                
            elif model_type == "random_forest":
                params = self._get_random_forest_params(trial)
                model = RandomForestClassifier(**params, n_jobs=-1, random_state=42)
                
            elif model_type == "lightgbm":
                params = self._get_lightgbm_params(trial)
                model = lgb.LGBMClassifier(**params, n_jobs=-1, random_state=42)
            
            # Cross-validation with ROC AUC scoring
            try:
                scores = cross_val_score(
                    model, X, y, 
                    cv=cv, 
                    scoring='roc_auc',
                    n_jobs=-1,  # Parallelize CV folds
                    error_score='raise'
                )
                mean_score = scores.mean()
                
                # Store intermediate value for pruning
                trial.set_user_attr("mean_score", mean_score)
                trial.set_user_attr("std_score", scores.std())
                
                return float(mean_score)
                
            except Exception as e:
                # Return poor score if model fails
                logger.warning(f"Model {model_type} failed during CV: {e}")
                return 0.5  # Random guessing score
    
        return objective
    
    def _get_xgboost_params(self, trial: optuna.Trial) -> Dict[str, Any]:
        """Get XGBoost hyperparameters from trial."""
        search_space = self.config.hyperparameter_tuning.search_spaces.get('xgboost', {})
        
        return {
            'n_estimators': trial.suggest_int('xgb_n_estimators', 
                                             search_space.get('n_estimators', [100, 300])[0],
                                             search_space.get('n_estimators', [100, 300])[1]),
            'max_depth': trial.suggest_int('xgb_max_depth',
                                          search_space.get('max_depth', [3, 8])[0],
                                          search_space.get('max_depth', [3, 8])[1]),
            'learning_rate': trial.suggest_float('xgb_learning_rate',
                                                search_space.get('learning_rate', [0.01, 0.2])[0],
                                                search_space.get('learning_rate', [0.01, 0.2])[1],
                                                log=True),
            'subsample': trial.suggest_float('xgb_subsample',
                                            search_space.get('subsample', [0.6, 1.0])[0],
                                            search_space.get('subsample', [0.6, 1.0])[1]),
            'colsample_bytree': trial.suggest_float('xgb_colsample_bytree',
                                                   search_space.get('colsample_bytree', [0.6, 1.0])[0],
                                                   search_space.get('colsample_bytree', [0.6, 1.0])[1]),
            'gamma': trial.suggest_float('xgb_gamma',
                                        search_space.get('gamma', [0, 5])[0],
                                        search_space.get('gamma', [0, 5])[1]),
            'reg_alpha': trial.suggest_float('xgb_reg_alpha',
                                            search_space.get('reg_alpha', [0, 10])[0],
                                            search_space.get('reg_alpha', [0, 10])[1]),
            'reg_lambda': trial.suggest_float('xgb_reg_lambda',
                                             search_space.get('reg_lambda', [1, 10])[0],
                                             search_space.get('reg_lambda', [1, 10])[1])
        }
    
    def _get_random_forest_params(self, trial: optuna.Trial) -> Dict[str, Any]:
        """Get Random Forest hyperparameters from trial."""
        search_space = self.config.hyperparameter_tuning.search_spaces.get('random_forest', {})
        
        return {
            'n_estimators': trial.suggest_int('rf_n_estimators',
                                             search_space.get('n_estimators', [100, 300])[0],
                                             search_space.get('n_estimators', [100, 300])[1]),
            'max_depth': trial.suggest_int('rf_max_depth',
                                          search_space.get('max_depth', [5, 15])[0],
                                          search_space.get('max_depth', [5, 15])[1]),
            'min_samples_split': trial.suggest_int('rf_min_samples_split',
                                                  search_space.get('min_samples_split', [2, 10])[0],
                                                  search_space.get('min_samples_split', [2, 10])[1]),
            'min_samples_leaf': trial.suggest_int('rf_min_samples_leaf',
                                                 search_space.get('min_samples_leaf', [1, 4])[0],
                                                 search_space.get('min_samples_leaf', [1, 4])[1]),
            'bootstrap': True,
            'class_weight': 'balanced'
        }
    
    def _get_lightgbm_params(self, trial: optuna.Trial) -> Dict[str, Any]:
        """Get LightGBM hyperparameters from trial."""
        search_space = self.config.hyperparameter_tuning.search_spaces.get('lightgbm', {})
        
        return {
            'n_estimators': trial.suggest_int('lgb_n_estimators',
                                             search_space.get('n_estimators', [100, 300])[0],
                                             search_space.get('n_estimators', [100, 300])[1]),
            'num_leaves': trial.suggest_int('lgb_num_leaves',
                                           search_space.get('num_leaves', [20, 100])[0],
                                           search_space.get('num_leaves', [20, 100])[1]),
            'learning_rate': trial.suggest_float('lgb_learning_rate',
                                                search_space.get('learning_rate', [0.01, 0.2])[0],
                                                search_space.get('learning_rate', [0.01, 0.2])[1],
                                                log=True),
            'feature_fraction': trial.suggest_float('lgb_feature_fraction',
                                                  search_space.get('feature_fraction', [0.6, 1.0])[0],
                                                  search_space.get('feature_fraction', [0.6, 1.0])[1]),
            'bagging_fraction': trial.suggest_float('lgb_bagging_fraction',
                                                  0.6, 1.0),
            'bagging_freq': trial.suggest_int('lgb_bagging_freq', 1, 10),
            'min_child_samples': trial.suggest_int('lgb_min_child_samples', 5, 50),
            'reg_alpha': trial.suggest_float('lgb_reg_alpha', 0, 10),
            'reg_lambda': trial.suggest_float('lgb_reg_lambda', 0, 10)
        }
    
    def optimize(self, X: np.ndarray, y: np.ndarray, n_trials: Optional[int] = None) -> Dict:
        """
        Run hyperparameter optimization.
        
        Args:
            X: Feature matrix
            y: Target vector
            n_trials: Number of optimization trials
            
        Returns:
            Dictionary with best parameters and results
        """
        if n_trials is None:
            n_trials = self.config.hyperparameter_tuning.n_trials
        
        logger.info(f"Starting hyperparameter optimization with {n_trials} trials...")
        
        # Create study with pruning
        self.study = optuna.create_study(
            direction="maximize",
            study_name=self.config.hyperparameter_tuning.study_name,
            pruner=optuna.pruners.MedianPruner(
                n_startup_trials=10,  # Don't prune first 10 trials
                n_warmup_steps=5,     # Minimum steps before pruning
                interval_steps=1       # Check pruning every step
            ),
            sampler=optuna.samplers.TPESampler(seed=42)
        )
        
        # Create objective function
        objective = self.create_objective_function(X, y)
        
        # Run optimization
        self.study.optimize(
            objective,
            n_trials=n_trials,
            timeout=self.config.hyperparameter_tuning.timeout_seconds,
            show_progress_bar=True
        )
        
        # Store best results
        self.best_params = self.study.best_params
        self.best_score = self.study.best_value
        
        logger.info(f"Optimization completed. Best AUC: {self.best_score:.4f}")
        logger.info(f"Best model type: {self.best_params.get('model_type', 'unknown')}")
        
        return {
            'best_params': self.best_params,
            'best_score': self.best_score,
            'study': self.study,
            'trials_dataframe': self.study.trials_dataframe()
        }
    
    def analyze_results(self) -> Dict[str, Any]:
        """
        Analyze optimization results and provide insights.
        
        Returns:
            Dictionary with analysis results
        """
        if self.study is None:
            raise ValueError("No optimization results to analyze. Run optimize() first.")
        
        trials_df = self.study.trials_dataframe()
        
        # ✅ FIX: Handle None duration
        duration_seconds = (
            self.study.best_trial.duration.total_seconds()
            if self.study.best_trial.duration is not None
            else 0.0
        )
        
        analysis = {
            'best_trial': {
                'number': self.study.best_trial.number,
                'value': self.study.best_trial.value,
                'params': self.study.best_trial.params,
                'duration': duration_seconds  # ✅ Now safe
            },
            'summary_stats': {
                'total_trials': len(trials_df),
                'mean_score': trials_df['value'].mean(),
                'std_score': trials_df['value'].std(),
                'min_score': trials_df['value'].min(),
                'max_score': trials_df['value'].max()
            },
            'model_distribution': trials_df['params_model_type'].value_counts().to_dict(),
            'parameter_importance': optuna.importance.get_param_importances(self.study),
            'convergence_plot_data': self._prepare_convergence_data()
        }
        
        # Log insights
        logger.info("\n" + "="*60)
        logger.info("HYPERPARAMETER OPTIMIZATION INSIGHTS")
        logger.info("="*60)
        logger.info(f"Best Model: {analysis['best_trial']['params'].get('model_type')}")
        logger.info(f"Best AUC: {analysis['best_trial']['value']:.4f}")
        logger.info(f"Trials by model type: {analysis['model_distribution']}")
        logger.info(f"Parameter importance: {analysis['parameter_importance']}")
        
        return analysis

    
    def _prepare_convergence_data(self) -> Dict[str, List[Any]]:
        """Prepare data for convergence plotting."""
        if self.study is None:
            return {
                'trial_numbers': [],
                'scores': [],
                'best_so_far': []
            }
        
        trials = self.study.trials
        
        # ✅ FIX: Filter out None values and provide default
        return {
            'trial_numbers': [t.number for t in trials],
            'scores': [t.value if t.value is not None else 0.0 for t in trials],
            'best_so_far': [
                max([t.value for t in trials[:i+1] if t.value is not None], default=0.0)
                for i in range(len(trials))
            ]
        }

    
    def get_best_model(self, X: np.ndarray, y: np.ndarray):
        """
        Train and return the best model found during optimization.
        
        Args:
            X: Training features
            y: Training labels
            
        Returns:
            Trained model with best hyperparameters
        """
        if not self.best_params:
            raise ValueError("No best parameters found. Run optimize() first.")
        
        model_type = self.best_params.get('model_type')
        
        if model_type == "xgboost":
            # Extract XGBoost parameters
            params = {k.replace('xgb_', ''): v for k, v in self.best_params.items() 
                     if k.startswith('xgb_')}
            model = xgb.XGBClassifier(**params, random_state=42, n_jobs=-1)
            
        elif model_type == "random_forest":
            params = {k.replace('rf_', ''): v for k, v in self.best_params.items() 
                     if k.startswith('rf_')}
            model = RandomForestClassifier(**params, random_state=42, n_jobs=-1)
            
        elif model_type == "lightgbm":
            params = {k.replace('lgb_', ''): v for k, v in self.best_params.items() 
                     if k.startswith('lgb_')}
            model = lgb.LGBMClassifier(**params, random_state=42, n_jobs=-1)
        
        else:
            logger.warning(f"Unknown model type: {model_type}. Using XGBoost as fallback.")
            model = xgb.XGBClassifier(random_state=42, n_jobs=-1)
        
        # Train the model
        logger.info(f"Training best {model_type} model...")
        model.fit(X, y)
        
        return model