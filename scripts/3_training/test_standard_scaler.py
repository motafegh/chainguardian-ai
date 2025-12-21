"""Quick test: StandardScaler vs RobustScaler"""
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import joblib

# Load data
df = pd.read_csv('data/complete_dataset_with_semantic.csv')
df['is_vulnerable'] = df['data_source'].isin(['smartbugs_curated', 'production_vulnerable', 'trail_of_bits']).astype(int)

# Features (same as before)
full_features = [f for f in ['has_reentrancy', 'has_access_control_issues', 'has_timestamp_dependency', 'has_unchecked_call', 'has_reentrancy_unlimited', 'has_reentrancy_benign', 'has_reentrancy_events', 'has_unchecked_transfer', 'has_controlled_delegatecall', 'has_delegatecall_loop', 'has_uninitialized_state', 'has_uninitialized_storage', 'has_uninitialized_local', 'has_tx_origin', 'has_inline_assembly', 'has_locked_ether', 'has_msg_value_loop', 'has_shadowing_state', 'has_shadowing_builtin', 'has_shadowing_abstract', 'has_unused_state_vars', 'has_unused_return_values', 'has_incorrect_solc_version', 'has_floating_pragma', 'has_outdated_compiler', 'high_severity_count', 'medium_severity_count', 'low_severity_count', 'num_functions', 'num_external_calls', 'num_state_vars', 'num_modifiers', 'max_cyclomatic_complexity', 'num_low_level_calls', 'lines_of_code', 'num_contracts_in_file', 'num_dependencies', 'avg_function_complexity', 'num_functions_high_complexity', 'num_comments', 'comment_to_code_ratio', 'num_payable_functions', 'num_library_calls', 'inheritance_depth', 'num_unused_functions', 'high_confidence_detectors', 'medium_confidence_detectors', 'low_confidence_detectors', 'security_detectors_triggered', 'optimization_detectors_triggered', 'total_detector_hits', 'unique_vulnerability_types', 'detectors_per_function', 'detectors_per_loc', 'risk_score_simple', 'risk_score_weighted', 'is_high_risk', 'cfg_num_nodes', 'cfg_num_edges', 'cfg_num_cycles', 'cfg_max_depth', 'cfg_avg_branching', 'cfg_has_complex_loops', 'cfg_num_exit_points', 'cfg_cyclomatic_total', 'cg_num_nodes', 'cg_num_edges', 'cg_max_call_depth', 'cg_num_external_calls', 'cg_external_call_ratio', 'cg_has_cyclic_calls', 'cg_num_public_entry_points', 'cg_num_internal_functions', 'cg_avg_calls_per_function', 'cg_num_leaf_functions', 'dfg_num_state_vars', 'dfg_num_tainted_flows', 'dfg_has_cross_function_flow', 'dfg_num_sensitive_sinks', 'dfg_num_external_sources', 'dfg_taint_to_sink_ratio', 'dfg_num_unvalidated_inputs', 'cei_violations', 'cei_safe_functions', 'cei_pattern_score', 'has_reentrancy_guard', 'functions_with_reentrancy_guard', 'state_before_call_count', 'state_after_call_count', 'unchecked_calls_in_critical_context'] if f in df.columns]

# Split
main_df = df[df['data_source'] != 'adversarial_test']
X_train, X_test, y_train, y_test = train_test_split(
    main_df[full_features], main_df['is_vulnerable'], 
    test_size=0.2, random_state=42, stratify=main_df['is_vulnerable']
)

# StandardScaler (original)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)

# Train
pos_weight = len(y_train) / (2 * y_train.sum())
model = xgb.XGBClassifier(
    n_estimators=300, max_depth=6, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8, 
    scale_pos_weight=pos_weight, random_state=42
)
model.fit(X_train_scaled, y_train)

# Test on adversarial
adversarial_df = df[df['data_source'] == 'adversarial_test']
adversarial_mask = df['data_source'] == 'adversarial_test'
df.loc[adversarial_mask, 'is_vulnerable'] = df.loc[adversarial_mask, 'contract_name'].str.contains('reentrancy|vulnerable|danger|exploit|honeypot|obvious', case=False, na=False).astype(int)
adversarial_df = df[df['data_source'] == 'adversarial_test']

X_adv = adversarial_df[full_features]
y_adv = adversarial_df['is_vulnerable']
X_adv_scaled = scaler.transform(X_adv)

y_pred = model.predict(X_adv_scaled)
acc = (y_pred == y_adv).sum() / len(y_adv)

print(f'\nStandardScaler + Uncalibrated XGBoost:')
print(f'Adversarial Accuracy: {acc:.1%}')

# Save temp
joblib.dump(model, 'models/test_standard.pkl')
joblib.dump(scaler, 'models/test_standard_scaler.pkl')
