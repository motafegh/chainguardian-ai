"""
Production Hybrid Predictor with SHAP & LLM-Ready Output
========================================================
Combines ML predictions with semantic security rules.

WHAT THIS DOES:
1. Loads trained XGBoost model (calibrated) + RobustScaler
2. Predicts vulnerability with hybrid ensemble (ML + Semantic)
3. Explains predictions with SHAP (feature contributions)
4. Outputs structured data for LLM integration
5. Applies domain knowledge overrides (CEI violations)

ARCHITECTURE:
┌─────────────────────────────────────────────────┐
│ INPUT: Contract Features (91 numeric features)  │
└─────────────────────────────────────────────────┘
                    ↓
    ┌───────────────────────────────┐
    │   RobustScaler Transform      │
    │   (median + IQR normalization)│
    └───────────────────────────────┘
                    ↓
    ┌───────────────────────────────────────────┐
    │         Hybrid Predictor                  │
    │  ┌─────────────┐   ┌──────────────────┐  │
    │  │ ML Model    │   │ Semantic Rules   │  │
    │  │ (XGBoost)   │   │ (CEI Analysis)   │  │
    │  │ Weight: 30% │   │ Weight: 70%      │  │
    │  └─────────────┘   └──────────────────┘  │
    │           ↓              ↓                │
    │      ┌──────────────────────┐            │
    │      │  Override Logic      │            │
    │      │  (3+ CEI → VULN)     │            │
    │      └──────────────────────┘            │
    └───────────────────────────────────────────┘
                    ↓
    ┌───────────────────────────────┐
    │   SHAP Explainer              │
    │   (Feature Contributions)     │
    └───────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ OUTPUT: LLM-Ready Structured JSON               │
│  • Prediction + Confidence                      │
│  • Risk Level (CRITICAL/HIGH/MEDIUM/LOW)        │
│  • SHAP Explanations (Top 10 features)          │
│  • Semantic Analysis (CEI violations)           │
│  • Contract Metadata (LOC, functions, etc.)     │
└─────────────────────────────────────────────────┘

Author: Ali
Date: December 22, 2024
Version: 2.0 (Final Production)
"""

import numpy as np
import pandas as pd
import joblib
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import logging

# SHAP for explainability
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logging.warning("SHAP not available. Install with: pip install shap")

logger = logging.getLogger(__name__)


class HybridPredictor:
    """
    Production Hybrid Vulnerability Predictor with SHAP Explainability.
    
    USAGE:
        # Initialize
        predictor = HybridPredictor(enable_shap=True)
        
        # Predict with full analysis
        result = predictor.predict(
            features=contract_features,
            return_details=True,
            explain=True,
            llm_ready=True  # Returns LLM-formatted output
        )
        
        # result contains:
        # - prediction: 0 (safe) or 1 (vulnerable)
        # - confidence: 0.0 to 1.0
        # - risk_level: CRITICAL/HIGH/MEDIUM/LOW/MINIMAL
        # - shap_explanation: Feature contributions
        # - semantic_analysis: CEI violations, guards, etc.
        # - contract_metadata: LOC, functions, complexity
    
    HYBRID WEIGHTS (Optimized via Grid Search):
        ML Weight:       30% (pattern recognition)
        Semantic Weight: 70% (rule-based precision)
        Threshold:       0.20 (high recall for security)
    
    OVERRIDE LOGIC:
        • 3+ CEI violations → Force VULNERABLE
        • Perfect CEI + Guard + Low ML → Force SAFE
    """
    
    # Optimized defaults from hyperparameter search
    DEFAULT_ML_WEIGHT = 0.30
    DEFAULT_SEMANTIC_WEIGHT = 0.70
    DEFAULT_THRESHOLD = 0.20
    
    def __init__(
        self,
        model_path: str = None,
        scaler_path: str = None,
        metadata_path: str = None,
        enable_shap: bool = True
    ):
        """
        Initialize hybrid predictor.
        
        PARAMETERS:
            model_path: Path to trained model (.pkl)
            scaler_path: Path to RobustScaler (.pkl)
            metadata_path: Path to feature metadata (.json)
            enable_shap: Enable SHAP explanations (slower but explainable)
        """
        # Paths
        models_dir = Path(__file__).parent.parent.parent.parent.parent / 'models'
        
        if model_path is None:
            model_path = models_dir / 'production_model.pkl'
        if scaler_path is None:
            scaler_path = models_dir / 'production_scaler.pkl'
        if metadata_path is None:
            metadata_path = models_dir / 'feature_metadata.json'
        
        # Load model and scaler
        try:
            self.ml_model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            logger.info(f"✅ Loaded model from {model_path}")
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            raise
        
        # Load feature names
        if Path(metadata_path).exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                self.feature_names = metadata.get('feature_names', [])
                self.model_metrics = metadata.get('metrics', {})
                logger.info(f"✅ Loaded {len(self.feature_names)} feature names")
        else:
            logger.warning("⚠️ Metadata file not found, using default feature order")
            self.feature_names = self._get_default_features()
            self.model_metrics = {}
        
        # Initialize SHAP explainer
        self.shap_explainer = None
        if enable_shap and SHAP_AVAILABLE:
            try:
                logger.info("🔍 Initializing SHAP TreeExplainer...")
                
                # Handle calibrated models
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
        """Return default 91-feature list in training order."""
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
        
        # Severity counts (3)
        severity = ['high_severity_count', 'medium_severity_count', 'low_severity_count']
        
        # Code metrics (17)
        code_metrics = [
            'lines_of_code', 'num_functions', 'num_external_calls', 'num_state_vars',
            'num_modifiers', 'num_low_level_calls', 'num_contracts_in_file',
            'num_dependencies', 'num_payable_functions', 'num_library_calls',
            'num_unused_functions', 'inheritance_depth', 'max_cyclomatic_complexity',
            'avg_function_complexity', 'num_functions_high_complexity',
            'comment_to_code_ratio', 'num_comments'
        ]
        
        # Detector stats (9)
        detector_stats = [
            'high_confidence_detectors', 'medium_confidence_detectors',
            'low_confidence_detectors', 'security_detectors_triggered',
            'optimization_detectors_triggered', 'total_detector_hits',
            'unique_vulnerability_types', 'detectors_per_function', 'detectors_per_loc'
        ]
        
        # Risk scores (3)
        risk_scores = ['risk_score_simple', 'risk_score_weighted', 'is_high_risk']
        
        # Graph features (25)
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
        
        # Semantic features (8) ⭐
        semantic_features = [
            'cei_violations', 'cei_safe_functions', 'cei_pattern_score',
            'has_reentrancy_guard', 'functions_with_reentrancy_guard',
            'state_before_call_count', 'state_after_call_count',
            'unchecked_calls_in_critical_context'
        ]
        
        return (vuln_flags + severity + code_metrics + detector_stats +
                risk_scores + graph_features + semantic_features)
    
    def calculate_semantic_risk(self, features: Dict) -> Tuple[float, List[str]]:
        """
        Calculate semantic risk based on CEI pattern analysis.
        
        RETURNS:
            (risk_score: float, reasons: List[str])
        """
        risk = 0.0
        reasons = []
        
        # CEI violations
        cei_violations = features.get('cei_violations', 0)
        if cei_violations > 0:
            violation_risk = self.semantic_weights['cei_violation'] * min(cei_violations / 5, 1.0)
            risk += violation_risk
            reasons.append(f"🚨 CEI violations: {cei_violations} (+{violation_risk:.0%} risk)")
        
        # Low CEI score
        cei_score = features.get('cei_pattern_score', 1.0)
        if cei_score < 0.8:
            score_risk = self.semantic_weights['cei_score_low'] * (1.0 - cei_score)
            risk += score_risk
            reasons.append(f"⚠️ Low CEI score: {cei_score:.2f} (+{score_risk:.0%} risk)")
        
        # State after call
        state_after = features.get('state_after_call_count', 0)
        if state_after > 0:
            state_risk = self.semantic_weights['state_after_call'] * min(state_after / 3, 1.0)
            risk += state_risk
            reasons.append(f"🚨 State-after-call: {state_after} (+{state_risk:.0%} risk)")
        
        # Unchecked calls
        unchecked = features.get('unchecked_calls_in_critical_context', 0)
        if unchecked > 0:
            unchecked_risk = self.semantic_weights['unchecked_critical'] * min(unchecked / 2, 1.0)
            risk += unchecked_risk
            reasons.append(f"⚠️ Unchecked critical calls: {unchecked} (+{unchecked_risk:.0%} risk)")
        
        # Reentrancy guard bonus
        has_guard = features.get('has_reentrancy_guard', False)
        num_external = features.get('num_external_calls', 0)
        
        if has_guard and num_external > 0:
            risk *= (1 + self.semantic_weights['reentrancy_guard_bonus'])
            reasons.append(f"✅ Reentrancy guard detected (-50% risk)")
        
        # Perfect CEI
        if cei_score == 1.0 and cei_violations == 0:
            reasons.append(f"✅ Perfect CEI compliance")
        
        return min(risk, 1.0), reasons
    
    def check_overrides(
        self,
        features: Dict,
        ml_score: float,
        semantic_score: float
    ) -> Optional[Tuple[int, str]]:
        """
        Check if domain knowledge should override ML prediction.
        
        RETURNS:
            None or (prediction, reason)
        """
        # Override VULNERABLE: Multiple CEI violations
        cei_violations = features.get('cei_violations', 0)
        if cei_violations >= self.override_thresholds['high_cei_violations']:
            return (1, f"OVERRIDE: {cei_violations} CEI violations → VULNERABLE")
        
        # Override SAFE: Perfect CEI + Guard
        cei_score = features.get('cei_pattern_score', 0)
        has_guard = features.get('has_reentrancy_guard', False)
        
        if cei_score == 1.0 and has_guard and ml_score < 0.3:
            return (0, f"OVERRIDE: Perfect CEI + guard → SAFE")
        
        return None
    
    def explain_with_shap(self, X_scaled: np.ndarray, top_k: int = 10) -> Dict:
        """
        Generate SHAP explanation for prediction.
        
        RETURNS:
            Dict with base_value, prediction_value, top_features
        """
        if self.shap_explainer is None:
            return {
                'base_value': 0.0,
                'prediction_value': 0.0,
                'top_features': [],
                'error': 'SHAP not available'
            }
        
        try:
            # Calculate SHAP values
            shap_values = self.shap_explainer.shap_values(X_scaled)
            base_value = self.shap_explainer.expected_value
            prediction_value = self.ml_model.predict_proba(X_scaled)[0, 1]
            
            # Extract feature values
            feature_values = X_scaled[0]
            
            # Create feature explanations
            feature_explanations = []
            for name, value, shap_val in zip(self.feature_names, feature_values, shap_values[0]):
                feature_explanations.append({
                    'feature': name,
                    'value': float(value),
                    'shap_value': float(shap_val),
                    'abs_shap': abs(float(shap_val))
                })
            
            # Sort by importance
            feature_explanations.sort(key=lambda x: x['abs_shap'], reverse=True)
            
            # Keep top K
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
        Predict vulnerability with hybrid approach.
        
        PARAMETERS:
            features: Contract features dict (91 features)
            ml_weight: ML component weight (default: 0.30)
            semantic_weight: Semantic component weight (default: 0.70)
            threshold: Classification threshold (default: 0.20)
            return_details: Include all metrics (default: True)
            explain: Generate SHAP explanation (default: True)
            llm_ready: Format output for LLM prompts (default: False)
        
        RETURNS:
            Dict with prediction, confidence, explanations, etc.
        """
        # Use defaults
        if ml_weight is None:
            ml_weight = self.DEFAULT_ML_WEIGHT
        if semantic_weight is None:
            semantic_weight = self.DEFAULT_SEMANTIC_WEIGHT
        if threshold is None:
            threshold = self.DEFAULT_THRESHOLD
        
        # Extract feature vector (align to model's expected features)
        # Get scaler's expected feature count
        n_features_expected = self.scaler.n_features_in_
        
        # If feature count mismatch, filter to scaler's features
        if len(self.feature_names) != n_features_expected:
            logger.warning(
                f"Feature mismatch: {len(self.feature_names)} vs {n_features_expected}. "
                f"Using first {n_features_expected} features."
            )
            model_features = self.feature_names[:n_features_expected]
        else:
            model_features = self.feature_names
        
        # Create feature vector
        X = pd.DataFrame(
            [[features.get(f, 0) for f in model_features]],
            columns=model_features
        )
        X_scaled = self.scaler.transform(X.values)
        
        # ML prediction
        ml_proba = self.ml_model.predict_proba(X_scaled)[0, 1]
        
        # Semantic risk
        semantic_score, semantic_reasons = self.calculate_semantic_risk(features)
        
        # Check overrides
        override = self.check_overrides(features, ml_proba, semantic_score)
        
        if override:
            prediction, override_reason = override
            final_score = 1.0 if prediction == 1 else 0.0
            method = "OVERRIDE"
        else:
            final_score = (ml_weight * ml_proba) + (semantic_weight * semantic_score)
            prediction = 1 if final_score > threshold else 0
            override_reason = None
            method = "HYBRID"
        
        # Base result
        result = {
            'prediction': prediction,
            'prediction_label': 'VULNERABLE' if prediction == 1 else 'SAFE',
            'confidence': final_score,
            'method': method,
        }
        
        # Add details
        if return_details:
            result.update({
                'ml_score': ml_proba,
                'semantic_score': semantic_score,
                'ml_weight': ml_weight,
                'semantic_weight': semantic_weight,
                'threshold': threshold,
                'semantic_reasons': semantic_reasons,
                'override_reason': override_reason,
                'risk_level': self._get_risk_level(final_score),
            })
        
        # Add SHAP explanation
        if explain and self.shap_explainer is not None:
            result['shap_explanation'] = self.explain_with_shap(X_scaled, top_k=10)
        
        # LLM-ready format
        if llm_ready:
            result = self._format_for_llm(result, features)
        
        return result
    
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
    
    def _format_for_llm(self, result: Dict, features: Dict) -> Dict:
        """
        Format output for LLM prompts.
        
        STRUCTURED OUTPUT FOR LLM:
        - Clear sections (prediction, analysis, metadata)
        - Human-readable descriptions
        - Actionable insights
        - Context for report generation
        """
        llm_output = {
            # Core prediction
            "prediction": {
                "label": result['prediction_label'],
                "confidence": round(result['confidence'], 3),
                "risk_level": result['risk_level'],
                "method": result['method']
            },
            
            # ML analysis
            "ml_analysis": {
                "score": round(result['ml_score'], 3),
                "weight": result['ml_weight'],
                "interpretation": "Model detects vulnerability patterns" if result['ml_score'] > 0.5 else "Model detects safe patterns"
            },
            
            # Semantic analysis
            "semantic_analysis": {
                "score": round(result['semantic_score'], 3),
                "weight": result['semantic_weight'],
                "cei_violations": int(features.get('cei_violations', 0)),
                "cei_pattern_score": round(features.get('cei_pattern_score', 0), 3),
                "has_reentrancy_guard": bool(features.get('has_reentrancy_guard', False)),
                "state_after_call_count": int(features.get('state_after_call_count', 0)),
                "findings": result.get('semantic_reasons', [])
            },
            
            # Contract metadata
            "contract_metadata": {
                "lines_of_code": int(features.get('lines_of_code', 0)),
                "num_functions": int(features.get('num_functions', 0)),
                "num_external_calls": int(features.get('num_external_calls', 0)),
                "max_complexity": int(features.get('max_cyclomatic_complexity', 0)),
                "has_inline_assembly": bool(features.get('has_inline_assembly', False))
            },
            
            # Slither detectors
            "static_analysis": {
                "total_issues": int(features.get('total_detector_hits', 0)),
                "high_severity": int(features.get('high_severity_count', 0)),
                "medium_severity": int(features.get('medium_severity_count', 0)),
                "low_severity": int(features.get('low_severity_count', 0)),
                "has_reentrancy": bool(features.get('has_reentrancy', False)),
                "has_unchecked_call": bool(features.get('has_unchecked_call', False)),
                "has_tx_origin": bool(features.get('has_tx_origin', False))
            }
        }
        
        # Add SHAP if available
        if 'shap_explanation' in result and 'top_features' in result['shap_explanation']:
            llm_output['explainability'] = {
                "method": "SHAP (SHapley Additive exPlanations)",
                "top_risk_factors": [
                    {
                        "feature": f['feature'],
                        "contribution": round(f['shap_value'], 3),
                        "direction": "increases risk" if f['shap_value'] > 0 else "decreases risk"
                    }
                    for f in result['shap_explanation']['top_features'][:5]
                ]
            }
        
        # Add override info if applicable
        if result.get('override_reason'):
            llm_output['override'] = {
                "triggered": True,
                "reason": result['override_reason']
            }
        
        return llm_output