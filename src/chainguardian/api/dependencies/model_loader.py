"""
Model loader dependency for FastAPI.
Loads predictor once at startup and caches it.
"""
from functools import lru_cache
from chainguardian.ml.models.hybrid_predictor_enhanced_v2 import EnhancedHybridPredictorV2


@lru_cache()  # Cache the result - loads only once!
def get_predictor() -> EnhancedHybridPredictorV2:
    """
    Get the ML predictor instance (cached singleton).
    
    This function is called by FastAPI's dependency injection system.
    The @lru_cache decorator ensures the predictor loads only once,
    then returns the cached instance on subsequent calls.
    
    Returns:
        EnhancedHybridPredictorV2: Loaded predictor ready for inference
    """
    print("🔄 Loading predictor (this should only print once)...")
    predictor = EnhancedHybridPredictorV2()
    print(f"✅ Predictor loaded: {predictor.use_ensemble and 'ensemble' or 'single'} model")
    return predictor
