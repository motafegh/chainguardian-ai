"""
Backward Compatibility Wrapper for Enhanced Hybrid Predictor
============================================================
Maintains the original v1 API while using the new v2 implementation.
"""

import logging
from pathlib import Path
import sys

logger = logging.getLogger(__name__)

try:
    # Try to import the new v2 predictor
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from chainguardian.ml.models.hybrid_predictor_enhanced_v2 import EnhancedHybridPredictorV2
    
    # Create wrapper class that inherits from v2 but maintains v1 API
    class EnhancedHybridPredictor(EnhancedHybridPredictorV2):
        """
        Backward compatibility wrapper for EnhancedHybridPredictor.
        
        Maintains the exact same API as the original v1 while using
        the enhanced v2 implementation under the hood.
        """
        
        def __init__(self, *args, **kwargs):
            """Initialize with backward compatibility."""
            # Map old parameter names if needed
            if 'models_dir' in kwargs and kwargs['models_dir']:
                # Ensure models_dir is a string path
                kwargs['models_dir'] = str(kwargs['models_dir'])
            
            # Call parent constructor
            super().__init__(*args, **kwargs)
            logger.info("Using EnhancedHybridPredictor v2 (with backward compatibility)")
        
        def predict_with_uncertainty(self, features, **kwargs):
            """Maintain original method signature."""
            # Map old parameter names
            llm_ready = kwargs.pop('llm_ready', False)
            explain = kwargs.pop('explain', True)
            return_details = kwargs.pop('return_details', True)
            
            # Use single prediction method
            return self.predict_single(
                features=features,
                return_details=return_details,
                explain=explain
            )
        
        # Keep original predict method for API compatibility
        def predict(self, features, **kwargs):
            """Original predict method for backward compatibility."""
            # Extract parameters
            return_details = kwargs.get('return_details', True)
            explain = kwargs.get('explain', True)
            llm_ready = kwargs.get('llm_ready', False)
            
            # Use single prediction
            result = self.predict_single(
                features=features,
                return_details=return_details,
                explain=explain
            )
            
            # Format for LLM if requested
            if llm_ready:
                return self._format_for_llm_enhanced(result, features)
            
            return result
    
    logger.info("✅ EnhancedHybridPredictor v2 loaded successfully")
    
except ImportError as e:
    logger.error(f"Failed to load EnhancedHybridPredictorV2: {e}")
    
    # Fall back to original v1 implementation
    logger.warning("Falling back to original EnhancedHybridPredictor v1")
    
    # Import the backup
    from .hybrid_predictor_enhanced_v1_backup import EnhancedHybridPredictor
    
    # Add warning
    class EnhancedHybridPredictorWithWarning(EnhancedHybridPredictor):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            logger.warning("⚠️ Using original EnhancedHybridPredictor v1 (v2 not available)")
    
    EnhancedHybridPredictor = EnhancedHybridPredictorWithWarning
