"""
Production-Ready ML Training with Semantic Features
====================================================
Train models on 963 contracts with 93 features (including 8 semantic)
Compare baseline (85 features) vs semantic-enhanced (93 features)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, precision_recall_curve
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import joblib
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

print("\n" + "="*80)
print("🎯 PRODUCTION ML TRAINING WITH SEMANTIC FEATURES")
print("="*80)

# ============================================================================
# STEP 1: LOAD DATA
# ============================================================================
print("\n📊 STEP 1: LOADING DATASET")
print("-" * 80)

df = pd.read_csv('data/complete_dataset_with_semantic.csv')

print(f"✅ Loaded {len(df)} contracts with {len(df.columns)} columns")

# Create labels from multiple sources
# Priority: data_source (smartbugs_curated, production_vulnerable = vulnerable)
df['is_vulnerable'] = df['data_source'].isin([
    'smartbugs_curated',
    'production_vulnerable',
    'trail_of_bits'
]).astype(int)

# For adversarial, use filename patterns
adversarial_mask = df['data_source'] == 'adversarial_test'
df.loc[adversarial_mask, 'is_vulnerable'] = df.loc[adversarial_mask, 'contract_name'].str.contains(
    'reentrancy|vulnerable|danger|exploit|honeypot|obvious',
    case=False,
    na=False
).astype(int)

print(f"\n📊 Label Distribution:")
print(f"   Vulnerable: {df['is_vulnerable'].sum()} ({df['is_vulnerable'].sum()/len(df)*100:.1f}%)")
print(f"   Safe: {(~df['is_vulnerable'].astype(bool)).sum()} ({(~df['is_vulnerable'].astype(bool)).sum()/len(df)*100:.1f}%)")

print(f"\n📊 By Source:")
print(df.groupby('data_source')['is_vulnerable'].agg(['sum', 'count']).to_string())

# ============================================================================
# STEP 2: FEATURE ENGINEERING
# ============================================================================
print("\n🔧 STEP 2: FEATURE SELECTION")
print("-" * 80)

# Define feature groups
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

severity_counts = [
    'high_severity_count', 'medium_severity_count', 'low_severity_count'
]

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

risk_scores = [
    'risk_score_simple', 'risk_score_weighted', 'is_high_risk'
]

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

# 🌟 SEMANTIC FEATURES (NEW!)
semantic_features = [
    'cei_violations',
    'cei_safe_functions',
    'cei_pattern_score',
    'has_reentrancy_guard',
    'functions_with_reentrancy_guard',
    'state_before_call_count',
    'state_after_call_count',
    'unchecked_calls_in_critical_context'
]

# Baseline: 85 features (without semantic)
baseline_features = (
    vulnerability_flags + severity_counts + ast_features + 
    detector_stats + risk_scores + graph_features
)

# Full: 93 features (with semantic)
full_features = baseline_features + semantic_features

# Filter to available features
baseline_features = [f for f in baseline_features if f in df.columns]
full_features = [f for f in full_features if f in df.columns]
semantic_available = [f for f in semantic_features if f in df.columns]

print(f"✅ Baseline features: {len(baseline_features)}")
print(f"✅ Semantic features: {len(semantic_available)}")
print(f"✅ Total features: {len(full_features)}")

print(f"\n🌟 Semantic features included:")
for feat in semantic_available:
    print(f"   • {feat}")

# ============================================================================
# STEP 3: TRAIN/TEST SPLIT
# ============================================================================
print("\n🔀 STEP 3: TRAIN/TEST SPLIT")
print("-" * 80)

# Separate adversarial test set
adversarial_df = df[df['data_source'] == 'adversarial_test'].copy()
main_df = df[df['data_source'] != 'adversarial_test'].copy()

print(f"Main dataset: {len(main_df)} contracts")
print(f"Adversarial test: {len(adversarial_df)} contracts")

# Split main dataset 80/20
X_main = main_df[full_features]
y_main = main_df['is_vulnerable']

X_train, X_test, y_train, y_test = train_test_split(
    X_main, y_main, 
    test_size=0.2, 
    random_state=42, 
    stratify=y_main
)

print(f"\n📊 Split:")
print(f"   Training: {len(X_train)} ({y_train.sum()} vulnerable)")
print(f"   Test: {len(X_test)} ({y_test.sum()} vulnerable)")
print(f"   Adversarial: {len(adversarial_df)} ({adversarial_df['is_vulnerable'].sum()} vulnerable)")

# ============================================================================
# STEP 4: TRAIN MODELS
# ============================================================================
print("\n🚀 STEP 4: TRAINING MODELS")
print("-" * 80)

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Calculate class weights for imbalanced data
pos_weight = len(y_train) / (2 * y_train.sum())
neg_weight = len(y_train) / (2 * (len(y_train) - y_train.sum()))

print(f"📊 Class weights: Vulnerable={pos_weight:.2f}, Safe={neg_weight:.2f}")

models = {}

# 1. XGBoost (Best for structured data)
print("\n1️⃣  Training XGBoost...")
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
xgb_model.fit(X_train_scaled, y_train)
models['XGBoost'] = xgb_model

# 2. Random Forest
print("2️⃣  Training Random Forest...")
rf_model = RandomForestClassifier(
    n_estimators=300,
    max_depth=15,
    min_samples_split=5,
    min_samples_leaf=2,
    class_weight={0: neg_weight, 1: pos_weight},
    random_state=42,
    n_jobs=-1
)
rf_model.fit(X_train_scaled, y_train)
models['RandomForest'] = rf_model

# 3. Gradient Boosting
print("3️⃣  Training Gradient Boosting...")
gb_model = GradientBoostingClassifier(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.1,
    subsample=0.8,
    random_state=42
)
gb_model.fit(X_train_scaled, y_train)
models['GradientBoosting'] = gb_model

print("✅ All models trained!")

# ============================================================================
# STEP 5: EVALUATE ON TEST SET
# ============================================================================
print("\n📊 STEP 5: TEST SET EVALUATION")
print("="*80)

best_model = None
best_auc = 0

for name, model in models.items():
    y_pred = model.predict(X_test_scaled)
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    auc = roc_auc_score(y_test, y_pred_proba)
    
    print(f"\n{name}:")
    print(f"   AUC: {auc:.4f}")
    print("\n" + classification_report(y_test, y_pred, target_names=['Safe', 'Vulnerable']))
    
    cm = confusion_matrix(y_test, y_pred)
    print(f"   Confusion Matrix:")
    print(f"      TN: {cm[0,0]:3d}  FP: {cm[0,1]:3d}")
    print(f"      FN: {cm[1,0]:3d}  TP: {cm[1,1]:3d}")
    
    if auc > best_auc:
        best_auc = auc
        best_model = model
        best_model_name = name

print(f"\n🏆 BEST MODEL: {best_model_name} (AUC: {best_auc:.4f})")

# ============================================================================
# STEP 6: ADVERSARIAL TEST EVALUATION
# ============================================================================
print("\n🎯 STEP 6: ADVERSARIAL TEST EVALUATION")
print("="*80)

if len(adversarial_df) > 0:
    X_adv = adversarial_df[full_features]
    y_adv = adversarial_df['is_vulnerable']
    
    X_adv_scaled = scaler.transform(X_adv)
    
    for name, model in models.items():
        y_pred = model.predict(X_adv_scaled)
        y_pred_proba = model.predict_proba(X_adv_scaled)[:, 1]
        
        accuracy = (y_pred == y_adv).sum() / len(y_adv)
        
        print(f"\n{name}:")
        print(f"   Accuracy: {accuracy:.1%}")
        print("\n" + classification_report(y_adv, y_pred, target_names=['Safe', 'Vulnerable'], zero_division=0))
        
        # Show predictions for each contract
        print(f"\n   Contract Predictions:")
        results = adversarial_df[['contract_name', 'is_vulnerable']].copy()
        results['predicted'] = y_pred
        results['confidence'] = y_pred_proba
        results['correct'] = results['is_vulnerable'] == results['predicted']
        
        for _, row in results.iterrows():
            status = "✅" if row['correct'] else "❌"
            print(f"      {status} {row['contract_name']:40s} | True: {row['is_vulnerable']} | Pred: {row['predicted']} | Conf: {row['confidence']:.2%}")

# ============================================================================
# STEP 7: FEATURE IMPORTANCE ANALYSIS
# ============================================================================
print("\n📊 STEP 7: FEATURE IMPORTANCE (TOP 20)")
print("="*80)

# Get feature importance from best model
if hasattr(best_model, 'feature_importances_'):
    importances = best_model.feature_importances_
    feature_importance = pd.DataFrame({
        'feature': full_features,
        'importance': importances
    }).sort_values('importance', ascending=False)
    
    print(f"\nTop 20 features ({best_model_name}):")
    for idx, row in feature_importance.head(20).iterrows():
        is_semantic = row['feature'] in semantic_available
        marker = "🌟" if is_semantic else "  "
        print(f"   {marker} {row['feature']:40s}: {row['importance']:.4f}")
    
    # Check semantic feature rankings
    semantic_ranks = feature_importance[feature_importance['feature'].isin(semantic_available)].copy()
    semantic_ranks['rank'] = range(1, len(semantic_ranks) + 1)
    
    print(f"\n🌟 Semantic Feature Rankings:")
    for _, row in semantic_ranks.iterrows():
        rank_in_all = feature_importance[feature_importance['feature'] == row['feature']].index[0] + 1
        print(f"   {row['feature']:40s}: Rank {rank_in_all:2d}/{len(full_features)} (Importance: {row['importance']:.4f})")

# ============================================================================
# STEP 8: SAVE MODELS
# ============================================================================
print("\n💾 STEP 8: SAVING MODELS")
print("-" * 80)

models_dir = Path('models')
models_dir.mkdir(exist_ok=True)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

# Save best model
joblib.dump(best_model, models_dir / f'semantic_model_{best_model_name.lower()}_{timestamp}.pkl')
joblib.dump(scaler, models_dir / f'semantic_scaler_{timestamp}.pkl')

# Save all models
for name, model in models.items():
    joblib.dump(model, models_dir / f'semantic_{name.lower()}_{timestamp}.pkl')

# Save metadata
metadata = {
    'timestamp': timestamp,
    'total_contracts': len(df),
    'training_contracts': len(X_train),
    'test_contracts': len(X_test),
    'adversarial_contracts': len(adversarial_df),
    'features_count': len(full_features),
    'semantic_features': semantic_available,
    'best_model': best_model_name,
    'best_auc': best_auc,
    'feature_list': full_features
}

import json
with open(models_dir / f'semantic_metadata_{timestamp}.json', 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"✅ Saved {len(models)} models to {models_dir}")
print(f"✅ Best model: {best_model_name}")
print(f"   AUC: {best_auc:.4f}")

print("\n" + "="*80)
print("🎉 TRAINING COMPLETE!")
print("="*80 + "\n")
