"""
Production Hybrid Predictor - OPTIMIZED
========================================
Combines ML model with semantic security rules for production deployment

OPTIMIZED CONFIGURATION (Dec 20, 2025):
- ML Weight: 0.60 | Semantic Weight: 0.40
- Threshold: 0.60 (increased from 0.50)
- Adversarial Accuracy: 76% (improved from 44%)
"""

import numpy as np
import pandas as pd
import joblib
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class HybridPredictor:
    """
    Production-ready hybrid vulnerability predictor - OPTIMIZED
    
    Combines XGBoost ML model with semantic security rules
    """
    
    # OPTIMIZED DEFAULTS (100% recall, 48% F1)
    # Config: Security-First (catches all vulnerabilities)
    DEFAULT_ML_WEIGHT = 0.30
    DEFAULT_SEMANTIC_WEIGHT = 0.70
    DEFAULT_THRESHOLD = 0.20  # Low threshold for maximum recall
    
    def __init__(self, model_path: str = None, scaler_path: str = None, metadata_path: str = None):
        """
        Initialize hybrid predictor
        
        Args:
            model_path: Path to trained ML model (.pkl)
            scaler_path: Path to feature scaler (.pkl)
            metadata_path: Path to metadata JSON with feature list
        """
        # Correct path: models/ at project root
        models_dir = Path(__file__).parent.parent.parent.parent.parent / 'models'
        
        # Load ML model
        if model_path is None:
            model_path = models_dir / 'production_model.pkl'
        
        if scaler_path is None:
            scaler_path = models_dir / 'production_scaler.pkl'
        
        try:
            self.ml_model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            logger.info(f"✅ Loaded ML model from {model_path}")
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            raise
        
        # Load feature names from metadata
        if metadata_path is None:
            # Find latest metadata file
            metadata_files = sorted(models_dir.glob('semantic_metadata_*.json'))
            if metadata_files:
                metadata_path = metadata_files[-1]
            else:
                # Try production metadata
                metadata_path = models_dir / 'PRODUCTION_MODEL_README.json'
        
        if Path(metadata_path).exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                self.feature_names = metadata.get('feature_list', None)
                if self.feature_names:
                    logger.info(f"✅ Loaded {len(self.feature_names)} feature names from metadata")
        
        # If still no feature names, try to get from model
        if not hasattr(self, 'feature_names') or self.feature_names is None:
            try:
                self.feature_names = self.ml_model.get_booster().feature_names
                logger.info("✅ Loaded feature names from model")
            except:
                logger.warning("⚠️  Could not load feature names, will use default order")
                # Define default feature order (93 features)
                self.feature_names = self._get_default_features()
        
        # Semantic rule weights
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
        """Return default feature list in expected order"""
        # Vulnerability flags (23)
        vuln_flags = [
            'has_reentrancy', 'has_access_control_issues', 'has_timestamp_dependency',
            'has_unchecked_call', 'has_reentrancy_unlimited', 'has_reentrancy_benign',
            'has_reentrancy_events', 'has_unchecked_transfer', 'has_controlled_delegatecall',
            'has_delegatecall_loop', 'has_uninitialized_state', 'has_uninitialized_storage',
            'has_uninitialized_local', 'has_tx_origin', 'has_inline_assembly',
            'has_locked_ether', 'has_msg_value_loop', 'has_shadowing_state',
            'has_shadowing_builtin', 'has_shadowing_abstract', 'has_unused_state_vars',
            'has_unused_return_values', 'has_incorrect_solc_version', 'has_floating_pragma',
            'has_outdated_compiler'
        ]
        
        # Severity counts (3)
        severity = ['high_severity_count', 'medium_severity_count', 'low_severity_count']
        
        # AST features (17)
        ast_features = [
            'num_functions', 'num_external_calls', 'num_state_vars', 'num_modifiers',
            'max_cyclomatic_complexity', 'num_low_level_calls', 'lines_of_code',
            'num_contracts_in_file', 'num_dependencies', 'avg_function_complexity',
            'num_functions_high_complexity', 'num_comments', 'comment_to_code_ratio',
            'num_payable_functions', 'num_library_calls', 'inheritance_depth',
            'num_unused_functions'
        ]
        
        # Detector stats (9)
        detector_stats = [
            'high_confidence_detectors', 'medium_confidence_detectors',
            'low_confidence_detectors', 'security_detectors_triggered',
            'optimization_detectors_triggered', 'total_detector_hits',
            'unique_vulnerability_types', 'detectors_per_function', 'detectors_per_loc'
        ]
        
        # Risk scores (4)
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
        
        # Semantic features (8)
        semantic_features = [
            'cei_violations', 'cei_safe_functions', 'cei_pattern_score',
            'has_reentrancy_guard', 'functions_with_reentrancy_guard',
            'state_before_call_count', 'state_after_call_count',
            'unchecked_calls_in_critical_context'
        ]
        
        return (vuln_flags + severity + ast_features + detector_stats + 
                risk_scores + graph_features + semantic_features)
        
    def calculate_semantic_risk(self, features: Dict) -> Tuple[float, List[str]]:
        """Calculate semantic risk score based on security patterns"""
        risk = 0.0
        reasons = []
        
        # CEI Pattern Violations (HIGH RISK)
        cei_violations = features.get('cei_violations', 0)
        if cei_violations > 0:
            violation_risk = self.semantic_weights['cei_violation'] * min(cei_violations / 5, 1.0)
            risk += violation_risk
            reasons.append(f"🚨 CEI violations: {cei_violations} (+{violation_risk:.0%} risk)")
        
        # Low CEI Compliance Score (MEDIUM RISK)
        cei_score = features.get('cei_pattern_score', 1.0)
        if cei_score < 0.8:
            score_risk = self.semantic_weights['cei_score_low'] * (1.0 - cei_score)
            risk += score_risk
            reasons.append(f"⚠️  Low CEI score: {cei_score:.2f} (+{score_risk:.0%} risk)")
        
        # State Modifications After External Calls (HIGH RISK)
        state_after_call = features.get('state_after_call_count', 0)
        if state_after_call > 0:
            state_risk = self.semantic_weights['state_after_call'] * min(state_after_call / 3, 1.0)
            risk += state_risk
            reasons.append(f"🚨 State-after-call: {state_after_call} (+{state_risk:.0%} risk)")
        
        # Unchecked Calls in Critical Context (MEDIUM RISK)
        unchecked_critical = features.get('unchecked_calls_in_critical_context', 0)
        if unchecked_critical > 0:
            unchecked_risk = self.semantic_weights['unchecked_critical'] * min(unchecked_critical / 2, 1.0)
            risk += unchecked_risk
            reasons.append(f"⚠️  Unchecked critical calls: {unchecked_critical} (+{unchecked_risk:.0%} risk)")
        
        # Reentrancy Guard Bonus (REDUCES RISK)
        has_guard = features.get('has_reentrancy_guard', False)
        num_external_calls = features.get('num_external_calls', 0)
        
        if has_guard and num_external_calls > 0:
            risk *= (1 + self.semantic_weights['reentrancy_guard_bonus'])
            reasons.append(f"✅ Reentrancy guard detected (-50% risk)")
        
        # Perfect CEI compliance (POSITIVE SIGNAL)
        if cei_score == 1.0 and cei_violations == 0:
            reasons.append(f"✅ Perfect CEI compliance")
        
        return min(risk, 1.0), reasons
    
    def check_overrides(self, features: Dict, ml_score: float, semantic_score: float) -> Optional[Tuple[int, str]]:
        """Check if semantic rules should override ML prediction"""
        # AUTO VULNERABLE: Multiple CEI violations
        cei_violations = features.get('cei_violations', 0)
        if cei_violations >= self.override_thresholds['high_cei_violations']:
            return (1, f"OVERRIDE: {cei_violations} CEI violations → VULNERABLE")
        
        # AUTO SAFE: Perfect CEI + Guard + Low ML score
        cei_score = features.get('cei_pattern_score', 0)
        has_guard = features.get('has_reentrancy_guard', False)
        
        if cei_score == 1.0 and has_guard and ml_score < 0.3:
            return (0, f"OVERRIDE: Perfect CEI + guard → SAFE")
        
        return None
    
    def predict(
        self,
        features: Dict,
        ml_weight: float = None,
        semantic_weight: float = None,
        threshold: float = None,
        return_details: bool = True
    ) -> Dict:
        """
        Predict vulnerability with hybrid approach
        
        Args:
            features: Contract features dictionary
            ml_weight: Weight for ML model (0-1) [default: 0.60]
            semantic_weight: Weight for semantic score (0-1) [default: 0.40]
            threshold: Classification threshold [default: 0.60]
            return_details: Include detailed reasoning
        
        Returns:
            Dictionary with prediction results
        """
        # Use optimized defaults
        if ml_weight is None:
            ml_weight = self.DEFAULT_ML_WEIGHT
        if semantic_weight is None:
            semantic_weight = self.DEFAULT_SEMANTIC_WEIGHT
        if threshold is None:
            threshold = self.DEFAULT_THRESHOLD
        
        # Validate weights
        assert abs(ml_weight + semantic_weight - 1.0) < 0.001, "Weights must sum to 1.0"
        
        # Extract feature vector for ML model
        X = np.array([features.get(f, 0) for f in self.feature_names]).reshape(1, -1)
        X_scaled = self.scaler.transform(X)
        
        # Get ML prediction
        ml_proba = self.ml_model.predict_proba(X_scaled)[0, 1]
        
        # Calculate semantic risk
        semantic_score, semantic_reasons = self.calculate_semantic_risk(features)
        
        # Check for overrides
        override = self.check_overrides(features, ml_proba, semantic_score)
        
        if override:
            prediction, override_reason = override
            final_score = 1.0 if prediction == 1 else 0.0
            method = "OVERRIDE"
        else:
            # Weighted ensemble
            final_score = (ml_weight * ml_proba) + (semantic_weight * semantic_score)
            prediction = 1 if final_score > threshold else 0
            override_reason = None
            method = "HYBRID"
        
        result = {
            'prediction': prediction,
            'prediction_label': 'VULNERABLE' if prediction == 1 else 'SAFE',
            'confidence': final_score,
            'method': method,
        }
        
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
        
        return result
    
    def predict_batch(
        self,
        contracts: List[Dict],
        ml_weight: float = None,
        semantic_weight: float = None,
        threshold: float = None
    ) -> pd.DataFrame:
        """Predict vulnerabilities for multiple contracts"""
        results = []
        
        for features in contracts:
            pred = self.predict(features, ml_weight, semantic_weight, threshold)
            results.append({
                'contract_name': features.get('contract_name', 'Unknown'),
                'prediction': pred['prediction_label'],
                'confidence': pred['confidence'],
                'method': pred['method'],
                'ml_score': pred['ml_score'],
                'semantic_score': pred['semantic_score'],
                'risk_level': pred['risk_level'],
            })
        
        return pd.DataFrame(results)
    
    def _get_risk_level(self, score: float) -> str:
        """Convert score to risk level"""
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
