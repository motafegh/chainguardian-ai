#!/usr/bin/env python3
"""
Test Pure ML vs Hybrid on Adversarial Set
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pandas as pd
import numpy as np
import joblib

# Load model directly
ml_model = joblib.load('models/production_model.pkl')
scaler = joblib.load('models/production_scaler.pkl')

# Feature list
features = [
    'has_reentrancy', 'has_access_control_issues', 'has_timestamp_dependency',
    'has_unchecked_call', 'has_reentrancy_unlimited', 'has_reentrancy_benign',
    'has_reentrancy_events', 'has_unchecked_transfer', 'has_controlled_delegatecall',
    'has_delegatecall_loop', 'has_uninitialized_state', 'has_uninitialized_storage',
    'has_uninitialized_local', 'has_tx_origin', 'has_inline_assembly',
    'has_locked_ether', 'has_msg_value_loop', 'has_shadowing_state',
    'has_shadowing_builtin', 'has_shadowing_abstract', 'has_unused_state_vars',
    'has_unused_return_values', 'has_incorrect_solc_version', 'has_floating_pragma',
    'has_outdated_compiler',
    'high_severity_count', 'medium_severity_count', 'low_severity_count',
    'num_functions', 'num_external_calls', 'num_state_vars', 'num_modifiers',
    'max_cyclomatic_complexity', 'num_low_level_calls', 'lines_of_code',
    'num_contracts_in_file', 'num_dependencies', 'avg_function_complexity',
    'num_functions_high_complexity', 'num_comments', 'comment_to_code_ratio',
    'num_payable_functions', 'num_library_calls', 'inheritance_depth',
    'num_unused_functions',
    'high_confidence_detectors', 'medium_confidence_detectors',
    'low_confidence_detectors', 'security_detectors_triggered',
    'optimization_detectors_triggered', 'total_detector_hits',
    'unique_vulnerability_types', 'detectors_per_function', 'detectors_per_loc',
    'risk_score_simple', 'risk_score_weighted', 'is_high_risk',
    'cfg_num_nodes', 'cfg_num_edges', 'cfg_num_cycles', 'cfg_max_depth',
    'cfg_avg_branching', 'cfg_has_complex_loops', 'cfg_num_exit_points',
    'cfg_cyclomatic_total', 'cg_num_nodes', 'cg_num_edges', 'cg_max_call_depth',
    'cg_num_external_calls', 'cg_external_call_ratio', 'cg_has_cyclic_calls',
    'cg_num_public_entry_points', 'cg_num_internal_functions',
    'cg_avg_calls_per_function', 'cg_num_leaf_functions', 'dfg_num_state_vars',
    'dfg_num_tainted_flows', 'dfg_has_cross_function_flow', 'dfg_num_sensitive_sinks',
    'dfg_num_external_sources', 'dfg_taint_to_sink_ratio', 'dfg_num_unvalidated_inputs',
    'cei_violations', 'cei_safe_functions', 'cei_pattern_score',
    'has_reentrancy_guard', 'functions_with_reentrancy_guard',
    'state_before_call_count', 'state_after_call_count',
    'unchecked_calls_in_critical_context'
]

# Load data
df = pd.read_csv('data/complete_dataset_with_semantic.csv')
df_adv = df[df['data_source'] == 'adversarial_test'].copy()
df_adv['label'] = df_adv['contract_name'].str.contains(
    'reentrancy|vulnerable|danger|exploit|honeypot|delegatecall|front_running|intentional',
    case=False, na=False
).astype(int)

print("="*80)
print("🔍 PURE ML vs HYBRID - Adversarial Set (25 contracts)")
print("="*80)
print(f"Vulnerable: {df_adv['label'].sum()}, Safe: {len(df_adv)-df_adv['label'].sum()}")

# Helper function for semantic scoring
def calculate_semantic_score(row):
    """Calculate semantic risk like HybridPredictor does"""
    risk = 0.0
    
    # CEI violations (weight 0.40)
    cei_viol = row.get('cei_violations', 0)
    if cei_viol > 0:
        risk += 0.40 * min(cei_viol / 5, 1.0)
    
    # Low CEI score (weight 0.20)
    cei_score = row.get('cei_pattern_score', 1.0)
    if cei_score < 0.8:
        risk += 0.20 * (1.0 - cei_score)
    
    # State after call (weight 0.30)
    state_after = row.get('state_after_call_count', 0)
    if state_after > 0:
        risk += 0.30 * min(state_after / 3, 1.0)
    
    # Unchecked critical (weight 0.20)
    unchecked = row.get('unchecked_calls_in_critical_context', 0)
    if unchecked > 0:
        risk += 0.20 * min(unchecked / 2, 1.0)
    
    # Reentrancy guard bonus (weight -0.50)
    has_guard = row.get('has_reentrancy_guard', 0)
    num_ext = row.get('num_external_calls', 0)
    if has_guard and num_ext > 0:
        risk *= (1 - 0.50)
    
    return min(risk, 1.0)

# Test PURE ML
print(f"\n{'='*80}")
print("🤖 PURE ML (threshold=0.5)")
print("="*80)

X = df_adv[features].fillna(0)
X_scaled = scaler.transform(X)
ml_proba = ml_model.predict_proba(X_scaled)[:, 1]
ml_pred = (ml_proba >= 0.5).astype(int)

ml_correct = (ml_pred == df_adv['label']).sum()
ml_tp = ((df_adv['label'] == 1) & (ml_pred == 1)).sum()
ml_fp = ((df_adv['label'] == 0) & (ml_pred == 1)).sum()
ml_fn = ((df_adv['label'] == 1) & (ml_pred == 0)).sum()
ml_tn = ((df_adv['label'] == 0) & (ml_pred == 0)).sum()

print(f"Accuracy: {ml_correct/len(df_adv):.1%}")
print(f"Precision: {ml_tp/(ml_tp+ml_fp):.1%}" if ml_tp+ml_fp > 0 else "Precision: N/A")
print(f"Recall: {ml_tp/(ml_tp+ml_fn):.1%}" if ml_tp+ml_fn > 0 else "Recall: N/A")
print(f"TP: {ml_tp}, FP: {ml_fp}, FN: {ml_fn}, TN: {ml_tn}")

# Test HYBRID
print(f"\n{'='*80}")
print("🔀 HYBRID (ml=0.6, semantic=0.4, threshold=0.55)")
print("="*80)

semantic_scores = df_adv.apply(calculate_semantic_score, axis=1).values
hybrid_score = 0.6 * ml_proba + 0.4 * semantic_scores
hybrid_pred = (hybrid_score >= 0.55).astype(int)

hybrid_correct = (hybrid_pred == df_adv['label']).sum()
hybrid_tp = ((df_adv['label'] == 1) & (hybrid_pred == 1)).sum()
hybrid_fp = ((df_adv['label'] == 0) & (hybrid_pred == 1)).sum()
hybrid_fn = ((df_adv['label'] == 1) & (hybrid_pred == 0)).sum()
hybrid_tn = ((df_adv['label'] == 0) & (hybrid_pred == 0)).sum()

print(f"Accuracy: {hybrid_correct/len(df_adv):.1%}")
print(f"Precision: {hybrid_tp/(hybrid_tp+hybrid_fp):.1%}" if hybrid_tp+hybrid_fp > 0 else "Precision: N/A")
print(f"Recall: {hybrid_tp/(hybrid_tp+hybrid_fn):.1%}" if hybrid_tp+hybrid_fn > 0 else "Recall: N/A")
print(f"TP: {hybrid_tp}, FP: {hybrid_fp}, FN: {hybrid_fn}, TN: {hybrid_tn}")

# Semantic contribution check
print(f"\n{'='*80}")
print("📊 SEMANTIC ANALYSIS")
print("="*80)
print(f"Semantic scores: min={semantic_scores.min():.3f}, max={semantic_scores.max():.3f}, mean={semantic_scores.mean():.3f}")
print(f"Non-zero semantic: {(semantic_scores > 0).sum()}/{len(semantic_scores)}")

if semantic_scores.max() == 0:
    print("⚠️  WARNING: All semantic scores are 0 (no CEI violations detected)")
    print("   Hybrid reduces to: 0.6 * ML_score")

print(f"\n{'='*80}")
print("📊 COMPARISON")
print("="*80)
print(f"             Pure ML    Hybrid     Change")
print(f"Accuracy:    {ml_correct/len(df_adv):5.1%}      {hybrid_correct/len(df_adv):5.1%}      {(hybrid_correct-ml_correct)/len(df_adv)*100:+.1f}pp")
print(f"TP/FP:       {ml_tp}/{ml_fp}         {hybrid_tp}/{hybrid_fp}          {hybrid_tp-ml_tp:+d}/{hybrid_fp-ml_fp:+d}")
print("="*80 + "\n")
