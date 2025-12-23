"""
ChainGuardian AI ML Package
===========================

Enhanced ML pipeline with:
- Hyperparameter tuning (Optuna)
- Heterogeneous ensemble
- Data augmentation
- Model registry
- Performance monitoring
- Batch prediction support
"""

from .config_manager import ConfigManager, get_config
from .hyperparameter_tuner import HyperparameterTuner
from .heterogeneous_ensemble import HeterogeneousEnsemble
from .data_augmenter import SmartContractAugmenter
from .model_registry import ModelRegistry
from .monitoring import MLMonitor
from chainguardian.ml.models.hybrid_predictor_enhanced_v2 import EnhancedHybridPredictorV2, EnhancedHybridPredictor

__version__ = "2.0.0"
__all__ = [
    "ConfigManager",
    "get_config",
    "HyperparameterTuner",
    "HeterogeneousEnsemble",
    "SmartContractAugmenter",
    "ModelRegistry",
    "MLMonitor",
    "EnhancedHybridPredictorV2",
    "EnhancedHybridPredictor"
]

print(f"✅ ChainGuardian AI ML Package v{__version__} loaded")
print("   Features: Hyperparameter tuning, Ensemble, Augmentation, Monitoring")