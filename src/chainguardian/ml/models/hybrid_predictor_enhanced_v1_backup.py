"""
Enhanced Hybrid Predictor with Confidence Calibration
====================================================
Adds dynamic weight adjustment, confidence calibration, and uncertainty tracking.
"""

import numpy as np
import pandas as pd
import joblib
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
import logging
from dataclasses import dataclass, asdict
from enum import Enum

# SHAP for explainability
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logging.warning("SHAP not available. Install with: pip install shap")

logger = logging.getLogger(__name__)


class DataQualityLevel(Enum):
    """Data quality assessment levels."""
    EXCELLENT = "EXCELLENT"      # Full source + complete semantic analysis
    GOOD = "GOOD"                # Full source, partial semantic
    FAIR = "FAIR"                # Partial source, static analysis only
    POOR = "POOR"                # Missing source, limited static
    UNKNOWN = "UNKNOWN"          # Cannot assess


class ConfidenceLevel(Enum):
    """Confidence assessment levels."""
    VERY_HIGH = "VERY_HIGH"      # 90-100%
    HIGH = "HIGH"                # 70-90%
    MODERATE = "MODERATE"        # 50-70%
    LOW = "LOW"                  # 30-50%
    VERY_LOW = "VERY_LOW"        # <30%


@dataclass
class DataCompletenessMetrics:
    """Tracks completeness of analysis data."""
    source_code_available: bool = False
    semantic_analysis_complete: bool = False
    static_analysis_complete: bool = False
    graph_features_available: bool = False
    cei_analysis_quality: float = 0.0  # 0-1 scale
    
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


class EnhancedHybridPredictor:
    """
    Enhanced Hybrid Vulnerability Predictor with Confidence Calibration.
    
    ENHANCEMENTS:
    1. DYNAMIC WEIGHT ADJUSTMENT:
       - Adjusts ML/semantic weights based on data quality
       - Poor semantic data → Higher ML weight
       - Excellent semantic data → Higher semantic weight
    
    2. CONFIDENCE CALIBRATION:
       - Boosts confidence when ML certainty aligns with static signals
       - Reduces confidence when contradictory signals exist
       - Adjusts for data completeness
    
    3. DATA COMPLETENESS TRACKING:
       - Tracks what analysis components were available
       - Provides quality score for predictions
    
    4. ENHANCED LLM OUTPUT:
       - Detailed uncertainty explanations
       - Data quality assessment
       - Actionable recommendations
    """
    
    # Default weights for different quality levels
    # 1. Update WEIGHT_PROFILES in EnhancedHybridPredictor class:
    WEIGHT_PROFILES = {
        DataQualityLevel.EXCELLENT: {'ml': 0.3, 'semantic': 0.7},
        DataQualityLevel.GOOD: {'ml': 0.4, 'semantic': 0.6},
        DataQualityLevel.FAIR: {'ml': 0.6, 'semantic': 0.4},
        DataQualityLevel.POOR: {'ml': 0.9, 'semantic': 0.1},  # CHANGED: 90/10 for NULL source
        DataQualityLevel.UNKNOWN: {'ml': 0.5, 'semantic': 0.5}
    }

    # 2. Update CONFIDENCE_BOOSTS:
    CONFIDENCE_BOOSTS = {
        'ml_certainty_alignment': 0.4,      # Increased
        'semantic_completeness': 0.25,      # Increased
        'contradiction_penalty': -0.2,      # Reduced
        'data_quality_multiplier': 1.3,     # Increased
        'static_signal_boost': 0.15,        # NEW
        'moderate_ml_boost': 0.25           # NEW
    }
    
    def __init__(
        self,
        model_path: str = None,
        scaler_path: str = None,
        metadata_path: str = None,
        enable_shap: bool = True,
        models_dir: str = None
    ):
        """Initialize enhanced predictor."""
        # Paths - use provided models_dir or default to project structure
        if models_dir:
            models_dir = Path(models_dir)
        else:
            # Default to project structure: chainguardian-ai/models
            models_dir = Path(__file__).parent.parent.parent.parent.parent / 'models'
        
        if model_path is None:
            model_path = models_dir / 'production_model_v6.pkl'
        if scaler_path is None:
            scaler_path = models_dir / 'production_scaler_v6.pkl'
        if metadata_path is None:
            metadata_path = models_dir / 'feature_metadata_v6.json'
        
        # Load model and scaler
        try:
            self.ml_model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            logger.info(f"✅ Loaded model from {model_path}")
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            # Try with .pkl extension if not already
            if not str(model_path).endswith('.pkl'):
                model_path = Path(str(model_path) + '.pkl')
                scaler_path = Path(str(scaler_path) + '.pkl')
            try:
                self.ml_model = joblib.load(model_path)
                self.scaler = joblib.load(scaler_path)
                logger.info(f"✅ Loaded model from {model_path}")
            except Exception as e2:
                logger.error(f"❌ Failed to load model with .pkl: {e2}")
                raise
        
        # Load feature names
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
        
        # Initialize SHAP explainer
        self.shap_explainer = None
        if enable_shap and SHAP_AVAILABLE:
            try:
                logger.info("🔍 Initializing SHAP TreeExplainer...")
                if hasattr(self.ml_model, 'calibrated_classifiers_'):
                    base_model = self.ml_model.calibrated_classifiers_[0].estimator
                    self.shap_explainer = shap.TreeExplainer(base_model)
                else:
                    self.shap_explainer = shap.TreeExplainer(self.ml_model)
                logger.info("✅ SHAP explainer ready")
            except Exception as e:
                logger.warning(f"⚠️ Could not initialize SHAP: {e}")
        
        # Semantic weights
        self.semantic_weights = {
            'cei_violation': 0.40,
            'cei_score_low': 0.20,
            'state_after_call': 0.30,
            'unchecked_critical': 0.20,
            'reentrancy_guard_bonus': -0.50,
        }
        
        # Override thresholds
        self.override_thresholds = {
            'high_cei_violations': 3,
            'perfect_cei_with_guard': True,
        }
    
    def _get_default_features(self) -> List[str]:
        """Return default feature list."""
        # Vulnerability flags (26)
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
    
    # Update the assess_data_completeness method in hybrid_predictor_enhanced.py:

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
        
        # CRITICAL FIX: If source code is NULL, semantic analysis cannot be complete
        if not has_source_code:
            metrics.semantic_analysis_complete = False
            metrics.cei_analysis_quality = 0.0
        else:
            # Only validate semantic features if source code exists
            semantic_valid = all(features.get(f, 0) >= 0 for f in cei_features)
            metrics.semantic_analysis_complete = semantic_present and semantic_valid
            
            # CEI analysis quality (if available)
            if metrics.semantic_analysis_complete:
                cei_score = features.get('cei_pattern_score', 0)
                cei_violations = features.get('cei_violations', 0)
                cei_safe = features.get('cei_safe_functions', 0)
                total_functions = features.get('num_functions', 1)
                
                # Quality based on CEI coverage and consistency
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
        profile = self.WEIGHT_PROFILES.get(data_quality, self.WEIGHT_PROFILES[DataQualityLevel.UNKNOWN])
        return profile['ml'], profile['semantic']
    
    def calculate_semantic_risk(self, features: Dict) -> Tuple[float, List[str], Dict]:
        """Enhanced semantic risk calculation with NULL source handling."""
        risk = 0.0
        reasons = []
        metadata = {
            'components_used': [],
            'data_quality_notes': []
        }
        
        # Check if source code is NULL
        source_code = features.get('source_code')
        has_source_code = source_code is not None and source_code != ""
        
        if not has_source_code:
            # NULL source: Use static analysis as proxy
            static_risk = 0.0
            static_components = []
            
            # Reentrancy
            if features.get('has_reentrancy', False):
                static_risk += 0.4
                static_components.append('reentrancy')
                reasons.append("🚨 Reentrancy detected (source unavailable)")
            
            # Unchecked calls
            if features.get('has_unchecked_call', False):
                static_risk += 0.3
                static_components.append('unchecked_call')
                reasons.append("⚠️ Unchecked calls (source unavailable)")
            
            # External calls
            num_external = features.get('num_external_calls', 0)
            if num_external > 0:
                call_risk = min(num_external / 10, 1.0) * 0.2
                static_risk += call_risk
                static_components.append('external_calls')
                reasons.append(f"🔍 {num_external} external calls (source unavailable)")
            
            # Access control
            if features.get('has_access_control_issues', False):
                static_risk += 0.1
                static_components.append('access_control')
                reasons.append("🔒 Access control issues (source unavailable)")
            
            # Apply reentrancy guard bonus if present
            has_guard = features.get('has_reentrancy_guard', False)
            if has_guard and num_external > 0:
                static_risk *= (1 + self.semantic_weights['reentrancy_guard_bonus'])
                reasons.append(f"✅ Reentrancy guard detected (-50% risk)")
            
            risk = min(static_risk, 0.5)  # Cap at 50% for proxy
            metadata['components_used'] = static_components
            metadata['data_quality_notes'].append("Semantic risk estimated from static analysis")
            
        else:
            # Original CEI-based calculation for contracts with source
            # CEI violations
            cei_violations = features.get('cei_violations', 0)
            if cei_violations > 0:
                violation_risk = self.semantic_weights['cei_violation'] * min(cei_violations / 5, 1.0)
                risk += violation_risk
                reasons.append(f"🚨 CEI violations: {cei_violations} (+{violation_risk:.0%} risk)")
                metadata['components_used'].append('cei_violations')
            
            # Low CEI score
            cei_score = features.get('cei_pattern_score', 1.0)
            if cei_score < 0.8:
                score_risk = self.semantic_weights['cei_score_low'] * (1.0 - cei_score)
                risk += score_risk
                reasons.append(f"⚠️ Low CEI score: {cei_score:.2f} (+{score_risk:.0%} risk)")
                metadata['components_used'].append('cei_score')
            elif cei_score == 1.0:
                reasons.append(f"✅ Perfect CEI compliance")
                metadata['data_quality_notes'].append("Perfect CEI pattern detected")
            
            # State after call
            state_after = features.get('state_after_call_count', 0)
            if state_after > 0:
                state_risk = self.semantic_weights['state_after_call'] * min(state_after / 3, 1.0)
                risk += state_risk
                reasons.append(f"🚨 State-after-call: {state_after} (+{state_risk:.0%} risk)")
                metadata['components_used'].append('state_after_call')
            
            # Unchecked calls
            unchecked = features.get('unchecked_calls_in_critical_context', 0)
            if unchecked > 0:
                unchecked_risk = self.semantic_weights['unchecked_critical'] * min(unchecked / 2, 1.0)
                risk += unchecked_risk
                reasons.append(f"⚠️ Unchecked critical calls: {unchecked} (+{unchecked_risk:.0%} risk)")
                metadata['components_used'].append('unchecked_calls')
            
            # Reentrancy guard bonus
            has_guard = features.get('has_reentrancy_guard', False)
            num_external = features.get('num_external_calls', 0)
            
            if has_guard and num_external > 0:
                risk *= (1 + self.semantic_weights['reentrancy_guard_bonus'])
                reasons.append(f"✅ Reentrancy guard detected (-50% risk)")
                metadata['components_used'].append('reentrancy_guard')
        
        return min(risk, 1.0), reasons, metadata
    
    def calibrate_confidence(
        self,
        ml_score: float,
        semantic_score: float,
        static_signals: Dict,
        data_quality: DataCompletenessMetrics,
        override_applied: bool = False
    ) -> Tuple[float, List[str]]:
        """Optimized confidence calibration."""
        base_confidence = (ml_score + semantic_score) / 2
        calibration_notes = []
        
        # 1. ML certainty alignment (increased boost)
        static_risk_score = self._calculate_static_risk_score(static_signals)
        
        if ml_score > 0.9 and static_risk_score > 0.7:
            boost = self.CONFIDENCE_BOOSTS['ml_certainty_alignment']
            base_confidence = min(base_confidence + boost, 1.0)
            calibration_notes.append(
                f"⬆️ High confidence: ML certainty aligns with strong static signals"
            )
        
        # 2. Moderate ML boost (new)
        elif ml_score > 0.6 and static_risk_score > 0.5:
            boost = self.CONFIDENCE_BOOSTS['moderate_ml_boost']
            base_confidence = min(base_confidence + boost, 0.9)
            calibration_notes.append(
                f"⬆️ Moderate confidence: ML shows strong indicators"
            )
        
        # 3. Static signal boost (new)
        if static_risk_score > 0.7 and ml_score > 0.4:
            boost = self.CONFIDENCE_BOOSTS['static_signal_boost']
            base_confidence = min(base_confidence + boost, 1.0)
            calibration_notes.append(
                f"⬆️ Static signals indicate risk"
            )
        
        # 4. Data quality multiplier (increased)
        quality_score = data_quality.calculate_quality_score()
        if quality_score > 0.8:
            multiplier = self.CONFIDENCE_BOOSTS['data_quality_multiplier']
            base_confidence = min(base_confidence * multiplier, 1.0)
            calibration_notes.append(
                f"⬆️ High data quality increases confidence"
            )
        elif quality_score < 0.4:
            # Less severe reduction for poor data
            base_confidence *= max(quality_score, 0.3)
            calibration_notes.append(
                f"⬇️ Low data quality reduces confidence"
            )
        
        # 5. Contradiction penalty (reduced)
        if self._has_contradictory_signals(ml_score, semantic_score, static_signals):
            penalty = self.CONFIDENCE_BOOSTS['contradiction_penalty']
            base_confidence = max(base_confidence + penalty, 0.2)  # Less severe
            calibration_notes.append(
                f"⬇️ Contradictory signals slightly reduce confidence"
            )
        
        # 6. Override handling
        if override_applied:
            base_confidence = max(base_confidence, 0.9)
            calibration_notes.append(
                f"✅ High confidence: Domain knowledge override"
            )
        
        # Ensure confidence is reasonable
        calibrated = max(0.1, min(base_confidence, 1.0))
        
        return calibrated, calibration_notes
    
    def _calculate_static_risk_score(self, static_signals: Dict) -> float:
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
            value = static_signals.get(signal, 0)
            if isinstance(value, bool):
                value = 1.0 if value else 0.0
            elif isinstance(value, (int, float)):
                # Normalize numeric values
                if 'count' in signal or 'num_' in signal:
                    value = min(value / 10, 1.0)
            score += weight * value
        
        return min(score, 1.0)
    
    def _has_contradictory_signals(
        self,
        ml_score: float,
        semantic_score: float,
        static_signals: Dict
    ) -> bool:
        """Check for contradictory signals that reduce confidence."""
        contradictions = []
        
        # ML says vulnerable but no static evidence
        if ml_score > 0.7 and not any(static_signals.get(f, False) for f in 
                                     ['has_reentrancy', 'has_unchecked_call', 'has_access_control_issues']):
            contradictions.append("ML high risk but no static vulnerabilities")
        
        # Static evidence but ML says safe
        if ml_score < 0.3 and any(static_signals.get(f, False) for f in 
                                 ['has_reentrancy', 'has_unchecked_call']):
            contradictions.append("Static vulnerabilities but ML low risk")
        
        # Semantic says high risk but ML says low risk
        if semantic_score > 0.7 and ml_score < 0.3:
            contradictions.append("Semantic high risk but ML low risk")
        
        return len(contradictions) > 0
    
    def predict_with_uncertainty(
        self,
        features: Dict,
        return_details: bool = True,
        explain: bool = True,
        llm_ready: bool = False
    ) -> Dict:
        """
        Enhanced prediction with uncertainty quantification.
        
        RETURNS:
            Dict with prediction, calibrated confidence, and uncertainty metrics
        """
        # Step 1: Assess data completeness
        data_completeness = self.assess_data_completeness(features)
        data_quality = data_completeness.get_quality_level()
        
        # Step 2: Calculate dynamic weights
        ml_weight, semantic_weight = self.calculate_dynamic_weights(data_quality)
        
        
        # Step 3: Extract feature vector - FIX FOR FEATURE NAMES
        # Create a DataFrame with the exact feature names the scaler expects
        X_df = pd.DataFrame(columns=self.feature_names)
        
        # Fill with 0s for missing features, use actual values for present features
        row_data = {}
        for feature in self.feature_names:
            row_data[feature] = features.get(feature, 0)
        
        X_df = pd.DataFrame([row_data])
        
        # Scale using the DataFrame (preserves feature names)
        try:
            X_scaled = self.scaler.transform(X_df)
        except Exception as e:
            # Fallback to numpy array if DataFrame fails
            logger.warning(f"⚠️ Scaling with DataFrame failed: {e}, using numpy array")
            X_scaled = self.scaler.transform(X_df.values)
        
        # Step 4: ML prediction
        ml_proba = self.ml_model.predict_proba(X_scaled)[0, 1]
        
        # Step 5: Semantic risk
        semantic_score, semantic_reasons, semantic_metadata = self.calculate_semantic_risk(features)
        
        # Step 6: Check overrides
        override = self.check_overrides(features, ml_proba, semantic_score)
        
        if override:
            prediction, override_reason = override
            final_score = 1.0 if prediction == 1 else 0.0
            method = "OVERRIDE"
            override_applied = True
        else:
            # Apply dynamic weights
            final_score = (ml_weight * ml_proba) + (semantic_weight * semantic_score)
            prediction = 1 if final_score > 0.2 else 0  # Using default threshold
            override_reason = None
            method = "DYNAMIC_HYBRID"
            override_applied = False
        
        # Step 7: Calibrate confidence
        static_signals = {
            'has_reentrancy': features.get('has_reentrancy', False),
            'has_unchecked_call': features.get('has_unchecked_call', False),
            'has_access_control_issues': features.get('has_access_control_issues', False),
            'num_external_calls': features.get('num_external_calls', 0),
            'high_severity_count': features.get('high_severity_count', 0),
            'has_inline_assembly': features.get('has_inline_assembly', False)
        }
        
        calibrated_confidence, calibration_notes = self.calibrate_confidence(
            ml_proba, semantic_score, static_signals, data_completeness, override_applied
        )
        
        # Step 8: Compile results
        result = {
            'prediction': prediction,
            'prediction_label': 'VULNERABLE' if prediction == 1 else 'SAFE',
            'raw_score': final_score,
            'calibrated_confidence': calibrated_confidence,
            'confidence_level': self._get_confidence_level(calibrated_confidence).value,
            'method': method,
            'weights_applied': {
                'ml_weight': ml_weight,
                'semantic_weight': semantic_weight,
                'data_quality': data_quality.value
            }
        }
        
        # Add detailed metrics if requested
        if return_details:
            result.update({
                'ml_score': ml_proba,
                'semantic_score': semantic_score,
                'threshold': 0.20,
                'semantic_reasons': semantic_reasons,
                'semantic_metadata': semantic_metadata,
                'override_reason': override_reason,
                'risk_level': self._get_risk_level(final_score),
                'data_quality': {
                    **asdict(data_completeness),
                    'quality_score': data_completeness.calculate_quality_score(),
                    'quality_level': data_quality.value
                },
                'calibration_notes': calibration_notes,
                'uncertainty_factors': self._identify_uncertainty_factors(
                    ml_proba, semantic_score, data_completeness, static_signals
                )
            })
        
        # Add SHAP explanation
        if explain and self.shap_explainer is not None:
            result['shap_explanation'] = self.explain_with_shap(X_scaled, top_k=10)
        
        # LLM-ready format
        if llm_ready:
            result = self._format_for_llm_enhanced(result, features, data_completeness)
        
        return result
    
    def _identify_uncertainty_factors(
        self,
        ml_score: float,
        semantic_score: float,
        data_completeness: DataCompletenessMetrics,
        static_signals: Dict
    ) -> List[str]:
        """Identify factors contributing to prediction uncertainty."""
        factors = []
        
        # Data completeness factors
        if not data_completeness.source_code_available:
            factors.append("Missing source code")
        if not data_completeness.semantic_analysis_complete:
            factors.append("Incomplete semantic analysis")
        if data_completeness.calculate_quality_score() < 0.5:
            factors.append("Low overall data quality")
        
        # Model disagreement factors
        if abs(ml_score - semantic_score) > 0.5:
            factors.append("ML and semantic scores significantly differ")
        
        # Static signal factors
        if ml_score > 0.7 and not any(static_signals.values()):
            factors.append("ML indicates risk but no static vulnerabilities found")
        
        return factors
    
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
    
    def _get_risk_level(self, score: float) -> str:
        """Convert score to risk level."""
        if score >= 0.8:
            return "CRITICAL"
        elif score >= 0.6:
            return "HIGH"
        elif score >= 0.4:
            return "MEDIUM"
        elif score >= 0.2:
            return "LOW"
        else:
            return "MINIMAL"
    
    def explain_with_shap(self, X_scaled: np.ndarray, top_k: int = 10) -> Dict:
        """Generate SHAP explanation for prediction."""
        if self.shap_explainer is None:
            return {
                'base_value': 0.0,
                'prediction_value': 0.0,
                'top_features': [],
                'error': 'SHAP not available'
            }
        
        try:
            shap_values = self.shap_explainer.shap_values(X_scaled)
            base_value = self.shap_explainer.expected_value
            prediction_value = self.ml_model.predict_proba(X_scaled)[0, 1]
            
            feature_values = X_scaled[0]
            feature_explanations = []
            
            for name, value, shap_val in zip(self.feature_names, feature_values, shap_values[0]):
                feature_explanations.append({
                    'feature': name,
                    'value': float(value),
                    'shap_value': float(shap_val),
                    'abs_shap': abs(float(shap_val))
                })
            
            feature_explanations.sort(key=lambda x: x['abs_shap'], reverse=True)
            top_features = feature_explanations[:top_k]
            for feat in top_features:
                del feat['abs_shap']
            
            return {
                'base_value': float(base_value),
                'prediction_value': float(prediction_value),
                'top_features': top_features
            }
            
        except Exception as e:
            logger.error(f"❌ SHAP explanation failed: {e}")
            return {
                'base_value': 0.0,
                'prediction_value': 0.0,
                'top_features': [],
                'error': str(e)
            }
    
    def check_overrides(
        self,
        features: Dict,
        ml_score: float,
        semantic_score: float
    ) -> Optional[Tuple[int, str]]:
        """Check if domain knowledge should override ML prediction."""
        cei_violations = features.get('cei_violations', 0)
        if cei_violations >= self.override_thresholds['high_cei_violations']:
            return (1, f"OVERRIDE: {cei_violations} CEI violations → VULNERABLE")
        
        cei_score = features.get('cei_pattern_score', 0)
        has_guard = features.get('has_reentrancy_guard', False)
        
        if cei_score == 1.0 and has_guard and ml_score < 0.3:
            return (0, f"OVERRIDE: Perfect CEI + guard → SAFE")
        
        return None
    
    def _format_for_llm_enhanced(
        self,
        result: Dict,
        features: Dict,
        data_completeness: DataCompletenessMetrics
    ) -> Dict:
        """Enhanced LLM output with uncertainty explanations."""
        llm_output = {
            "security_assessment": {
                "overall_prediction": result['prediction_label'],
                "calibrated_confidence": round(result['calibrated_confidence'], 3),
                "confidence_level": result['confidence_level'],
                "risk_level": result['risk_level'],
                "method_used": result['method'],
                "weights_applied": result['weights_applied']
            },
            
            # Data quality assessment
            "data_quality": {
                "overall_score": round(data_completeness.calculate_quality_score(), 3),
                "level": data_completeness.get_quality_level().value,
                "components": {
                    "source_code_available": data_completeness.source_code_available,
                    "semantic_analysis_complete": data_completeness.semantic_analysis_complete,
                    "static_analysis_complete": data_completeness.static_analysis_complete,
                    "graph_features_available": data_completeness.graph_features_available,
                    "cei_analysis_quality": round(data_completeness.cei_analysis_quality, 3)
                }
            },
            
            # Uncertainty analysis
            "uncertainty_analysis": {
                "factors": result.get('uncertainty_factors', []),
                "calibration_notes": result.get('calibration_notes', []),
            },
            
            # Model insights
            "model_insights": {
                "ml_analysis": {
                    "score": round(result.get('ml_score', 0), 3),
                    "weight_applied": result.get('weights_applied', {}).get('ml_weight', 0),
                    "interpretation": self._interpret_ml_score(result.get('ml_score', 0))
                },
                "semantic_analysis": {
                    "score": round(result.get('semantic_score', 0), 3),
                    "weight_applied": result.get('weights_applied', {}).get('semantic_weight', 0),
                    "findings": result.get('semantic_reasons', []),
                    "components_used": result.get('semantic_metadata', {}).get('components_used', [])
                }
            },
            
            # Contract context
            "contract_context": {
                "metadata": {
                    "lines_of_code": int(features.get('lines_of_code', 0)),
                    "num_functions": int(features.get('num_functions', 0)),
                    "num_external_calls": int(features.get('num_external_calls', 0)),
                    "max_complexity": int(features.get('max_cyclomatic_complexity', 0))
                },
                "static_analysis_findings": {
                    "total_issues": int(features.get('total_detector_hits', 0)),
                    "high_severity": int(features.get('high_severity_count', 0)),
                    "has_reentrancy": bool(features.get('has_reentrancy', False)),
                    "has_unchecked_call": bool(features.get('has_unchecked_call', False)),
                    "has_access_control_issues": bool(features.get('has_access_control_issues', False))
                },
                "cei_analysis": {
                    "violations": int(features.get('cei_violations', 0)),
                    "pattern_score": round(features.get('cei_pattern_score', 0), 3),
                    "has_reentrancy_guard": bool(features.get('has_reentrancy_guard', False))
                }
            },
            
            # Recommendations
            "recommendations": self._generate_recommendations(result, data_completeness, features)
        }
        
        # Add SHAP explanations if available
        if 'shap_explanation' in result and 'top_features' in result['shap_explanation']:
            llm_output['explainability'] = {
                "method": "SHAP (SHapley Additive exPlanations)",
                "base_risk": round(result['shap_explanation'].get('base_value', 0), 3),
                "top_risk_factors": [
                    {
                        "feature": f['feature'],
                        "contribution": round(f['shap_value'], 3),
                        "direction": "increases risk" if f['shap_value'] > 0 else "decreases risk",
                        "interpretation": self._interpret_feature(f['feature'], f['value'])
                    }
                    for f in result['shap_explanation']['top_features'][:5]
                ]
            }
        
        # Add override info if applicable
        if result.get('override_reason'):
            llm_output['domain_knowledge'] = {
                "override_applied": True,
                "reason": result['override_reason'],
                "explanation": "Domain knowledge rules override model prediction"
            }
        
        return llm_output
    
    def _interpret_ml_score(self, score: float) -> str:
        """Interpret ML score for human-readable output."""
        if score >= 0.9:
            return "Model is very confident about vulnerability patterns"
        elif score >= 0.7:
            return "Model detects strong vulnerability indicators"
        elif score >= 0.5:
            return "Model shows moderate concern about vulnerability patterns"
        elif score >= 0.3:
            return "Model shows slight concern about vulnerability patterns"
        else:
            return "Model detects primarily safe patterns"
    
    def _interpret_feature(self, feature_name: str, value: float) -> str:
        """Provide human interpretation of feature importance."""
        interpretations = {
            'has_reentrancy': "Direct reentrancy vulnerability flag",
            'has_unchecked_call': "External calls without proper error handling",
            'cei_violations': "Violations of Checks-Effects-Interactions pattern",
            'num_external_calls': "Number of external contract interactions",
            'has_access_control_issues': "Missing or insufficient access controls",
            'dfg_num_sensitive_sinks': "Data flow to sensitive operations (e.g., transfers)",
            'cg_external_call_ratio': "Ratio of external calls to total calls"
        }
        
        return interpretations.get(feature_name, "Feature indicates contract characteristic")
    
    def _generate_recommendations(
        self,
        result: Dict,
        data_completeness: DataCompletenessMetrics,
        features: Dict
    ) -> Dict:
        """Generate actionable recommendations based on analysis."""
        recommendations = {
            "immediate_actions": [],
            "investigation_priorities": [],
            "data_gathering": [],
            "long_term_improvements": []
        }
        
        # Immediate actions based on risk level
        risk_level = result['risk_level']
        if risk_level in ["CRITICAL", "HIGH"]:
            recommendations["immediate_actions"].append(
                "Conduct manual security audit immediately"
            )
            recommendations["immediate_actions"].append(
                "Review external call patterns and CEI compliance"
            )
        
        # Data gathering recommendations
        if not data_completeness.source_code_available:
            recommendations["data_gathering"].append(
                "Obtain source code for more accurate semantic analysis"
            )
        
        if not data_completeness.semantic_analysis_complete:
            recommendations["data_gathering"].append(
                "Run CEI analysis with complete source code"
            )
        
        # Investigation priorities
        if features.get('has_reentrancy', False):
            recommendations["investigation_priorities"].append(
                "Focus on reentrancy protection mechanisms"
            )
        
        if features.get('num_external_calls', 0) > 5:
            recommendations["investigation_priorities"].append(
                "Review all external calls for proper error handling"
            )
        
        # Confidence-based recommendations
        confidence = result['confidence_level']
        if confidence in ["LOW", "VERY_LOW"]:
            recommendations["long_term_improvements"].append(
                "Improve data quality by ensuring source code availability"
            )
            recommendations["long_term_improvements"].append(
                "Consider additional static analysis tools for cross-validation"
            )
        
        return recommendations


# Utility function for backward compatibility
class HybridPredictor(EnhancedHybridPredictor):
    """
    Backward compatibility wrapper.
    Uses new enhanced features but maintains original API.
    """
    def predict(
        self,
        features: Dict,
        ml_weight: float = None,
        semantic_weight: float = None,
        threshold: float = None,
        return_details: bool = True,
        explain: bool = True,
        llm_ready: bool = False
    ) -> Dict:
        """
        Original predict method for backward compatibility.
        """
        # If custom weights provided, use original logic
        if ml_weight is not None or semantic_weight is not None:
            # Fall back to base implementation
            return super().predict_with_uncertainty(
                features=features,
                return_details=return_details,
                explain=explain,
                llm_ready=llm_ready
            )
        
        # Otherwise use enhanced prediction
        return self.predict_with_uncertainty(
            features=features,
            return_details=return_details,
            explain=explain,
            llm_ready=llm_ready
        )