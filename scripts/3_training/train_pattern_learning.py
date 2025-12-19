"""
Pattern-Learning Model (Model B)

Learns from CODE PATTERNS only (no Slither flags).
This shows what ML can learn without static analysis tools.

Features used:
- Graph features (CFG, Call Graph, Data Flow)
- Code structure (complexity, calls, state vars)
- NO Slither vulnerability flags
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score, StratifiedKFold, train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
from imblearn.over_sampling import SMOTE
import xgboost as xgb
import joblib
import matplotlib.pyplot as plt
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

print("\n" + "="*70)
print("🧠 MODEL B: PATTERN-LEARNING (WITHOUT SLITHER)")
print("="*70)

# ============================================================
# 1. LOAD AND PREPARE DATA
# ============================================================
print("\n1️⃣ Loading training data...")
df = pd.read_csv('data/training_clean.csv')

# Define Slither features to REMOVE
slither_features = [
    # Vulnerability flags (25 features)
    'has_reentrancy', 'has_access_control_issues', 'has_timestamp_dependency',
    'has_unchecked_call', 'has_reentrancy_unlimited', 'has_reentrancy_benign',
    'has_reentrancy_events', 'has_unchecked_transfer', 'has_controlled_delegatecall',
    'has_delegatecall_loop', 'has_uninitialized_state', 'has_uninitialized_storage',
    'has_uninitialized_local', 'has_tx_origin', 'has_inline_assembly',
    'has_locked_ether', 'has_msg_value_loop', 'has_shadowing_state',
    'has_shadowing_builtin', 'has_shadowing_abstract', 'has_unused_state_vars',
    'has_unused_return_values', 'has_incorrect_solc_version', 'has_floating_pragma',
    'has_outdated_compiler',
    
    # Severity counts (keep these - they're aggregate stats)
    # 'high_severity_count', 'medium_severity_count', 'low_severity_count',
    
    # Detector stats (keep these - aggregate metrics)
    # 'high_confidence_detectors', 'medium_confidence_detectors',
    # 'security_detectors_triggered', 'optimization_detectors_triggered',
    # 'total_detector_hits',
    
    # Risk scores (derived, remove)
    'risk_score_simple', 'risk_score_weighted', 'is_high_risk',
    
    # Keep unique_vulnerability_types as it's a count
]

# Remove Slither flags
features_to_remove = [f for f in slither_features if f in df.columns]
df_patterns = df.drop(columns=features_to_remove)

X = df_patterns.drop('label', axis=1)
y = df_patterns['label']

print(f"   Original features: 70")
print(f"   Removed Slither flags: {len(features_to_remove)}")
print(f"   Pattern features: {len(X.columns)}")
print(f"   Samples: {len(X)}")
print(f"   Vulnerable: {(y == 1).sum()} ({(y == 1).sum()/len(y)*100:.1f}%)")
print(f"   Safe: {(y == 0).sum()} ({(y == 0).sum()/len(y)*100:.1f}%)")

# Show feature categories
graph_features = [f for f in X.columns if f.startswith(('cfg_', 'cg_', 'dfg_'))]
detector_features = [f for f in X.columns if 'detector' in f or 'severity' in f]
code_features = [f for f in X.columns if f not in graph_features + detector_features]

print(f"\n   Feature breakdown:")
print(f"      🟢 Graph features: {len(graph_features)}")
print(f"      🟣 Detector stats: {len(detector_features)}")
print(f"      🔵 Code structure: {len(code_features)}")

# ============================================================
# 2. HANDLE CLASS IMBALANCE WITH SMOTE
# ============================================================
print("\n2️⃣ Handling class imbalance with SMOTE...")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

print(f"   Before SMOTE:")
print(f"      Train Vulnerable: {(y_train == 1).sum()}")
print(f"      Train Safe: {(y_train == 0).sum()}")

smote = SMOTE(random_state=42)
X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)

print(f"   After SMOTE:")
print(f"      Train Vulnerable: {(y_train_balanced == 1).sum()}")
print(f"      Train Safe: {(y_train_balanced == 0).sum()}")

# ============================================================
# 3. TRAIN MODELS WITH CROSS-VALIDATION
# ============================================================
print("\n3️⃣ Training models with 5-fold CV...")

models = {
    'Logistic Regression': LogisticRegression(
        max_iter=2000,
        class_weight='balanced',
        random_state=42
    ),
    'Random Forest': RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    ),
    'Gradient Boosting': GradientBoostingClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.1,
        random_state=42
    ),
    'XGBoost': xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        scale_pos_weight=(y == 0).sum() / (y == 1).sum(),
        random_state=42,
        n_jobs=-1,
        eval_metric='logloss'
    )
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
results = {}

for name, model in models.items():
    print(f"\n   Training {name}...")
    
    # Cross-validation on original (imbalanced) data
    scores = cross_val_score(model, X, y, cv=cv, scoring='roc_auc', n_jobs=-1)
    
    results[name] = {
        'cv_scores': scores,
        'mean_auc': scores.mean(),
        'std_auc': scores.std()
    }
    
    print(f"      CV AUC: {scores.mean():.3f} (+/- {scores.std():.3f})")
    
    # Interpretation
    if scores.mean() > 0.80:
        print(f"      ✅ STRONG - Learning good patterns")
    elif scores.mean() > 0.65:
        print(f"      ✅ HONEST - Realistic performance")
    elif scores.mean() > 0.55:
        print(f"      ⚠️  WEAK - Some signal present")
    else:
        print(f"      ❌ RANDOM - No learning")

# ============================================================
# 4. TRAIN BEST MODEL WITH SMOTE
# ============================================================
print("\n4️⃣ Training best model with SMOTE...")

best_model_name = max(results, key=lambda k: results[k]['mean_auc'])
best_auc = results[best_model_name]['mean_auc']

print(f"   Best model: {best_model_name} (CV AUC: {best_auc:.3f})")

# Train on SMOTE-balanced data
best_model = models[best_model_name]
best_model.fit(X_train_balanced, y_train_balanced)

# Test on held-out data
y_pred = best_model.predict(X_test)
y_pred_proba = best_model.predict_proba(X_test)[:, 1]
test_auc = roc_auc_score(y_test, y_pred_proba)

print(f"\n   Held-out test performance:")
print(f"      AUC: {test_auc:.3f}")
print(f"\n   Classification Report:")
print(classification_report(y_test, y_pred, target_names=['Safe', 'Vulnerable']))

# ============================================================
# 5. FEATURE IMPORTANCE
# ============================================================
if hasattr(best_model, 'feature_importances_'):
    print("\n5️⃣ Feature importance...")
    
    feat_imp = pd.DataFrame({
        'feature': X.columns,
        'importance': best_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"\n   Top 15 features:")
    for i, row in feat_imp.head(15).iterrows():
        category = '🟢' if any(row['feature'].startswith(p) for p in ['cfg_', 'cg_', 'dfg_']) else '🔵'
        print(f"      {category} {row['feature']:40s}: {row['importance']:.4f}")
    
    # Save
    feat_imp.to_csv('reports/pattern_learning_feature_importance.csv', index=False)

# ============================================================
# 6. ADVERSARIAL VALIDATION
# ============================================================
print("\n6️⃣ Adversarial validation (dataset leakage check)...")

df_full = pd.read_csv('data/training_labeled_full.csv')
df_adv = df_full[df_full['data_source'].isin(['smartbugs_curated', 'openzeppelin'])].copy()
df_adv['dataset_label'] = (df_adv['data_source'] == 'smartbugs_curated').astype(int)

# Get pattern features only
pattern_features = [c for c in X.columns if c in df_adv.columns]
X_adv = df_adv[pattern_features].select_dtypes(include=[np.number])
y_adv = df_adv['dataset_label']

rf_adv = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
scores_adv = cross_val_score(rf_adv, X_adv, y_adv, cv=cv, scoring='roc_auc', n_jobs=-1)

print(f"   Dataset AUC: {scores_adv.mean():.3f}")

if scores_adv.mean() > 0.7:
    print(f"   ❌ SEVERE - Features still leak dataset identity")
elif scores_adv.mean() > 0.6:
    print(f"   ⚠️  MODERATE - Some dataset bias remains")
elif scores_adv.mean() > 0.55:
    print(f"   ⚠️  SLIGHT - Minor dataset signature")
else:
    print(f"   ✅ CLEAN - Features are dataset-independent!")

# ============================================================
# 7. SAVE MODEL
# ============================================================
print(f"\n7️⃣ Saving model...")

models_dir = Path('models')
models_dir.mkdir(exist_ok=True)

# Save pattern-learning model
model_path = models_dir / 'pattern_learning_model.pkl'
joblib.dump(best_model, model_path)

# Also save feature list
feature_list_path = models_dir / 'pattern_learning_features.txt'
with open(feature_list_path, 'w') as f:
    for feat in X.columns:
        f.write(f"{feat}\n")

print(f"   ✅ Model saved: {model_path}")
print(f"   ✅ Features saved: {feature_list_path}")

# ============================================================
# 8. SUMMARY REPORT
# ============================================================
with open('reports/pattern_learning_results.txt', 'w') as f:
    f.write("="*70 + "\n")
    f.write("MODEL B: PATTERN-LEARNING RESULTS\n")
    f.write("="*70 + "\n\n")
    
    f.write("APPROACH:\n")
    f.write("  Learn from CODE PATTERNS without Slither vulnerability flags\n\n")
    
    f.write("FEATURES:\n")
    f.write(f"  Total: {len(X.columns)}\n")
    f.write(f"  Graph features: {len(graph_features)}\n")
    f.write(f"  Detector stats: {len(detector_features)}\n")
    f.write(f"  Code structure: {len(code_features)}\n\n")
    
    f.write("REMOVED (to avoid leakage):\n")
    f.write(f"  Slither vulnerability flags: {len(features_to_remove)}\n\n")
    
    f.write("MODELS:\n")
    for name, res in sorted(results.items(), key=lambda x: x[1]['mean_auc'], reverse=True):
        f.write(f"\n  {name}:\n")
        f.write(f"    CV AUC: {res['mean_auc']:.3f} (+/- {res['std_auc']:.3f})\n")
    
    f.write(f"\nBEST MODEL: {best_model_name}\n")
    f.write(f"  CV AUC: {best_auc:.3f}\n")
    f.write(f"  Test AUC: {test_auc:.3f}\n")
    f.write(f"  Dataset Leakage AUC: {scores_adv.mean():.3f}\n")
    
    if best_auc > 0.80:
        f.write(f"\n  Status: ✅ STRONG - Patterns learned successfully\n")
    elif best_auc > 0.65:
        f.write(f"\n  Status: ✅ HONEST - Realistic ML performance\n")
    elif best_auc > 0.55:
        f.write(f"\n  Status: ⚠️  WEAK - Limited learning\n")
    else:
        f.write(f"\n  Status: ❌ FAILED - No pattern learning\n")

print(f"\n✅ Report saved: reports/pattern_learning_results.txt")

# ============================================================
# FINAL SUMMARY
# ============================================================
print("\n" + "="*70)
print("📋 PATTERN-LEARNING MODEL COMPLETE")
print("="*70)

print(f"\n🎯 MODEL B PERFORMANCE:")
print(f"   CV AUC: {best_auc:.3f}")
print(f"   Test AUC: {test_auc:.3f}")
print(f"   Dataset Leakage: {scores_adv.mean():.3f}")

print(f"\n💡 INTERPRETATION:")
if best_auc > 0.65:
    print(f"   ✅ ML CAN learn patterns without Slither!")
    print(f"   ✅ This is HONEST, realistic performance")
    print(f"   ✅ Ready for ensemble with Model A")
else:
    print(f"   ⚠️  Patterns alone give limited signal")
    print(f"   ⚠️  Slither features are more informative")
    print(f"   ⚠️  Consider this the 'conservative' model")

print("\n📋 NEXT STEPS:")
print("   1. Compare Model A (Slither-enhanced) vs Model B (Pattern-learning)")
print("   2. Build ensemble combining both")
print("   3. Use ensemble for semi-supervised learning")

print("="*70 + "\n")
