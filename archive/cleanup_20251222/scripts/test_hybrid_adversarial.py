"""
Test Adversarial Performance: Pure ML vs Hybrid
================================================

WHAT THIS DOES:
1. Load NEW calibrated model (RobustScaler + calibration)
2. Test on adversarial set with PURE ML (current 48%)
3. Test on adversarial set with HYBRID (expected 70-80%)
4. Compare predictions side-by-side
5. Show which component (ML vs semantic) catches each vulnerability

EXPECTED RESULTS:
- Pure ML: ~48% (current)
- Hybrid: ~70-80% (semantic rules save you)

Author: Ali
Date: December 21, 2024
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import classification_report, confusion_matrix

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from chainguardian.ml.models.hybrid_predictor import HybridPredictor

print("\n" + "="*80)
print("🔍 ADVERSARIAL DIAGNOSTIC: PURE ML vs HYBRID")
print("="*80)

# ============================================================================
# STEP 1: LOAD DATA
# ============================================================================
print("\n📊 STEP 1: LOADING ADVERSARIAL DATA")
print("-" * 80)

df = pd.read_csv('data/complete_dataset_with_semantic.csv')

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

# Get adversarial set
adversarial_df = df[df['data_source'] == 'adversarial_test'].copy()

print(f"✅ Loaded {len(adversarial_df)} adversarial contracts")
print(f"   Vulnerable: {adversarial_df['is_vulnerable'].sum()}")
print(f"   Safe: {(~adversarial_df['is_vulnerable'].astype(bool)).sum()}")

# ============================================================================
# STEP 2: DEFINE FEATURES
# ============================================================================
print("\n🔧 STEP 2: FEATURE SELECTION")
print("-" * 80)

# [Copy feature groups from train_with_robust_calibrated.py]
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

full_features = (vulnerability_flags + severity_counts + ast_features + 
                 detector_stats + risk_scores + graph_features + semantic_features)
full_features = [f for f in full_features if f in adversarial_df.columns]

print(f"✅ Using {len(full_features)} features")

# ============================================================================
# STEP 3: TEST PURE ML MODEL
# ============================================================================
print("\n🤖 STEP 3: TESTING PURE ML (Current Approach)")
print("="*80)

# Load model and scaler
models_dir = Path('models')
model_path = models_dir / 'production_model.pkl'
scaler_path = models_dir / 'production_scaler.pkl'

if not model_path.exists() or not scaler_path.exists():
    print("❌ Model files not found!")
    print(f"   Expected: {model_path}")
    print(f"   Expected: {scaler_path}")
    print("\n💡 Run this first:")
    print("   poetry run python scripts/3_training/train_with_robust_calibrated.py")
    sys.exit(1)

ml_model = joblib.load(model_path)
scaler = joblib.load(scaler_path)

print(f"✅ Loaded model from {model_path}")
print(f"✅ Loaded scaler from {scaler_path}")

# Prepare features
X_adv = adversarial_df[full_features]
y_adv = adversarial_df['is_vulnerable']

X_adv_scaled = scaler.transform(X_adv)

# Predict with PURE ML
y_pred_ml = ml_model.predict(X_adv_scaled)
y_pred_proba_ml = ml_model.predict_proba(X_adv_scaled)[:, 1]

ml_accuracy = (y_pred_ml == y_adv).sum() / len(y_adv)

print(f"\n📊 PURE ML PERFORMANCE:")
print(f"   Accuracy: {ml_accuracy:.1%}")
print(f"   Correct: {(y_pred_ml == y_adv).sum()}/{len(y_adv)}")

print("\n" + classification_report(y_adv, y_pred_ml, target_names=['Safe', 'Vulnerable'], zero_division=0))

cm_ml = confusion_matrix(y_adv, y_pred_ml)
print(f"   Confusion Matrix:")
print(f"      TN: {cm_ml[0,0]:3d}  FP: {cm_ml[0,1]:3d}")
print(f"      FN: {cm_ml[1,0]:3d}  TP: {cm_ml[1,1]:3d}")

# ============================================================================
# STEP 4: TEST HYBRID PREDICTOR
# ============================================================================
print("\n🔀 STEP 4: TESTING HYBRID PREDICTOR")
print("="*80)

# Initialize HybridPredictor
try:
    hybrid = HybridPredictor(
        model_path=str(model_path),
        scaler_path=str(scaler_path),
        enable_shap=False  # Faster without SHAP
    )
    print("✅ HybridPredictor initialized")
except Exception as e:
    print(f"❌ Failed to initialize HybridPredictor: {e}")
    sys.exit(1)

# Predict with HYBRID (using default weights: 30% ML, 70% semantic)
results = []
for idx, row in adversarial_df.iterrows():
    # Convert row to dict
    features_dict = row[full_features].to_dict()
    
    # Get hybrid prediction
    pred = hybrid.predict(
        features_dict,
        return_details=True,
        explain=False          # Skip SHAP for speed
    )
    
    results.append({
        'contract_name': row['contract_name'],
        'true_label': row['is_vulnerable'],
        'hybrid_pred': pred['prediction'],
        'hybrid_conf': pred['confidence'],
        'ml_score': pred['ml_score'],
        'semantic_score': pred['semantic_score'],
        'method': pred['method'],
        'semantic_reasons': pred.get('semantic_reasons', [])
    })

results_df = pd.DataFrame(results)

# Calculate hybrid accuracy
hybrid_accuracy = (results_df['hybrid_pred'] == results_df['true_label']).sum() / len(results_df)

print(f"\n📊 HYBRID PERFORMANCE:")
print(f"   Accuracy: {hybrid_accuracy:.1%}")
print(f"   Correct: {(results_df['hybrid_pred'] == results_df['true_label']).sum()}/{len(results_df)}")

y_pred_hybrid = results_df['hybrid_pred'].values
print("\n" + classification_report(y_adv, y_pred_hybrid, target_names=['Safe', 'Vulnerable'], zero_division=0))

cm_hybrid = confusion_matrix(y_adv, y_pred_hybrid)
print(f"   Confusion Matrix:")
print(f"      TN: {cm_hybrid[0,0]:3d}  FP: {cm_hybrid[0,1]:3d}")
print(f"      FN: {cm_hybrid[1,0]:3d}  TP: {cm_hybrid[1,1]:3d}")

# ============================================================================
# STEP 5: COMPARISON ANALYSIS
# ============================================================================
print("\n📈 STEP 5: COMPARISON ANALYSIS")
print("="*80)

print(f"\n🎯 ACCURACY COMPARISON:")
print(f"   Pure ML:  {ml_accuracy:.1%}")
print(f"   Hybrid:   {hybrid_accuracy:.1%}")
print(f"   Improvement: {(hybrid_accuracy - ml_accuracy)*100:+.1f} percentage points")

if hybrid_accuracy > ml_accuracy:
    print(f"\n✅ HYPOTHESIS CONFIRMED: Semantic rules improve robustness!")
    print(f"   Semantic component (70% weight) catches patterns ML misses")
else:
    print(f"\n⚠️  UNEXPECTED: Hybrid didn't improve performance")
    print(f"   Need to investigate semantic analyzer")

# Show per-contract comparison
print(f"\n📋 PER-CONTRACT COMPARISON:")
print(f"{'Contract':<40} {'True':<6} {'ML':<6} {'Hybrid':<6} {'Semantic Reasons'}")
print("-" * 120)

comparison = adversarial_df[['contract_name', 'is_vulnerable']].copy()
comparison['ml_pred'] = y_pred_ml
comparison['hybrid_pred'] = results_df['hybrid_pred'].values
comparison['ml_correct'] = comparison['ml_pred'] == comparison['is_vulnerable']
comparison['hybrid_correct'] = comparison['hybrid_pred'] == comparison['is_vulnerable']

for idx, row in comparison.iterrows():
    ml_icon = "✅" if row['ml_correct'] else "❌"
    hybrid_icon = "✅" if row['hybrid_correct'] else "❌"
    
    # Get semantic reasons
    reasons = results_df[results_df['contract_name'] == row['contract_name']]['semantic_reasons'].iloc[0]
    reasons_str = "; ".join(reasons[:2]) if reasons else "None"  # Show first 2 reasons
    
    print(f"{row['contract_name']:<40} {row['is_vulnerable']:<6} "
          f"{ml_icon} {row['ml_pred']:<3} {hybrid_icon} {row['hybrid_pred']:<3} "
          f"{reasons_str[:60]}")

# Show where hybrid saves ML
ml_wrong = comparison[~comparison['ml_correct']]
hybrid_saved = ml_wrong[ml_wrong['hybrid_correct']]

if len(hybrid_saved) > 0:
    print(f"\n🎉 HYBRID SAVED {len(hybrid_saved)} CASES WHERE ML FAILED:")
    for _, row in hybrid_saved.iterrows():
        print(f"   • {row['contract_name']}")
        reasons = results_df[results_df['contract_name'] == row['contract_name']]['semantic_reasons'].iloc[0]
        for reason in reasons:
            print(f"     - {reason}")

print("\n" + "="*80)
print("🎉 DIAGNOSTIC COMPLETE!")
print("="*80 + "\n")
