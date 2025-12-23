"""
ChainGuardian AI ML Package
===========================

Exposes ML models and utilities for vulnerability prediction.
"""

# Existing imports
from .models.hybrid_predictor import HybridPredictor
from .models.hybrid_predictor_enhanced import EnhancedHybridPredictor

# New imports from core modules
from .core.config_manager import ConfigManager, get_config
from .core.hyperparameter_tuner import HyperparameterTuner
from .core.heterogeneous_ensemble import HeterogeneousEnsemble
from .core.data_augmenter import SmartContractAugmenter
from .core.model_registry import ModelRegistry
from .core.monitoring import MLMonitor

# For backward compatibility - expose EnhancedHybridPredictorV2 as EnhancedHybridPredictor
try:
    from .models.hybrid_predictor_enhanced_v2 import EnhancedHybridPredictorV2
    EnhancedHybridPredictorV2 = EnhancedHybridPredictorV2
except ImportError:
    pass

__version__ = "2.0.0"
__all__ = [
    "HybridPredictor",
    "EnhancedHybridPredictor",
    "EnhancedHybridPredictorV2",
    "ConfigManager",
    "get_config",
    "HyperparameterTuner",
    "HeterogeneousEnsemble",
    "SmartContractAugmenter",
    "ModelRegistry",
    "MLMonitor"
]

print(f"✅ ChainGuardian AI ML Package v{__version__} loaded")
print("   Enhanced with: Hyperparameter tuning, Ensemble, Augmentation, Monitoring")
