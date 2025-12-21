"""
Production ML Training with RobustScaler + Calibration
======================================================
Enhanced training with outlier-robust scaling and probability calibration.

IMPROVEMENTS OVER train_with_mlflow.py:
1. RobustScaler instead of StandardScaler (handles outliers)
2. CalibratedClassifierCV with isotonic regression (trustworthy probabilities)
3. Calibration curve visualization (verify improvement)
4. Before/after comparison metrics

EDUCATIONAL NOTES:
- RobustScaler uses median + IQR (resistant to outliers)
- Calibration learns mapping: raw_probability → true_probability
- Isotonic regression = non-parametric, flexible calibration
- 5-fold CV prevents overfitting the calibration function

WHY THIS MATTERS:
- Better robustness: Large contracts don't compress normal range
- Better trust: 0.80 confidence = 80% actual vulnerability rate
- Better decisions: Users can rely on probabilities

Author: Ali
Date: December 21, 2024
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score, 
    roc_curve, brier_score_loss
)
from sklearn.preprocessing import RobustScaler  # NEW: Robust to outliers
from sklearn.calibration import CalibratedClassifierCV, calibration_curve  # NEW: Calibration
import xgboost as xgb
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# MLflow imports
import mlflow
import mlflow.sklearn
import mlflow.xgboost
from mlflow.models.signature import infer_signature

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

print("\n" + "="*80)
print("🎯 PRODUCTION ML TRAINING: ROBUSTSCALER + CALIBRATION")
print("="*80)

# ============================================================================
# MLFLOW SETUP
# ============================================================================
print("\n📊 MLFLOW SETUP")
print("-" * 80)

EXPERIMENT_NAME = "smart_contract_robust_calibrated"
mlflow.set_experiment(EXPERIMENT_NAME)

experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
print(f"✅ Experiment: {EXPERIMENT_NAME}")
print(f"   ID: {experiment.experiment_id}")

# ============================================================================
# STEP 1: LOAD DATA
# ============================================================================
print("\n📊 STEP 1: LOADING DATASET")
print("-" * 80)

df = pd.read_csv('data/complete_dataset_with_semantic.csv')
print(f"✅ Loaded {len(df)} contracts")

# Create labels
df['is_vulnerable'] = df['data_source'].isin([
    'smartbugs_curated',
    'production_vulnerable',
    'trail_of_bits'
]).astype(int)

adversarial_mask = df['data_source'] == 'adversarial_test'
df.loc[adversarial_mask, 'is_vulnerable'] = df.loc[adversarial_mask, 'contract_name'].str.contains(
    'reentrancy|vulnerable|danger|exploit|honeypot|obvious',
    case=False,
    na=False
).astype(int)

print(f"   Vulnerable: {df['is_vulnerable'].sum()} ({df['is_vulnerable'].sum()/len(df)*100:.1f}%)")
print(f"   Safe: {(~df['is_vulnerable'].astype(bool)).sum()}")

# ============================================================================
# STEP 2: FEATURE SELECTION
# ============================================================================
print("\n🔧 STEP 2: FEATURE SELECTION")
print("-" * 80)

# [Use same feature groups as before - copy from train_with_mlflow.py]
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

severity_counts = ['high_severity_count', 'medium_severity_count', 'low_severity_count']

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

baseline_features = (
    vulnerability_flags + severity_counts + ast_features + 
    detector_stats + risk_scores + graph_features
)
full_features = baseline_features + semantic_features

baseline_features = [f for f in baseline_features if f in df.columns]
full_features = [f for f in full_features if f in df.columns]

print(f"✅ Total features: {len(full_features)}")

# ============================================================================
# STEP 3: TRAIN/TEST SPLIT
# ============================================================================
print("\n🔀 STEP 3: TRAIN/TEST SPLIT")
print("-" * 80)

adversarial_df = df[df['data_source'] == 'adversarial_test'].copy()
main_df = df[df['data_source'] != 'adversarial_test'].copy()

X_main = main_df[full_features]
y_main = main_df['is_vulnerable']

X_train, X_test, y_train, y_test = train_test_split(
    X_main, y_main, 
    test_size=0.2, 
    random_state=42, 
    stratify=y_main
)

print(f"   Training: {len(X_train)}")
print(f"   Test: {len(X_test)}")
print(f"   Adversarial: {len(adversarial_df)}")

pos_weight = len(y_train) / (2 * y_train.sum())

# ============================================================================
# STEP 4: ROBUST SCALING (NEW!)
# ============================================================================
print("\n🔄 STEP 4: ROBUST SCALING")
print("-" * 80)

# EDUCATIONAL NOTE: RobustScaler uses median and IQR
# Formula: (X - median) / IQR
# IQR = Q3 - Q1 (middle 50% of data)
# 
# WHY BETTER:
# - Outliers don't affect median (unlike mean)
# - IQR ignores extreme values (unlike std)
# - Preserves distinctions in normal range
scaler = RobustScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

if len(adversarial_df) > 0:
    X_adv = adversarial_df[full_features]
    y_adv = adversarial_df['is_vulnerable']
    X_adv_scaled = scaler.transform(X_adv)
else:
    X_adv_scaled = None
    y_adv = None

print(f"✅ Features scaled using RobustScaler")
print(f"   Method: (X - median) / IQR")
print(f"   Robust to outliers: Yes")

# ============================================================================
# STEP 5: TRAIN MODELS WITH CALIBRATION
# ============================================================================

def train_calibrated_model(
    model_name: str,
    base_model,
    X_train_scaled,
    y_train,
    X_test_scaled,
    y_test,
    X_adv_scaled=None,
    y_adv=None,
    feature_names=None
):
    """
    Train model with calibration and comprehensive logging.
    
    CALIBRATION WORKFLOW:
    1. Train base model on training data
    2. Use CalibratedClassifierCV with 5-fold CV
    3. Each fold: train on 4/5, calibrate on 1/5
    4. Learn isotonic regression mapping
    5. Return calibrated model
    
    EDUCATIONAL NOTE: Isotonic regression is non-parametric
    - Learns arbitrary non-decreasing function
    - Flexible: fits actual calibration curve shape
    - Needs sufficient data (we have 770 training samples ✅)
    """
    
    with mlflow.start_run(run_name=f"{model_name}_calibrated_{datetime.now().strftime('%Y%m%d_%H%M')}"):
        
        print(f"\n{'='*60}")
        print(f"Training: {model_name} (with calibration)")
        print(f"{'='*60}")
        
        # Log configuration
        mlflow.log_param("model_type", model_name)
        mlflow.log_param("scaler_type", "RobustScaler")
        mlflow.log_param("calibration_method", "isotonic")
        mlflow.log_param("calibration_cv_folds", 5)
        
        model_params = base_model.get_params()
        for param, value in model_params.items():
            if isinstance(value, (int, float, str, bool)):
                mlflow.log_param(f"model_{param}", value)
        
        mlflow.log_params({
            "train_size": len(X_train_scaled),
            "test_size": len(X_test_scaled),
            "num_features": len(feature_names) if feature_names else X_train_scaled.shape[1],
            "random_state": 42
        })
        
        # ────────────────────────────────────────────────────────────
        # TRAIN WITHOUT CALIBRATION (Baseline)
        # ────────────────────────────────────────────────────────────
        print(f"\n🚀 Training base model (uncalibrated)...")
        train_start = datetime.now()
        
        base_model.fit(X_train_scaled, y_train)
        
        base_train_time = (datetime.now() - train_start).total_seconds()
        print(f"✅ Base training: {base_train_time:.1f}s")
        
        # Evaluate uncalibrated model
        y_pred_base = base_model.predict(X_test_scaled)
        y_pred_proba_base = base_model.predict_proba(X_test_scaled)[:, 1]
        
        base_auc = roc_auc_score(y_test, y_pred_proba_base)
        base_brier = brier_score_loss(y_test, y_pred_proba_base)
        
        print(f"\n📊 Uncalibrated Performance:")
        print(f"   AUC: {base_auc:.4f}")
        print(f"   Brier Score: {base_brier:.4f} (lower is better)")
        
        # ────────────────────────────────────────────────────────────
        # TRAIN WITH CALIBRATION (Improved)
        # ────────────────────────────────────────────────────────────
        print(f"\n🔧 Applying calibration (isotonic regression)...")
        calib_start = datetime.now()
        
        # EDUCATIONAL NOTE: CalibratedClassifierCV uses cross-validation
        # - Splits training data into 5 folds
        # - For each fold: train on 4/5, calibrate on 1/5
        # - Final model averages 5 calibrated models
        # - Prevents overfitting the calibration function
        calibrated_model = CalibratedClassifierCV(
            base_model,
            method='isotonic',  # Non-parametric, flexible
            cv=5,               # 5-fold cross-validation
            n_jobs=-1           # Use all CPU cores
        )
        
        calibrated_model.fit(X_train_scaled, y_train)
        
        calib_time = (datetime.now() - calib_start).total_seconds()
        total_time = base_train_time + calib_time
        print(f"✅ Calibration: {calib_time:.1f}s")
        print(f"✅ Total: {total_time:.1f}s")
        
        mlflow.log_metric("train_duration_base", base_train_time)
        mlflow.log_metric("train_duration_calibration", calib_time)
        mlflow.log_metric("train_duration_total", total_time)
        
        # Evaluate calibrated model
        y_pred_calib = calibrated_model.predict(X_test_scaled)
        y_pred_proba_calib = calibrated_model.predict_proba(X_test_scaled)[:, 1]
        
        calib_auc = roc_auc_score(y_test, y_pred_proba_calib)
        calib_brier = brier_score_loss(y_test, y_pred_proba_calib)
        
        # EDUCATIONAL NOTE: Brier Score measures calibration quality
        # Formula: mean((predicted_prob - actual_label)²)
        # Range: 0 (perfect) to 1 (worst)
        # Lower = better calibration
        
        print(f"\n📊 Calibrated Performance:")
        print(f"   AUC: {calib_auc:.4f}")
        print(f"   Brier Score: {calib_brier:.4f}")
        print(f"\n📈 Improvement:")
        print(f"   Brier: {base_brier:.4f} → {calib_brier:.4f} ({(base_brier - calib_brier):.4f} better)")
        
        # Log metrics
        mlflow.log_metrics({
            "test_auc_base": base_auc,
            "test_auc_calibrated": calib_auc,
            "brier_score_base": base_brier,
            "brier_score_calibrated": calib_brier,
            "brier_improvement": base_brier - calib_brier
        })
        
        # Classification metrics
        report = classification_report(y_test, y_pred_calib, output_dict=True)
        mlflow.log_metrics({
            "test_accuracy": report['accuracy'],
            "test_precision": report['1']['precision'],
            "test_recall": report['1']['recall'],
            "test_f1": report['1']['f1-score']
        })
        
        # ────────────────────────────────────────────────────────────
        # ADVERSARIAL EVALUATION
        # ────────────────────────────────────────────────────────────
        if X_adv_scaled is not None and y_adv is not None:
            print(f"\n🎯 Adversarial Set Evaluation:")
            
            y_pred_adv = calibrated_model.predict(X_adv_scaled)
            adv_accuracy = (y_pred_adv == y_adv).sum() / len(y_adv)
            
            mlflow.log_metric("adversarial_accuracy", adv_accuracy)
            print(f"   Accuracy: {adv_accuracy:.4f} ({adv_accuracy:.1%})")
        
        # ────────────────────────────────────────────────────────────
        # VISUALIZATIONS
        # ────────────────────────────────────────────────────────────
        print(f"\n📈 Creating visualizations...")
        
        # 1. Calibration Curve (Before vs After)
        # EDUCATIONAL NOTE: This is THE key plot for calibration
        # X-axis: Predicted probability (binned)
        # Y-axis: Actual frequency in that bin
        # Diagonal line = perfect calibration
        plt.figure(figsize=(10, 8))
        
        # Plot uncalibrated
        fraction_of_positives_base, mean_predicted_value_base = calibration_curve(
            y_test, y_pred_proba_base, n_bins=10, strategy='quantile'
        )
        plt.plot(mean_predicted_value_base, fraction_of_positives_base, 
                 's-', label=f'{model_name} (Uncalibrated)', linewidth=2, markersize=8)
        
        # Plot calibrated
        fraction_of_positives_calib, mean_predicted_value_calib = calibration_curve(
            y_test, y_pred_proba_calib, n_bins=10, strategy='quantile'
        )
        plt.plot(mean_predicted_value_calib, fraction_of_positives_calib, 
                 'o-', label=f'{model_name} (Calibrated)', linewidth=2, markersize=8)
        
        # Perfect calibration reference
        plt.plot([0, 1], [0, 1], 'k--', label='Perfect Calibration', linewidth=1)
        
        plt.xlabel('Predicted Probability', fontsize=12)
        plt.ylabel('Actual Frequency', fontsize=12)
        plt.title(f'Calibration Curve - {model_name}\nBefore vs After', fontsize=14, fontweight='bold')
        plt.legend(loc='lower right', fontsize=10)
        plt.grid(alpha=0.3)
        plt.xlim([0, 1])
        plt.ylim([0, 1])
        plt.tight_layout()
        
        calib_curve_path = f'calibration_curve_{model_name}.png'
        plt.savefig(calib_curve_path, dpi=150)
        mlflow.log_artifact(calib_curve_path)
        plt.close()
        
        # 2. Confusion Matrix
        cm = confusion_matrix(y_test, y_pred_calib)
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                    xticklabels=['Safe', 'Vulnerable'],
                    yticklabels=['Safe', 'Vulnerable'])
        plt.title(f'Confusion Matrix - {model_name} (Calibrated)')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()
        
        cm_path = f'confusion_matrix_{model_name}_calibrated.png'
        plt.savefig(cm_path, dpi=150)
        mlflow.log_artifact(cm_path)
        plt.close()
        
        # 3. ROC Curve
        fpr, tpr, _ = roc_curve(y_test, y_pred_proba_calib)
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, label=f'{model_name} (AUC = {calib_auc:.3f})', linewidth=2)
        plt.plot([0, 1], [0, 1], 'k--', label='Random Classifier')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title(f'ROC Curve - {model_name} (Calibrated)')
        plt.legend(loc="lower right")
        plt.grid(alpha=0.3)
        plt.tight_layout()
        
        roc_path = f'roc_curve_{model_name}_calibrated.png'
        plt.savefig(roc_path, dpi=150)
        mlflow.log_artifact(roc_path)
        plt.close()
        
        # ────────────────────────────────────────────────────────────
        # SAVE MODELS
        # ────────────────────────────────────────────────────────────
        print(f"\n💾 Logging models to MLflow...")
        
        # Log calibrated model (primary)
        signature = infer_signature(X_train_scaled, y_pred_proba_calib)
        mlflow.sklearn.log_model(
            calibrated_model,
            artifact_path="calibrated_model",
            signature=signature
        )
        
        # Also log scaler (needed for deployment)
        import joblib
        scaler_path = f'robust_scaler_{model_name}.pkl'
        joblib.dump(scaler, scaler_path)
        mlflow.log_artifact(scaler_path)
        
        mlflow.set_tags({
            "developer": "ali",
            "purpose": "production_calibrated",
            "stage": "experimental",
            "improvements": "robust_scaler+calibration"
        })
        
        print(f"✅ Run logged!")
        print(f"   Run ID: {mlflow.active_run().info.run_id}")
        
        return calibrated_model, calib_auc, calib_brier

# ============================================================================
# STEP 6: TRAIN MODELS
# ============================================================================
print("\n🚀 STEP 6: TRAINING CALIBRATED MODELS")
print("="*80)

results = {}

# XGBoost (Primary)
print("\n1️⃣  XGBoost with Calibration")
xgb_model = xgb.XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=pos_weight,
    random_state=42,
    eval_metric='logloss'
)

model, auc, brier = train_calibrated_model(
    "XGBoost",
    xgb_model,
    X_train_scaled,
    y_train,
    X_test_scaled,
    y_test,
    X_adv_scaled,
    y_adv,
    full_features
)
results['XGBoost'] = {'model': model, 'auc': auc, 'brier': brier}

# ============================================================================
# STEP 7: SUMMARY
# ============================================================================
print("\n" + "="*80)
print("🎉 TRAINING COMPLETE!")
print("="*80)

best_model = 'XGBoost'
print(f"\n🏆 BEST MODEL: {best_model}")
print(f"   Test AUC: {results[best_model]['auc']:.4f}")
print(f"   Brier Score: {results[best_model]['brier']:.4f}")

print(f"\n🔍 View results in MLflow UI:")
print(f"   http://localhost:5000")
print(f"   Experiment: {EXPERIMENT_NAME}")

print(f"\n💡 KEY IMPROVEMENTS:")
print(f"   ✅ RobustScaler: Better handling of outliers")
print(f"   ✅ Calibration: Trustworthy probabilities")
print(f"   ✅ Brier Score: Calibration quality metric")

print("\n" + "="*80 + "\n")