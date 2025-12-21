"""
Production Hybrid Predictor with SHAP Explainability
====================================================
Combines ML model with semantic security rules AND per-prediction explanations.

WHAT'S NEW (Dec 21, 2024):
- SHAP TreeExplainer integration for XGBoost/RandomForest
- Waterfall plots showing feature contributions
- Top-K most important features per prediction
- Combined ML + semantic explanations

EDUCATIONAL NOTES:
- SHAP = SHapley Additive exPlanations (game theory)
- TreeExplainer = Fast SHAP for tree models (XGBoost, RF)
- Waterfall plot = Visual breakdown of prediction
- Base value = Expected prediction before seeing features

ARCHITECTURE:
HybridPredictor
├─ ML Component (XGBoost)
│  ├─ predict_proba() → 0.75
│  └─ SHAP explain() → Why 0.75?
├─ Semantic Component (Rules)
│  └─ Calculate CEI risk → 0.65
└─ Ensemble (weighted) → Final 0.70

Author: Ali
Date: December 21, 2024
"""

import numpy as np
import pandas as pd
import joblib
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

# SHAP for explainability - NEW!
import shap

logger = logging.getLogger(__name__)


class HybridPredictor:
    """
    Production-ready hybrid vulnerability predictor with SHAP explainability.
    
    WHAT IT DOES:
    1. Predicts vulnerability using ensemble (ML + semantic rules)
    2. Explains predictions with SHAP values (feature contributions)
    3. Provides human-readable explanations ("3 CEI violations found")
    4. Handles override logic (domain knowledge > ML when appropriate)
    
    WHY HYBRID:
    - ML catches general patterns (learns from 963 contracts)
    - Semantic rules catch specific vulnerabilities (CEI violations)
    - SHAP explains ML predictions (builds trust)
    - Overrides prevent ML confusion on edge cases
    
    USAGE:
        predictor = HybridPredictor()
        result = predictor.predict(contract_features, return_details=True)
        
        # result includes:
        # - prediction: 0 (safe) or 1 (vulnerable)
        # - confidence: 0.0 to 1.0
        # - shap_explanation: Top features with contributions
        # - semantic_reasons: List of security issues found
    """
    
    # Optimized defaults (from hybrid optimization)
    # EDUCATIONAL NOTE: These weights were tuned via grid search
    # 30% ML, 70% semantic = best adversarial accuracy (76%)
    DEFAULT_ML_WEIGHT = 0.60      # Optimized for adversarial robustness
    DEFAULT_SEMANTIC_WEIGHT = 0.40
    DEFAULT_THRESHOLD = 0.60
    
    def __init__(
        self, 
        model_path: str = None, 
        scaler_path: str = None, 
        metadata_path: str = None,
        enable_shap: bool = True
    ):
        """
        Initialize hybrid predictor with SHAP explainability.
        
        PARAMETERS:
            model_path: Path to trained ML model (.pkl)
            scaler_path: Path to feature scaler (.pkl)
            metadata_path: Path to metadata JSON with feature list
            enable_shap: Whether to load SHAP explainer (default: True)
                        Set to False for faster initialization if explanations not needed
        
        EDUCATIONAL NOTE: enable_shap parameter lets you trade speed for explainability
        - True: Slower init (~5s), can explain predictions
        - False: Fast init (~0.5s), predictions only (no explanations)
        """
        # Determine model directory (handles different execution contexts)
        # EDUCATIONAL NOTE: This path resolution works whether you run from:
        # - scripts/3_training/
        # - project root
        # - anywhere else
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
        # EDUCATIONAL NOTE: Feature names needed for:
        # 1. Extracting features in correct order
        # 2. SHAP explanations (labeling contributions)
        if metadata_path is None:
            # Try to find latest metadata file
            metadata_files = sorted(models_dir.glob('semantic_metadata_*.json'))
            if metadata_files:
                metadata_path = metadata_files[-1]
            else:
                metadata_path = models_dir / 'PRODUCTION_MODEL_README.json'
        
        if Path(metadata_path).exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                self.feature_names = metadata.get('feature_list', None)
                if self.feature_names:
                    logger.info(f"✅ Loaded {len(self.feature_names)} feature names from metadata")
        
        # Fallback: try to get feature names from model
        if not hasattr(self, 'feature_names') or self.feature_names is None:
            try:
                self.feature_names = self.ml_model.get_booster().feature_names
                logger.info("✅ Loaded feature names from model")
            except:
                logger.warning("⚠️ Could not load feature names, using default order")
                self.feature_names = self._get_default_features()
        
        # Initialize SHAP explainer (optional)
        # EDUCATIONAL NOTE: TreeExplainer is model-specific and FAST
        # - Works for: XGBoost, RandomForest, LightGBM, CatBoost
        # - Time: O(TLD²) where T=trees, L=leaves, D=depth
        # - For 300 trees, depth 6: ~0.1 seconds per prediction
        # Initialize SHAP explainer (with calibrated model support)
        # EDUCATIONAL NOTE: CalibratedClassifierCV wraps the base model
        # We need to extract the base estimator for SHAP
        self.shap_explainer = None
        if enable_shap:
            try:
                logger.info("🔍 Initializing SHAP TreeExplainer...")
                
                # Check if model is calibrated (wrapper)
                # EDUCATIONAL NOTE: CalibratedClassifierCV has .calibrated_classifiers_
                # which is a list of (classifier, calibrator) pairs from CV
                if hasattr(self.ml_model, 'calibrated_classifiers_'):
                    # Extract base model from first calibrated classifier
                    # EDUCATIONAL NOTE: We use [0] because CV creates multiple calibrators
                    # They're all trained on same base model type, so any works for SHAP
                    base_model = self.ml_model.calibrated_classifiers_[0].estimator
                    logger.info("   Detected calibrated model, extracting base estimator...")
                    self.shap_explainer = shap.TreeExplainer(base_model)
                else:
                    # Direct model (not calibrated)
                    self.shap_explainer = shap.TreeExplainer(self.ml_model)
                
                logger.info("✅ SHAP explainer ready")
            except Exception as e:
                logger.warning(f"⚠️ Could not initialize SHAP: {e}")
                logger.warning("   Predictions will work but explanations unavailable")
        # Semantic rule weights (for vulnerability scoring)
        # EDUCATIONAL NOTE: These weights define how semantic features combine
        # Positive weights = increase risk, Negative weights = decrease risk
        self.semantic_weights = {
            'cei_violation': 0.40,           # CEI violations are CRITICAL
            'cei_score_low': 0.20,           # Low CEI compliance is risky
            'state_after_call': 0.30,        # State changes after calls = reentrancy risk
            'unchecked_critical': 0.20,      # Unchecked calls in critical contexts
            'reentrancy_guard_bonus': -0.50, # Guard reduces risk by 50%
        }
        
        # Override thresholds (when to ignore ML and force prediction)
        # EDUCATIONAL NOTE: Domain knowledge overrides when:
        # 1. Evidence is overwhelming (3+ CEI violations = definitely vulnerable)
        # 2. Safety is guaranteed (perfect CEI + guard = definitely safe)
        self.override_thresholds = {
            'high_cei_violations': 3,      # 3+ violations → force VULNERABLE
            'perfect_cei_with_guard': True, # Perfect CEI + guard → force SAFE
        }
        
    def _get_default_features(self) -> List[str]:
        """
        Return default feature list in expected order (93 features total).
        
        EDUCATIONAL NOTE: Feature order MATTERS because:
        - ML models expect features in training order
        - Wrong order → wrong predictions (silently!)
        - This method ensures consistency even without metadata
        
        FEATURE GROUPS:
        - Vulnerability flags (23): Binary indicators from Slither
        - Severity counts (3): High/medium/low issue counts
        - AST features (17): Code structure metrics
        - Detector stats (9): Slither analysis metadata
        - Risk scores (3): Composite risk indicators
        - Graph features (25): CFG, CG, DFG properties
        - Semantic features (8): CEI pattern analysis ⭐ YOUR INNOVATION
        """
        # [Previous _get_default_features implementation - keep as is]
        vulnerability_flags = [
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
        
        severity = ['high_severity_count', 'medium_severity_count', 'low_severity_count']
        
        ast_features = [
            'num_functions', 'num_external_calls', 'num_state_vars', 'num_modifiers',
            'max_cyclomatic_complexity', 'num_low_level_calls', 'lines_of_code',
            'num_contracts_in_file', 'num_dependencies', 'avg_function_complexity',
            'num_functions_high_complexity', 'num_comments', 'comment_to_code_ratio',
            'num_payable_functions', 'num_library_calls', 'inheritance_depth',
            'num_unused_functions'
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
        
        return (vulnerability_flags + severity + ast_features + detector_stats + 
                risk_scores + graph_features + semantic_features)
        
    def calculate_semantic_risk(self, features: Dict) -> Tuple[float, List[str]]:
        """
        Calculate semantic risk score based on security patterns.
        
        WHAT THIS DOES:
        1. Analyzes CEI (Checks-Effects-Interactions) pattern compliance
        2. Checks for reentrancy guards
        3. Detects state modifications after external calls
        4. Returns risk score (0-1) and human-readable reasons
        
        WHY SEPARATE FROM ML:
        - Semantic rules are explainable (CEI violation at line 67)
        - ML learns patterns but can't articulate specific issues
        - Combination gives best of both worlds
        
        RETURNS:
            tuple: (risk_score: float, reasons: List[str])
        """
        risk = 0.0
        reasons = []
        
        # CEI Pattern Violations (HIGH RISK)
        # EDUCATIONAL NOTE: CEI = Checks-Effects-Interactions pattern
        # Safe: balance -= amount; externalCall();
        # Unsafe: externalCall(); balance -= amount; ← REENTRANCY!
        cei_violations = features.get('cei_violations', 0)
        if cei_violations > 0:
            violation_risk = self.semantic_weights['cei_violation'] * min(cei_violations / 5, 1.0)
            risk += violation_risk
            reasons.append(f"🚨 CEI violations: {cei_violations} (+{violation_risk:.0%} risk)")
        
        # Low CEI Compliance Score (MEDIUM RISK)
        # EDUCATIONAL NOTE: cei_pattern_score = ratio of safe functions
        # 1.0 = perfect (all functions follow CEI), 0.0 = terrible
        cei_score = features.get('cei_pattern_score', 1.0)
        if cei_score < 0.8:
            score_risk = self.semantic_weights['cei_score_low'] * (1.0 - cei_score)
            risk += score_risk
            reasons.append(f"⚠️ Low CEI score: {cei_score:.2f} (+{score_risk:.0%} risk)")
        
        # State Modifications After External Calls (HIGH RISK)
        # EDUCATIONAL NOTE: This is the CORE reentrancy vulnerability pattern
        # externalCall() then balance-- = attacker can re-enter with old balance
        state_after_call = features.get('state_after_call_count', 0)
        if state_after_call > 0:
            state_risk = self.semantic_weights['state_after_call'] * min(state_after_call / 3, 1.0)
            risk += state_risk
            reasons.append(f"🚨 State-after-call: {state_after_call} (+{state_risk:.0%} risk)")
        
        # Unchecked Calls in Critical Context (MEDIUM RISK)
        # EDUCATIONAL NOTE: call() returns bool but result not checked
        # If call fails silently, contract logic continues with wrong assumptions
        unchecked_critical = features.get('unchecked_calls_in_critical_context', 0)
        if unchecked_critical > 0:
            unchecked_risk = self.semantic_weights['unchecked_critical'] * min(unchecked_critical / 2, 1.0)
            risk += unchecked_risk
            reasons.append(f"⚠️ Unchecked critical calls: {unchecked_critical} (+{unchecked_risk:.0%} risk)")
        
        # Reentrancy Guard Bonus (REDUCES RISK)
        # EDUCATIONAL NOTE: nonReentrant modifier prevents recursive calls
        # modifier nonReentrant() { require(!locked); locked = true; _; locked = false; }
        has_guard = features.get('has_reentrancy_guard', False)
        num_external_calls = features.get('num_external_calls', 0)
        
        if has_guard and num_external_calls > 0:
            risk *= (1 + self.semantic_weights['reentrancy_guard_bonus'])
            reasons.append(f"✅ Reentrancy guard detected (-50% risk)")
        
        # Perfect CEI compliance (POSITIVE SIGNAL)
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
        Check if semantic rules should override ML prediction.
        
        WHEN TO OVERRIDE:
        1. Multiple CEI violations (≥3) → Force VULNERABLE
           WHY: 3+ violations is overwhelming evidence, trust semantic analysis
        2. Perfect CEI + guard + low ML score → Force SAFE
           WHY: Strong safety signals override ML uncertainty
        
        EDUCATIONAL NOTE: Overrides implement "domain knowledge trumps ML"
        - ML can be confused by dataset artifacts
        - Semantic rules are trustworthy (based on security principles)
        - Hybrid approach: ML for general patterns, rules for edge cases
        
        RETURNS:
            None if no override needed
            (prediction, reason) if override triggered
        """
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
    
    def explain_with_shap(
        self, 
        X_scaled: np.ndarray, 
        top_k: int = 10
    ) -> Dict:
        """
        Generate SHAP explanation for a single prediction.
        
        WHAT SHAP DOES:
        - Calculates each feature's contribution to prediction
        - Uses game theory (Shapley values) for fair attribution
        - Handles feature interactions correctly
        
        HOW TO READ RESULTS:
        - Positive SHAP value = pushes toward VULNERABLE
        - Negative SHAP value = pushes toward SAFE
        - Sum of all SHAP values = prediction - base_value
        
        EXAMPLE OUTPUT:
        {
            'base_value': 0.20,  # Expected prediction before seeing features
            'prediction_value': 0.85,  # Actual prediction after seeing features
            'top_features': [
                {'feature': 'cei_violations', 'value': 3, 'shap_value': +0.45},
                {'feature': 'num_external_calls', 'value': 45, 'shap_value': +0.25},
                {'feature': 'has_reentrancy_guard', 'value': 0, 'shap_value': +0.20},
            ]
        }
        
        PARAMETERS:
            X_scaled: Scaled feature vector (1 x 93 numpy array)
            top_k: Number of most important features to return
        
        RETURNS:
            Dictionary with base_value, prediction_value, and top_features
        """
        if self.shap_explainer is None:
            logger.warning("⚠️ SHAP explainer not initialized, returning empty explanation")
            return {
                'base_value': 0.0,
                'prediction_value': 0.0,
                'top_features': [],
                'error': 'SHAP not available'
            }
        
        try:
            # Calculate SHAP values for this prediction
            # EDUCATIONAL NOTE: shap_values has shape (1, n_features)
            # Each value shows how much that feature pushed the prediction
            shap_values = self.shap_explainer.shap_values(X_scaled)
            
            # Get base value (expected prediction before seeing features)
            # EDUCATIONAL NOTE: This is the training set average prediction
            # For balanced dataset: ~0.5, For imbalanced: ~class ratio
            base_value = self.shap_explainer.expected_value
            
            # Get prediction value (actual prediction after seeing features)
            prediction_value = self.ml_model.predict_proba(X_scaled)[0, 1]
            
            # Extract feature values (unscale for human readability)
            # EDUCATIONAL NOTE: X_scaled has mean=0, std=1
            # We want original values for display (e.g., "3 CEI violations" not "1.5 std")
            # But unscaling needs original data statistics - so we use scaled values for now
            feature_values = X_scaled[0]
            
            # Create list of (feature_name, feature_value, shap_value) tuples
            feature_explanations = []
            for i, (name, value, shap_val) in enumerate(zip(
                self.feature_names, feature_values, shap_values[0]
            )):
                feature_explanations.append({
                    'feature': name,
                    'value': float(value),  # Convert numpy to Python float
                    'shap_value': float(shap_val),
                    'abs_shap': abs(float(shap_val))  # For sorting
                })
            
            # Sort by absolute SHAP value (most impactful features first)
            feature_explanations.sort(key=lambda x: x['abs_shap'], reverse=True)
            
            # Keep only top K features
            top_features = feature_explanations[:top_k]
            
            # Remove abs_shap (was only for sorting)
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
        explain: bool = True
    ) -> Dict:
        """
        Predict vulnerability with hybrid approach and SHAP explanations.
        
        COMPLETE WORKFLOW:
        1. Extract feature vector from features dict
        2. Scale features (normalize to mean=0, std=1)
        3. Get ML prediction (XGBoost probability)
        4. Get semantic risk (CEI analysis)
        5. Check for overrides (domain knowledge)
        6. Combine predictions (weighted ensemble)
        7. Generate SHAP explanation (if requested)
        8. Return comprehensive results
        
        PARAMETERS:
            features: Dict of contract features (93 features)
            ml_weight: Weight for ML prediction (default: 0.30)
            semantic_weight: Weight for semantic risk (default: 0.70)
            threshold: Classification threshold (default: 0.20)
            return_details: Include all metrics in response (default: True)
            explain: Generate SHAP explanation (default: True)
                    Set to False for faster predictions when explanations not needed
        
        RETURNS:
            Dict with prediction, confidence, explanations, and metadata
        """
        # Use optimized defaults
        if ml_weight is None:
            ml_weight = self.DEFAULT_ML_WEIGHT
        if semantic_weight is None:
            semantic_weight = self.DEFAULT_SEMANTIC_WEIGHT
        if threshold is None:
            threshold = self.DEFAULT_THRESHOLD
        
        # Validate weights sum to 1.0
        assert abs(ml_weight + semantic_weight - 1.0) < 0.001, "Weights must sum to 1.0"
        
        # Extract feature vector for ML model (must be in training order!)
        # EDUCATIONAL NOTE: Wrong order = wrong predictions (silently!)
        # Example: If model trained with [cei, loc] but we pass [loc, cei]
        # → Model thinks "loc=3 cei=5000" when reality is "cei=3 loc=5000"
        X = pd.DataFrame(
            [[features.get(f, 0) for f in self.feature_names]],
            columns=self.feature_names
        )
        X_scaled = self.scaler.transform(X)
                
        # Get ML prediction (probability of vulnerable)
        ml_proba = self.ml_model.predict_proba(X_scaled)[0, 1]
        
        # Calculate semantic risk (CEI pattern analysis)
        semantic_score, semantic_reasons = self.calculate_semantic_risk(features)
        
        # Check for overrides (domain knowledge trumps ML)
        override = self.check_overrides(features, ml_proba, semantic_score)
        
        if override:
            prediction, override_reason = override
            final_score = 1.0 if prediction == 1 else 0.0
            method = "OVERRIDE"
        else:
            # Weighted ensemble (ML + semantic)
            final_score = (ml_weight * ml_proba) + (semantic_weight * semantic_score)
            prediction = 1 if final_score >= threshold else 0
            override_reason = None
            method = "HYBRID"
        
        # Base result (always included)
        result = {
            'prediction': prediction,
            'prediction_label': 'VULNERABLE' if prediction == 1 else 'SAFE',
            'confidence': final_score,
            'method': method,
        }
        
        # Add detailed information (if requested)
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
        
        # Add SHAP explanation (if requested and available)
        # EDUCATIONAL NOTE: SHAP adds ~0.1 seconds per prediction
        # Disable if doing batch predictions (1000s of contracts)
        if explain and self.shap_explainer is not None:
            result['shap_explanation'] = self.explain_with_shap(X_scaled, top_k=10)
        
        return result
    
    def predict_batch(
        self,
        contracts: List[Dict],
        ml_weight: float = None,
        semantic_weight: float = None,
        threshold: float = None,
        explain: bool = False  # Default False for batch (performance)
    ) -> pd.DataFrame:
        """
        Predict vulnerabilities for multiple contracts.
        
        EDUCATIONAL NOTE: Batch prediction is more efficient than loop
        - Can leverage vectorization (NumPy operations on arrays)
        - SHAP explanations disabled by default (slow for large batches)
        - Use explain=True only for small batches (<100 contracts)
        
        PARAMETERS:
            contracts: List of feature dictionaries
            ml_weight: Weight for ML component
            semantic_weight: Weight for semantic component
            threshold: Classification threshold
            explain: Whether to include SHAP explanations (slow!)
        
        RETURNS:
            DataFrame with predictions and key metrics
        """
        results = []
        
        for features in contracts:
            pred = self.predict(
                features, ml_weight, semantic_weight, threshold, 
                return_details=True, explain=explain
            )
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
        """
        Convert numerical score to human-readable risk level.
        
        EDUCATIONAL NOTE: Risk levels for user communication
        - CRITICAL: Immediate action required
        - HIGH: Review urgently
        - MEDIUM: Review soon
        - LOW: Consider reviewing
        - MINIMAL: Likely safe
        """
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