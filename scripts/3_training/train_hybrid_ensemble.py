"""
Hybrid Ensemble: ML Detector + Semantic Rules
==============================================
Combines XGBoost (syntactic) with semantic security rules
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

print("\n" + "="*80)
print("🔀 HYBRID ENSEMBLE: ML + SEMANTIC RULES")
print("="*80)

# ============================================================================
# STEP 1: LOAD TRAINED MODEL
# ============================================================================
print("\n📊 STEP 1: LOADING TRAINED MODEL")
print("-" * 80)

# Find latest model
models_dir = Path('models')
model_files = sorted(models_dir.glob('semantic_xgboost_*.pkl'))
scaler_files = sorted(models_dir.glob('semantic_scaler_*.pkl'))

if not model_files:
    print("❌ No trained model found! Run train_with_semantic_production.py first")
    sys.exit(1)

ml_model = joblib.load(model_files[-1])
scaler = joblib.load(scaler_files[-1])

print(f"✅ Loaded ML model: {model_files[-1].name}")

# ============================================================================
# STEP 2: DEFINE SEMANTIC RULES
# ============================================================================
print("\n🧠 STEP 2: SEMANTIC SECURITY RULES")
print("-" * 80)

def semantic_risk_score(row):
    """
    Calculate semantic risk score based on security patterns
    
    Returns score 0.0-1.0 where:
    - 0.0 = Perfectly safe semantic patterns
    - 1.0 = Multiple semantic vulnerabilities
    """
    risk = 0.0
    
    # CEI Pattern Violations (HIGH RISK)
    if row['cei_violations'] > 0:
        risk += 0.4 * min(row['cei_violations'] / 5, 1.0)  # Cap at 5 violations
    
    # Low CEI score (MEDIUM RISK)
    if row['cei_pattern_score'] < 0.8:
        risk += 0.2 * (1.0 - row['cei_pattern_score'])
    
    # State modifications after external calls (HIGH RISK)
    if row['state_after_call_count'] > 0:
        risk += 0.3 * min(row['state_after_call_count'] / 3, 1.0)
    
    # Unchecked calls in critical context (MEDIUM RISK)
    if row['unchecked_calls_in_critical_context'] > 0:
        risk += 0.2 * min(row['unchecked_calls_in_critical_context'] / 2, 1.0)
    
    # Reentrancy guard REDUCES risk (if external calls exist)
    if row['has_reentrancy_guard'] and row['num_external_calls'] > 0:
        risk *= 0.5  # 50% risk reduction
    
    # Cap at 1.0
    return min(risk, 1.0)

def hybrid_predict(row, ml_score, ml_threshold=0.5, semantic_weight=0.4):
    """
    Hybrid prediction combining ML and semantic analysis
    
    Args:
        row: Contract features
        ml_score: ML model probability
        ml_threshold: Threshold for ML prediction
        semantic_weight: Weight for semantic score (0-1)
    
    Returns:
        (prediction, confidence, reasoning)
    """
    semantic_score = semantic_risk_score(row)
    
    # Weighted ensemble
    ml_weight = 1.0 - semantic_weight
    final_score = (ml_weight * ml_score) + (semantic_weight * semantic_score)
    
    prediction = 1 if final_score > ml_threshold else 0
    
    # Generate reasoning
    reasons = []
    
    if semantic_score > 0.5:
        if row['cei_violations'] > 0:
            reasons.append(f"CEI violations: {row['cei_violations']}")
        if row['state_after_call_count'] > 0:
            reasons.append(f"State-after-call: {row['state_after_call_count']}")
        if row['unchecked_calls_in_critical_context'] > 0:
            reasons.append(f"Unchecked calls: {row['unchecked_calls_in_critical_context']}")
    
    if row['has_reentrancy_guard']:
        reasons.append("✅ Has reentrancy guard")
    
    if row['cei_pattern_score'] == 1.0:
        reasons.append("✅ Perfect CEI compliance")
    
    reasoning = " | ".join(reasons) if reasons else "Standard ML prediction"
    
    return prediction, final_score, semantic_score, reasoning

print("✅ Semantic rules defined:")
print("   • CEI violation detection (40% risk)")
print("   • State-after-call pattern (30% risk)")
print("   • Unchecked critical calls (20% risk)")
print("   • Reentrancy guard bonus (50% reduction)")

# ============================================================================
# STEP 3: EVALUATE ON ADVERSARIAL SET
# ============================================================================
print("\n🎯 STEP 3: HYBRID EVALUATION ON ADVERSARIAL SET")
print("-" * 80)

# Load data
df = pd.read_csv('data/complete_dataset_with_semantic.csv')

# Get adversarial test set
adversarial_df = df[df['data_source'] == 'adversarial_test'].copy()

# Create labels
adversarial_df['is_vulnerable'] = adversarial_df['contract_name'].str.contains(
    'reentrancy|vulnerable|danger|exploit|honeypot|obvious',
    case=False,
    na=False
).astype(int)

print(f"Adversarial contracts: {len(adversarial_df)}")
print(f"Vulnerable: {adversarial_df['is_vulnerable'].sum()}")
print(f"Safe: {(~adversarial_df['is_vulnerable'].astype(bool)).sum()}")

# Load metadata to get feature list
import json
metadata_files = sorted(models_dir.glob('semantic_metadata_*.json'))
with open(metadata_files[-1], 'r') as f:
    metadata = json.load(f)

features = metadata['feature_list']

# Prepare features
X_adv = adversarial_df[features]
X_adv_scaled = scaler.transform(X_adv)

# Get ML predictions
ml_predictions = ml_model.predict_proba(X_adv_scaled)[:, 1]

# Get hybrid predictions
results = []
for idx, (_, row) in enumerate(adversarial_df.iterrows()):
    ml_score = ml_predictions[idx]
    pred, final_score, semantic_score, reasoning = hybrid_predict(
        row, ml_score, semantic_weight=0.4
    )
    
    results.append({
        'contract': row['contract_name'],
        'true_label': row['is_vulnerable'],
        'ml_score': ml_score,
        'semantic_score': semantic_score,
        'final_score': final_score,
        'prediction': pred,
        'reasoning': reasoning
    })

results_df = pd.DataFrame(results)
results_df['correct'] = results_df['true_label'] == results_df['prediction']

# Calculate metrics
accuracy = results_df['correct'].sum() / len(results_df)

print(f"\n📊 HYBRID MODEL PERFORMANCE:")
print(f"   Accuracy: {accuracy:.1%}")

print(f"\n📋 DETAILED RESULTS:")
print("-" * 80)

for _, row in results_df.iterrows():
    status = "✅" if row['correct'] else "❌"
    true_label = "VULN" if row['true_label'] == 1 else "SAFE"
    pred_label = "VULN" if row['prediction'] == 1 else "SAFE"
    
    print(f"{status} {row['contract']:40s}")
    print(f"      True: {true_label:4s} | Pred: {pred_label:4s} | ML: {row['ml_score']:.2%} | Semantic: {row['semantic_score']:.2%} | Final: {row['final_score']:.2%}")
    print(f"      {row['reasoning']}")
    print()

# ============================================================================
# STEP 4: COMPARISON
# ============================================================================
print("\n" + "="*80)
print("📊 PERFORMANCE COMPARISON")
print("="*80)

ml_predictions_binary = (ml_predictions > 0.5).astype(int)
ml_accuracy = (ml_predictions_binary == adversarial_df['is_vulnerable'].values).sum() / len(adversarial_df)

print(f"\nML Only:     {ml_accuracy:.1%}")
print(f"Hybrid:      {accuracy:.1%}")
print(f"Improvement: {(accuracy - ml_accuracy)*100:+.1f} percentage points")

# Show specific improvements
improved = results_df[
    (results_df['correct']) & 
    (ml_predictions_binary != adversarial_df['is_vulnerable'].values)
]

if len(improved) > 0:
    print(f"\n✅ Contracts fixed by semantic rules: {len(improved)}")
    for _, row in improved.iterrows():
        print(f"   • {row['contract']}: {row['reasoning']}")

# ============================================================================
# STEP 5: SAVE HYBRID MODEL
# ============================================================================
print("\n💾 STEP 5: SAVING HYBRID MODEL")
print("-" * 80)

from datetime import datetime
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

hybrid_metadata = {
    'timestamp': timestamp,
    'ml_model': str(model_files[-1]),
    'semantic_weight': 0.4,
    'ml_weight': 0.6,
    'adversarial_accuracy': accuracy,
    'ml_only_accuracy': ml_accuracy,
    'improvement': accuracy - ml_accuracy
}

with open(models_dir / f'hybrid_metadata_{timestamp}.json', 'w') as f:
    json.dump(hybrid_metadata, f, indent=2)

print(f"✅ Saved hybrid model metadata")

print("\n" + "="*80)
print("🎉 HYBRID ENSEMBLE COMPLETE!")
print("="*80 + "\n")
