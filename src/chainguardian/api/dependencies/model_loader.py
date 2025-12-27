"""Model loader using PathResolver for environment-aware paths."""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_predictor: Optional[object] = None

def get_predictor():
    """Get or load the predictor instance (lazy loading)."""
    global _predictor
    if _predictor is None:
        _predictor = load_predictor()
    return _predictor

def load_predictor():
    """Load ML predictor using PathResolver."""
    from chainguardian.ml.models.hybrid_predictor_enhanced_v2 import EnhancedHybridPredictorV2
    from chainguardian.ml.core.path_resolver import path_resolver
    
    models_dir = path_resolver.models_dir
    logger.info(f"🔍 Project root: {path_resolver.project_root}")
    logger.info(f"📦 Models directory: {models_dir}")
    
    predictor = EnhancedHybridPredictorV2(
        models_dir=str(models_dir),
        enable_shap=True,
        enable_monitoring=True
    )
    
    logger.info("✅ Predictor loaded successfully")
    return predictor
