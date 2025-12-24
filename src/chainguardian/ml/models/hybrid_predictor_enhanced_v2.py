
"""
Enhanced Hybrid Predictor v2 with All New Features
===================================================

ENHANCEMENTS:
1. YAML configuration support
2. Ensemble model integration
3. Batch prediction support
4. Bootstrap uncertainty quantification
5. Monitoring hooks
6. Performance optimization
"""

import numpy as np
import pandas as pd
import joblib
import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union, Generator
import logging
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from functools import lru_cache

# Import our new modules
from chainguardian.ml.core.config_manager import get_config
from chainguardian.ml.core.monitoring import MLMonitor
print(f"🔍 DEBUG: Starting import of hybrid_predictor_enhanced_v2 from {__file__}")

import sys
print(f"🔍 DEBUG: Module in sys.modules: {'hybrid_predictor_enhanced_v2' in sys.modules}")
# SHAP for explainability
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logging.warning("SHAP not available. Install with: pip install shap")

logger = logging.getLogger(__name__)

# ============================================================================
# CORE CLASSES (Keep existing enums and data classes for backward compatibility)
# ============================================================================

class DataQualityLevel(Enum):
    """Data quality assessment levels."""
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"
    UNKNOWN = "UNKNOWN"

class ConfidenceLevel(Enum):
    """Confidence assessment levels."""
    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    VERY_LOW = "VERY_LOW"

@dataclass
class DataCompletenessMetrics:
    """Tracks completeness of analysis data."""
    source_code_available: bool = False
    semantic_analysis_complete: bool = False
    static_analysis_complete: bool = False
    graph_features_available: bool = False
    cei_analysis_quality: float = 0.0
    
    def calculate_quality_score(self) -> float:
        """Calculate overall data quality score (0-1)."""
        weights = {
            'source': 0.3,
            'semantic': 0.3,
            'static': 0.2,
            'graph': 0.1,
            'cei': 0.1
        }
        
        score = 0.0
        score += weights['source'] * (1.0 if self.source_code_available else 0.5)
        score += weights['semantic'] * (1.0 if self.semantic_analysis_complete else 0.0)
        score += weights['static'] * (1.0 if self.static_analysis_complete else 0.5)
        score += weights['graph'] * (1.0 if self.graph_features_available else 0.0)
        score += weights['cei'] * self.cei_analysis_quality
        
        return min(score, 1.0)
    
    def get_quality_level(self) -> DataQualityLevel:
        """Convert quality score to quality level."""
        score = self.calculate_quality_score()
        
        if score >= 0.9:
            return DataQualityLevel.EXCELLENT
        elif score >= 0.7:
            return DataQualityLevel.GOOD
        elif score >= 0.5:
            return DataQualityLevel.FAIR
        elif score >= 0.3:
            return DataQualityLevel.POOR
        else:
            return DataQualityLevel.UNKNOWN

# ============================================================================
# ENHANCED HYBRID PREDICTOR v2
# ============================================================================

class EnhancedHybridPredictorV2:
    """
    Enhanced Hybrid Vulnerability Predictor v2.
    
    Key Improvements:
    1. Configuration-based parameters
    2. Ensemble model support
    3. Batch prediction with vectorization
    4. True uncertainty quantification
    5. Performance monitoring
    6. Efficient feature handling
    """
    
    def __init__(
        self,
        model_path: str = None,
        scaler_path: str = None,
        metadata_path: str = None,
        enable_shap: bool = True,
        models_dir: str = None,
        config_path: str = None,
        enable_monitoring: bool = True
    ):
        """Initialize enhanced predictor v2."""
        
        # ✅ STEP 1: Initialize ALL attributes FIRST (defensive programming)
        self.use_ensemble = False  # Default value, will update if needed
        self.config = get_config()
        self.shap_explainer = None
        self.monitor = None
        self.feature_cache = {}
        
        # ✅ STEP 2: Determine paths
        if models_dir:
            models_dir = Path(models_dir)
        else:
            models_dir = Path(__file__).parent.parent.parent.parent.parent / 'config/models'
        
        # ✅ STEP 3: Set model path and use_ensemble flag
        if model_path is None:
            # Try ensemble model first, fall back to single model
            ensemble_path = models_dir / "ensemble_model_v7.pkl"
            single_path = models_dir / "production_model_v7.pkl"
            
            if ensemble_path.exists():
                model_path = ensemble_path
                self.use_ensemble = True
            elif single_path.exists():
                model_path = single_path
                self.use_ensemble = False
            else:
                # Fall back to v6 for backward compatibility
                model_path = models_dir / "production_model_v6.pkl"
                self.use_ensemble = False
        else:
            # ✅ NEW: Handle case where model_path is provided
            # Detect if it's an ensemble based on filename
            model_path = Path(model_path)
            self.use_ensemble = "ensemble" in model_path.name
        
        # ✅ STEP 4: Set scaler path (now self.use_ensemble always exists)
        if scaler_path is None:
            if self.use_ensemble:
                scaler_path = models_dir / "ensemble_scaler_v7.pkl"
            else:
                scaler_path = models_dir / "production_scaler_v7.pkl"
        
        if metadata_path is None:
            metadata_path = models_dir / "feature_metadata_v7.json"
        
        # ✅ STEP 5: Load models
        self._load_models(model_path, scaler_path)
        
        # ✅ STEP 6: Load metadata
        self._load_metadata(metadata_path)
        
        # ✅ STEP 7: Initialize SHAP (optional)
        if enable_shap and SHAP_AVAILABLE:
            self._initialize_shap()
        
        # ✅ STEP 8: Initialize monitoring (optional)
        if enable_monitoring:
            self._initialize_monitoring()
        
        # ✅ STEP 9: Warmup
        self._warmup_prediction()

        logger.info(f"✅ EnhancedHybridPredictorV2 initialized")
        logger.info(f"   Using {'ensemble' if self.use_ensemble else 'single'} model")
        logger.info(f"   Features: {len(self.feature_names)}")

    def _warmup_prediction(self):
        """
        Run warmup predictions for both fast and full paths.
        Eliminates cold start on first user request.
        """
        try:
            import time
            print("🔥 Running warmup predictions...")
            
            # Create dummy features
            dummy_features = {name: 0.0 for name in self.feature_names}
            
            # Warmup 1: Fast path (batch mode)
            start = time.time()
            _ = self.predict_single(
                dummy_features, 
                return_details=False,  # Fast path
                explain=False
            )
            fast_time = (time.time() - start) * 1000
            print(f"   ✅ Fast path warmed up ({fast_time:.0f}ms)")
            
            # Warmup 2: Full path (single prediction with all bells and whistles)
            start = time.time()
            _ = self.predict_single(
                dummy_features, 
                return_details=True,   # Full path with calibration
                explain=False
            )
            full_time = (time.time() - start) * 1000
            print(f"   ✅ Full path warmed up ({full_time:.0f}ms)")
            
            # Warmup 3: Repeat full path to verify caching
            start = time.time()
            _ = self.predict_single(
                dummy_features, 
                return_details=True,
                explain=False
            )
            cached_time = (time.time() - start) * 1000
            print(f"   ✅ Cached path verified ({cached_time:.0f}ms)")
            
            total_time = fast_time + full_time + cached_time
            print(f"✅ Warmup complete in {total_time:.0f}ms total")
            
        except Exception as e:
            print(f"⚠️  Warmup FAILED: {e}")
            import traceback
            traceback.print_exc()

    def _load_models(self, model_path: Path, scaler_path: Path):
        """Load model(s) and scaler with error handling."""
        try:
            # Load scaler
            self.scaler = joblib.load(scaler_path)
            logger.info(f"✅ Loaded scaler from {scaler_path}")
            
            # Load model
            model_data = joblib.load(model_path)
            
            # Check if it's an ensemble
            if hasattr(model_data, 'predict_proba') and hasattr(model_data, 'models'):
                # It's a single model
                self.ml_model = model_data
                self.use_ensemble = False
            elif isinstance(model_data, dict) and 'ensemble' in model_data:
                # It's our saved ensemble
                from chainguardian.ml.core.heterogeneous_ensemble import HeterogeneousEnsemble
                self.ml_model = HeterogeneousEnsemble.load(model_path, self.config)
                self.use_ensemble = True
            else:
                # Unknown format, try to use as is
                self.ml_model = model_data
                self.use_ensemble = False
            
            logger.info(f"✅ Loaded model from {model_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            raise
    
    def _load_metadata(self, metadata_path: Path):
        """Load feature names and metadata."""
        if Path(metadata_path).exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                self.feature_names = metadata.get('feature_names', [])
                self.model_metrics = metadata.get('metrics', {})
                self.metadata = metadata
                logger.info(f"✅ Loaded {len(self.feature_names)} feature names")
        else:
            logger.warning("⚠️ Metadata file not found, using default feature order")
            self.feature_names = self._get_default_features()
            self.model_metrics = {}
            self.metadata = {}
    
    def _initialize_shap(self):
        """Initialize SHAP explainer for model interpretability."""
        try:
            logger.info("🔍 Initializing SHAP explainer...")
            
            if self.use_ensemble:
                # For ensemble, use the first model for SHAP (usually XGBoost)
                if hasattr(self.ml_model, 'models'):
                    base_model = self.ml_model.models['xgboost']['model']
                else:
                    base_model = self.ml_model
            else:
                base_model = self.ml_model
            
            # Check if model supports SHAP
            if hasattr(base_model, 'feature_importances_'):
                self.shap_explainer = shap.TreeExplainer(base_model)
                logger.info("✅ SHAP TreeExplainer ready")
            else:
                logger.warning("⚠️ Model doesn't support TreeExplainer, using KernelExplainer")
                # Fall back to KernelExplainer for non-tree models
                self.shap_explainer = shap.KernelExplainer(
                    lambda X: base_model.predict_proba(X)[:, 1],
                    np.zeros((1, len(self.feature_names)))
                )
                
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize SHAP: {e}")
            self.shap_explainer = None
    
    def _initialize_monitoring(self):
        """Initialize performance monitoring."""
        try:
            from chainguardian.ml.core.monitoring import MLMonitor
            self.monitor = MLMonitor(self.config)
            logger.info("✅ Performance monitoring initialized")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize monitoring: {e}")
            self.monitor = None
    
    @lru_cache(maxsize=1000)
    def _get_feature_vector(self, features: Dict) -> np.ndarray:
        """
        Convert features dictionary to numpy array with caching.
        Caching significantly speeds up batch predictions.
        """

        # Handle both dict and frozenset
        if isinstance(features, frozenset):
            # Convert frozenset back to dict
            features_dict = dict(features)
            features = features_dict
        # Create feature vector with exact feature order
        feature_vector = np.zeros(len(self.feature_names))
        
        for i, feature_name in enumerate(self.feature_names):
            feature_vector[i] = features.get(feature_name, 0)
        
        return feature_vector
    
    def _extract_features_batch(self, features_list: List[Dict]) -> np.ndarray:
        """
        Extract features for batch processing efficiently.
        Uses vectorization and caching for performance.
        """
        batch_size = len(features_list)
        feature_matrix = np.zeros((batch_size, len(self.feature_names)))
        
        for i, features in enumerate(features_list):
            # Use cached feature vector if available
            cache_key = str(sorted(features.items()))
            if cache_key in self.feature_cache:
                feature_matrix[i] = self.feature_cache[cache_key]
            else:
                feature_vector = self._get_feature_vector(frozenset(features.items()))
                self.feature_cache[cache_key] = feature_vector
                feature_matrix[i] = feature_vector
        
        # Apply scaling
        if hasattr(self, 'scaler'):
            feature_matrix = self.scaler.transform(feature_matrix)
        
        return feature_matrix
    
    def predict_single(self, features: Dict, return_details: bool = True, 
                      explain: bool = True) -> Dict:
        """
        Make prediction for a single contract.
        
        Args:
            features: Feature dictionary
            return_details: Whether to return detailed metrics
            explain: Whether to generate SHAP explanations
            
        Returns:
            Prediction dictionary with uncertainty
        """
        start_time = time.time()
        
        # 1. Assess data completeness
        data_completeness = self.assess_data_completeness(features)
        data_quality = data_completeness.get_quality_level()
        
        # 2. Extract and scale features
        feature_vector = self._get_feature_vector(frozenset(features.items()))
        X_scaled = self.scaler.transform(feature_vector.reshape(1, -1))
        
        # 3. Get ML prediction with uncertainty
        if self.use_ensemble and hasattr(self.ml_model, 'predict_with_uncertainty'):
            # Use ensemble with uncertainty
            ml_prediction, ml_proba, ml_ci = self.ml_model.predict_with_uncertainty(X_scaled)
            ml_proba = ml_proba[0, 1]
            ml_uncertainty = ml_ci[0, 1] - ml_ci[0, 0]  # Confidence interval width
        else:
            # Single model prediction
            ml_proba = self.ml_model.predict_proba(X_scaled)[0, 1]
            ml_prediction = 1 if ml_proba > 0.5 else 0
            ml_uncertainty = 0.0
        
        # 4. Calculate semantic risk
        semantic_score, semantic_reasons, semantic_metadata = self.calculate_semantic_risk(features)
        
        # 5. Calculate dynamic weights
        ml_weight, semantic_weight = self.calculate_dynamic_weights(data_quality)
        
        # 6. Apply hybrid scoring
        final_score = (ml_weight * ml_proba) + (semantic_weight * semantic_score)
        prediction = 1 if final_score > self.config.thresholds.get('vulnerability_prediction', 0.2) else 0
        
        # 7. Calibrate confidence
        calibrated_confidence, calibration_notes = self.calibrate_confidence(
            ml_proba, semantic_score, features, data_completeness
        )
        
        # 8. Compile results
        result = self._compile_results(
            prediction=prediction,
            final_score=final_score,
            ml_proba=ml_proba,
            semantic_score=semantic_score,
            calibrated_confidence=calibrated_confidence,
            ml_uncertainty=ml_uncertainty,
            data_completeness=data_completeness,
            semantic_reasons=semantic_reasons,
            calibration_notes=calibration_notes,
            ml_weight=ml_weight,
            semantic_weight=semantic_weight
        )
        
        # 9. Add explanations if requested
        if explain and self.shap_explainer is not None:
            result['shap_explanation'] = self.explain_with_shap(X_scaled)
        
        # 10. Add processing time
        result['processing_time_ms'] = (time.time() - start_time) * 1000
        
        # 11. Log to monitor if enabled
        if self.monitor is not None:
            self.monitor.log_prediction(features, result)
        
        return result
    
    def predict_batch(self, features_list: List[Dict], max_workers: int = None,
                     return_details: bool = True) -> List[Dict]:
        """
        Make predictions for multiple contracts efficiently.
        
        Args:
            features_list: List of feature dictionaries
            max_workers: Maximum number of parallel workers
            return_details: Whether to return detailed metrics
            
        Returns:
            List of prediction dictionaries
        """
        if max_workers is None:
            max_workers = self.config.batch_processing.get('max_workers', 4)
        
        batch_size = self.config.batch_processing.get('batch_size', 32)
        results = []
        
        # Process in batches
        for i in range(0, len(features_list), batch_size):
            batch = features_list[i:i + batch_size]
            
            if self.config.batch_processing.get('enable_vectorization', True):
                # Vectorized batch processing
                batch_results = self._process_batch_vectorized(batch, return_details)
            else:
                # Parallel processing
                batch_results = self._process_batch_parallel(batch, max_workers, return_details)
            
            results.extend(batch_results)
            
            logger.info(f"Processed batch {i//batch_size + 1}/{(len(features_list) + batch_size - 1)//batch_size}")
        
        return results
    
    def _process_batch_vectorized(self, batch: List[Dict], return_details: bool) -> List[Dict]:
        """Process batch using vectorized operations for efficiency."""
        
        # Extract features in batch
        X_batch = self._extract_features_batch(batch)
        
        # Get batch predictions from model
        if self.use_ensemble and hasattr(self.ml_model, 'predict_with_uncertainty'):
            predictions, probabilities, confidence_intervals = self.ml_model.predict_with_uncertainty(X_batch)
            ml_probas = probabilities[:, 1]
            ml_uncertainties = confidence_intervals[:, 1] - confidence_intervals[:, 0]
        else:
            ml_probas = self.ml_model.predict_proba(X_batch)[:, 1]
            predictions = (ml_probas > 0.5).astype(int)
            ml_uncertainties = np.zeros(len(batch))
        
        # ✅ Pre-compute semantic scores and reasons for ALL samples (avoid recalculation)
        semantic_data = []
        for features in batch:
            semantic_score, semantic_reasons, semantic_metadata = self.calculate_semantic_risk(features)
            semantic_data.append({
                'score': semantic_score,
                'reasons': semantic_reasons,
                'metadata': semantic_metadata
            })
        
        # ✅ Fast path: Simplified batch processing (skip calibration if not needed)
        if not return_details:
            batch_results = []
            for i, features in enumerate(batch):
                semantic_score = semantic_data[i]['score']
                final_score = 0.8 * ml_probas[i] + 0.2 * semantic_score  # Default weights
                prediction = 1 if final_score > self.config.thresholds.get('vulnerability_prediction', 0.2) else 0
                
                batch_results.append({
                    'prediction': prediction,
                    'prediction_label': 'VULNERABLE' if prediction == 1 else 'SAFE',
                    'probability': float(ml_probas[i]),
                    'confidence': float(ml_probas[i]),  # Simplified confidence
                    'raw_score': float(final_score)
                })
            return batch_results
        
        # ✅ Full processing path: Use pre-computed semantic data
        batch_results = []
        for i, features in enumerate(batch):
            # Assess data completeness (per-sample, but fast)
            data_completeness = self.assess_data_completeness(features)
            
            # ✅ Use pre-computed semantic data (no recalculation!)
            semantic_score = semantic_data[i]['score']
            semantic_reasons = semantic_data[i]['reasons']
            
            # Calculate dynamic weights
            ml_weight, semantic_weight = self.calculate_dynamic_weights(
                data_completeness.get_quality_level()
            )
            
            # Apply hybrid scoring
            final_score = (ml_weight * ml_probas[i]) + (semantic_weight * semantic_score)
            prediction = 1 if final_score > self.config.thresholds.get('vulnerability_prediction', 0.2) else 0
            
            # Calibrate confidence
            calibrated_confidence, calibration_notes = self.calibrate_confidence(
                ml_probas[i], semantic_score, features, data_completeness
            )
            
            # Compile results
            result = self._compile_results(
                prediction=prediction,
                final_score=final_score,
                ml_proba=ml_probas[i],
                semantic_score=semantic_score,
                calibrated_confidence=calibrated_confidence,
                ml_uncertainty=ml_uncertainties[i],
                data_completeness=data_completeness,
                semantic_reasons=semantic_reasons,
                calibration_notes=calibration_notes,
                ml_weight=ml_weight,
                semantic_weight=semantic_weight
            )
            
            batch_results.append(result)
        
        return batch_results
    
    def _process_batch_parallel(self, batch: List[Dict], max_workers: int, 
                               return_details: bool) -> List[Dict]:
        """Process batch using parallel workers."""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_features = {
                executor.submit(self.predict_single, features, return_details, False): features
                for features in batch
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_features):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    features = future_to_features[future]
                    logger.error(f"Failed to predict for features: {e}")
                    # Return error result
                    results.append({
                        'error': str(e),
                        'prediction': -1,
                        'prediction_label': 'ERROR'
                    })
        
        return results
    
    def _compile_results(self, **kwargs) -> Dict:
        """Compile prediction results into standardized format."""
        result = {
            'prediction': kwargs['prediction'],
            'prediction_label': 'VULNERABLE' if kwargs['prediction'] == 1 else 'SAFE',
            'raw_score': kwargs['final_score'],
            'calibrated_confidence': kwargs['calibrated_confidence'],
            'confidence_level': self._get_confidence_level(kwargs['calibrated_confidence']).value,
            'ml_score': kwargs['ml_proba'],
            'semantic_score': kwargs['semantic_score'],
            'ml_uncertainty': kwargs['ml_uncertainty'],
            'weights_applied': {
                'ml_weight': kwargs['ml_weight'],
                'semantic_weight': kwargs['semantic_weight']
            },
            'data_quality': {
                'quality_score': kwargs['data_completeness'].calculate_quality_score(),
                'quality_level': kwargs['data_completeness'].get_quality_level().value
            },
            'semantic_reasons': kwargs['semantic_reasons'],
            'calibration_notes': kwargs['calibration_notes']
        }
        
        return result
    
    # ============================================================================
    # EXISTING METHODS (Updated to use configuration)
    # ============================================================================
    
    def assess_data_completeness(self, features: Dict) -> DataCompletenessMetrics:
        """Assess completeness of the provided features."""
        metrics = DataCompletenessMetrics()
        
        # Check source code availability
        source_code_key = 'source_code'
        has_source_code = features.get(source_code_key) is not None
        metrics.source_code_available = has_source_code
        
        # Check semantic analysis completeness
        cei_features = ['cei_violations', 'cei_safe_functions', 'cei_pattern_score']
        semantic_present = any(f in features for f in cei_features)
        
        if not has_source_code:
            metrics.semantic_analysis_complete = False
            metrics.cei_analysis_quality = 0.0
        else:
            semantic_valid = all(features.get(f, 0) >= 0 for f in cei_features)
            metrics.semantic_analysis_complete = semantic_present and semantic_valid
            
            if metrics.semantic_analysis_complete:
                cei_score = features.get('cei_pattern_score', 0)
                cei_violations = features.get('cei_violations', 0)
                cei_safe = features.get('cei_safe_functions', 0)
                total_functions = features.get('num_functions', 1)
                
                coverage = cei_safe / total_functions if total_functions > 0 else 0
                consistency = 1.0 - (cei_violations / (cei_violations + cei_safe + 1))
                metrics.cei_analysis_quality = (cei_score + coverage + consistency) / 3
            else:
                metrics.cei_analysis_quality = 0.0
        
        # Check static analysis completeness
        static_flags = ['has_reentrancy', 'has_access_control_issues', 'has_unchecked_call']
        static_present = any(f in features for f in static_flags)
        metrics.static_analysis_complete = static_present
        
        # Check graph features
        graph_flags = ['cfg_num_nodes', 'dfg_num_sensitive_sinks', 'cg_num_external_calls']
        graph_present = any(f in features for f in graph_flags)
        metrics.graph_features_available = graph_present
        
        return metrics
    
    def calculate_dynamic_weights(self, data_quality: DataQualityLevel) -> Tuple[float, float]:
        """Calculate dynamic weights based on data quality."""
        profiles = self.config.weights.get('data_quality_profiles', {})
        profile = profiles.get(data_quality.value, profiles.get('UNKNOWN', {'ml': 0.5, 'semantic': 0.5}))
        return profile['ml'], profile['semantic']
    
    def calculate_semantic_risk(self, features: Dict) -> Tuple[float, List[str], Dict]:
        """Enhanced semantic risk calculation with configuration-based weights."""
        risk = 0.0
        reasons = []
        metadata = {'components_used': []}
        
        # Get weights from configuration
        semantic_weights = self.config.weights.get('semantic_risk', {})
        
        # Check if source code is NULL
        has_source_code = features.get('source_code') is not None and features.get('source_code') != ""
        
        if not has_source_code:
            # NULL source: Use static analysis as proxy
            static_risk = 0.0
            
            # Reentrancy
            if features.get('has_reentrancy', False):
                static_risk += 0.4
                reasons.append("🚨 Reentrancy detected (source unavailable)")
            
            # Unchecked calls
            if features.get('has_unchecked_call', False):
                static_risk += 0.3
                reasons.append("⚠️ Unchecked calls (source unavailable)")
            
            # External calls
            num_external = features.get('num_external_calls', 0)
            if num_external > 0:
                call_risk = min(num_external / 10, 1.0) * 0.2
                static_risk += call_risk
                reasons.append(f"🔍 {num_external} external calls (source unavailable)")
            
            # Access control
            if features.get('has_access_control_issues', False):
                static_risk += 0.1
                reasons.append("🔒 Access control issues (source unavailable)")
            
            # Apply reentrancy guard bonus
            has_guard = features.get('has_reentrancy_guard', False)
            if has_guard and num_external > 0:
                static_risk *= (1 + semantic_weights.get('reentrancy_guard_bonus', -0.5))
                reasons.append(f"✅ Reentrancy guard detected (-50% risk)")
            
            risk = min(static_risk, 0.5)
            
        else:
            # Original CEI-based calculation
            cei_violations = features.get('cei_violations', 0)
            if cei_violations > 0:
                violation_risk = semantic_weights.get('cei_violation', 0.4) * min(cei_violations / 5, 1.0)
                risk += violation_risk
                reasons.append(f"🚨 CEI violations: {cei_violations} (+{violation_risk:.0%} risk)")
                metadata['components_used'].append('cei_violations')
            
            cei_score = features.get('cei_pattern_score', 1.0)
            if cei_score < 0.8:
                score_risk = semantic_weights.get('cei_score_low', 0.2) * (1.0 - cei_score)
                risk += score_risk
                reasons.append(f"⚠️ Low CEI score: {cei_score:.2f} (+{score_risk:.0%} risk)")
                metadata['components_used'].append('cei_score')
            elif cei_score == 1.0:
                reasons.append(f"✅ Perfect CEI compliance")
            
            state_after = features.get('state_after_call_count', 0)
            if state_after > 0:
                state_risk = semantic_weights.get('state_after_call', 0.3) * min(state_after / 3, 1.0)
                risk += state_risk
                reasons.append(f"🚨 State-after-call: {state_after} (+{state_risk:.0%} risk)")
                metadata['components_used'].append('state_after_call')
            
            unchecked = features.get('unchecked_calls_in_critical_context', 0)
            if unchecked > 0:
                unchecked_risk = semantic_weights.get('unchecked_critical', 0.2) * min(unchecked / 2, 1.0)
                risk += unchecked_risk
                reasons.append(f"⚠️ Unchecked critical calls: {unchecked} (+{unchecked_risk:.0%} risk)")
                metadata['components_used'].append('unchecked_calls')
            
            has_guard = features.get('has_reentrancy_guard', False)
            num_external = features.get('num_external_calls', 0)
            
            if has_guard and num_external > 0:
                risk *= (1 + semantic_weights.get('reentrancy_guard_bonus', -0.5))
                reasons.append(f"✅ Reentrancy guard detected (-50% risk)")
                metadata['components_used'].append('reentrancy_guard')
        
        return min(risk, 1.0), reasons, metadata
    
    def calibrate_confidence(self, ml_score: float, semantic_score: float,
                           features: Dict, data_completeness: DataCompletenessMetrics) -> Tuple[float, List[str]]:
        """Calibrate confidence score based on multiple factors."""
        base_confidence = (ml_score + semantic_score) / 2
        calibration_notes = []
        
        # Get boost values from configuration
        boosts = self.config.weights.get('confidence_calibration', {})
        
        # 1. ML certainty alignment
        static_risk_score = self._calculate_static_risk_score(features)
        
        if ml_score > 0.9 and static_risk_score > 0.7:
            boost = boosts.get('ml_certainty_alignment', 0.4)
            base_confidence = min(base_confidence + boost, 1.0)
            calibration_notes.append("⬆️ High confidence: ML certainty aligns with strong static signals")
        
        # 2. Moderate ML boost
        elif ml_score > 0.6 and static_risk_score > 0.5:
            boost = boosts.get('moderate_ml_boost', 0.25)
            base_confidence = min(base_confidence + boost, 0.9)
            calibration_notes.append("⬆️ Moderate confidence: ML shows strong indicators")
        
        # 3. Static signal boost
        if static_risk_score > 0.7 and ml_score > 0.4:
            boost = boosts.get('static_signal_boost', 0.15)
            base_confidence = min(base_confidence + boost, 1.0)
            calibration_notes.append("⬆️ Static signals indicate risk")
        
        # 4. Data quality multiplier
        quality_score = data_completeness.calculate_quality_score()
        if quality_score > 0.8:
            multiplier = boosts.get('data_quality_multiplier', 1.3)
            base_confidence = min(base_confidence * multiplier, 1.0)
            calibration_notes.append("⬆️ High data quality increases confidence")
        elif quality_score < 0.4:
            base_confidence *= max(quality_score, 0.3)
            calibration_notes.append("⬇️ Low data quality reduces confidence")
        
        # 5. Contradiction penalty
        if self._has_contradictory_signals(ml_score, semantic_score, features):
            penalty = boosts.get('contradiction_penalty', -0.2)
            base_confidence = max(base_confidence + penalty, 0.2)
            calibration_notes.append("⬇️ Contradictory signals slightly reduce confidence")
        
        # Ensure confidence is reasonable
        calibrated = max(0.1, min(base_confidence, 1.0))
        
        return calibrated, calibration_notes
    
    def _calculate_static_risk_score(self, features: Dict) -> float:
        """Calculate risk score from static analysis signals."""
        weights = {
            'has_reentrancy': 0.3,
            'has_unchecked_call': 0.2,
            'has_access_control_issues': 0.2,
            'num_external_calls': 0.1,
            'high_severity_count': 0.1,
            'has_inline_assembly': 0.1
        }
        
        score = 0.0
        for signal, weight in weights.items():
            value = features.get(signal, 0)
            if isinstance(value, bool):
                value = 1.0 if value else 0.0
            elif isinstance(value, (int, float)):
                if 'count' in signal or 'num_' in signal:
                    value = min(value / 10, 1.0)
            score += weight * value
        
        return min(score, 1.0)
    
    def _has_contradictory_signals(self, ml_score: float, semantic_score: float,
                                 features: Dict) -> bool:
        """Check for contradictory signals that reduce confidence."""
        contradictions = []
        
        if ml_score > 0.7 and not any(features.get(f, False) for f in 
                                     ['has_reentrancy', 'has_unchecked_call', 'has_access_control_issues']):
            contradictions.append("ML high risk but no static vulnerabilities")
        
        if ml_score < 0.3 and any(features.get(f, False) for f in 
                                 ['has_reentrancy', 'has_unchecked_call']):
            contradictions.append("Static vulnerabilities but ML low risk")
        
        if semantic_score > 0.7 and ml_score < 0.3:
            contradictions.append("Semantic high risk but ML low risk")
        
        return len(contradictions) > 0
    
    def _get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Convert confidence score to confidence level."""
        if confidence >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif confidence >= 0.7:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.5:
            return ConfidenceLevel.MODERATE
        elif confidence >= 0.3:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def explain_with_shap(self, X_scaled: np.ndarray, top_k: int = 10) -> Dict:
        """Generate SHAP explanation for prediction."""
        if self.shap_explainer is None:
            return {'error': 'SHAP not available'}
        
        try:
            shap_values = self.shap_explainer.shap_values(X_scaled)
            
            # Handle different SHAP explainer outputs
            if isinstance(shap_values, list):
                shap_values = shap_values[1]  # For binary classification
            
            feature_explanations = []
            for i, feature_name in enumerate(self.feature_names):
                shap_val = shap_values[0, i] if len(shap_values.shape) > 1 else shap_values[i]
                feature_explanations.append({
                    'feature': feature_name,
                    'value': float(X_scaled[0, i]),
                    'shap_value': float(shap_val),
                    'abs_shap': abs(float(shap_val))
                })
            
            feature_explanations.sort(key=lambda x: x['abs_shap'], reverse=True)
            top_features = feature_explanations[:top_k]
            
            return {
                'top_features': top_features,
                'base_value': float(self.shap_explainer.expected_value)
            }
            
        except Exception as e:
            logger.error(f"❌ SHAP explanation failed: {e}")
            return {'error': str(e)}
    
    def _get_default_features(self) -> List[str]:
        """Return default feature list (backward compatibility)."""
        # Same as original implementation
        vuln_flags = [
            'has_reentrancy', 'has_access_control_issues', 'has_timestamp_dependency',
            'has_unchecked_call', 'has_reentrancy_unlimited', 'has_reentrancy_benign',
            'has_reentrancy_events', 'has_unchecked_transfer', 'has_controlled_delegatecall',
            'has_delegatecall_loop', 'has_uninitialized_state', 'has_uninitialized_storage',
            'has_uninitialized_local', 'has_tx_origin', 'has_inline_assembly',
            'has_locked_ether', 'has_msg_value_loop', 'has_shadowing_state',
            'has_shadowing_builtin', 'has_shadowing_abstract', 'has_unused_state_vars',
            'has_unused_return_values', 'has_incorrect_solc_version', 'has_floating_pragma',
            'has_outdated_compiler', 'has_arbitrary_send'
        ]
        
        severity = ['high_severity_count', 'medium_severity_count', 'low_severity_count']
        code_metrics = [
            'lines_of_code', 'num_functions', 'num_external_calls', 'num_state_vars',
            'num_modifiers', 'num_low_level_calls', 'num_contracts_in_file',
            'num_dependencies', 'num_payable_functions', 'num_library_calls',
            'num_unused_functions', 'inheritance_depth', 'max_cyclomatic_complexity',
            'avg_function_complexity', 'num_functions_high_complexity',
            'comment_to_code_ratio', 'num_comments'
        ]
        
        detector_stats = [
            'high_confidence_detectors', 'medium_confidence_detectors',
            'low_confidence_detectors', 'security_detectors_triggered',
            'optimization_detectors_triggered', 'total_detector_hits',
            'unique_vulnerability_types', 'detectors_per_function', 'detectors_per_loc'
        ]
        
        risk_scores = ['risk_score_simple', 'risk_score_weighted', 'is_high_risk']
        
        graph_features = [
            'cfg_num_nodes', 'cfg_num_edges', 'cfg_num_cycles', 'cfg_max_depth',
            'cfg_avg_branching', 'cfg_has_complex_loops', 'cfg_num_exit_points',
            'cfg_cyclomatic_total',
            'cg_num_nodes', 'cg_num_edges', 'cg_max_call_depth', 'cg_num_external_calls',
            'cg_external_call_ratio', 'cg_has_cyclic_calls', 'cg_num_public_entry_points',
            'cg_num_internal_functions', 'cg_avg_calls_per_function', 'cg_num_leaf_functions',
            'dfg_num_state_vars', 'dfg_num_tainted_flows', 'dfg_has_cross_function_flow',
            'dfg_num_sensitive_sinks', 'dfg_num_external_sources', 'dfg_taint_to_sink_ratio',
            'dfg_num_unvalidated_inputs'
        ]
        
        semantic_features = [
            'cei_violations', 'cei_safe_functions', 'cei_pattern_score',
            'has_reentrancy_guard', 'functions_with_reentrancy_guard',
            'state_before_call_count', 'state_after_call_count',
            'unchecked_calls_in_critical_context'
        ]
        
        return (vuln_flags + severity + code_metrics + detector_stats +
                risk_scores + graph_features + semantic_features)

# ============================================================================
# BACKWARD COMPATIBILITY WRAPPER
# ============================================================================

class EnhancedHybridPredictor(EnhancedHybridPredictorV2):
    """
    Backward compatibility wrapper.
    Maintains original API while using new enhanced features.
    """
    
    def predict(self, features: Dict, **kwargs) -> Dict:
        """
        Original predict method for backward compatibility.
        """
        # Map old parameters to new method
        llm_ready = kwargs.get('llm_ready', False)
        explain = kwargs.get('explain', True)
        return_details = kwargs.get('return_details', True)
        
        # Use new single prediction method
        return self.predict_single(
            features=features,
            return_details=return_details,
            explain=explain
        )
    
    def predict_with_uncertainty(self, features: Dict, **kwargs) -> Dict:
        """
        Enhanced prediction with uncertainty (original method name).
        """
        return self.predict_single(features, **kwargs)