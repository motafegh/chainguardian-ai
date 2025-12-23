"""
ChainGuardian AI ML Package
===========================

Exposes ML models and utilities for vulnerability prediction.
"""

# Existing imports
from chainguardian.ml.models.hybrid_predictor import HybridPredictor
from chainguardian.ml.models.hybrid_predictor_enhanced import EnhancedHybridPredictor

# New imports from core modules
from chainguardian.ml.core.config_manager import ConfigManager, get_config
from chainguardian.ml.core.hyperparameter_tuner import HyperparameterTuner
from chainguardian.ml.core.heterogeneous_ensemble import HeterogeneousEnsemble
from chainguardian.ml.core.data_augmenter import SmartContractAugmenter
from chainguardian.ml.core.model_registry import ModelRegistry
from chainguardian.ml.core.monitoring import MLMonitor
from chainguardian.ml.models.hybrid_predictor_enhanced_v2 import EnhancedHybridPredictorV2
# For backward compatibility - expose EnhancedHybridPredictorV2 as EnhancedHybridPredictor
try:
    from chainguardian.ml.models.hybrid_predictor_enhanced_v2 import EnhancedHybridPredictorV2
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
