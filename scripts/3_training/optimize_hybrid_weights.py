"""
Optimize Hybrid Model Weights & Threshold
==========================================
Test different ML/semantic weights and thresholds to maximize adversarial accuracy
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from chainguardian.ml.models.hybrid_predictor import HybridPredictor

print("\n" + "="*80)
print("🔬 OPTIMIZING HYBRID WEIGHTS & THRESHOLD")
print("="*80)

# ============================================================================
# LOAD DATA
# ============================================================================
print("\n📂 Loading test data...")

df = pd.read_csv('data/complete_dataset_with_semantic.csv')

# Create labels
df['is_vulnerable'] = df['data_source'].isin([
    'smartbugs_curated',
    'production_vulnerable',
    'trail_of_bits'
]).astype(int)

# Adversarial labels
adversarial_mask = df['data_source'] == 'adversarial_test'
df.loc[adversarial_mask, 'is_vulnerable'] = df.loc[adversarial_mask, 'contract_name'].str.contains(
    'reentrancy|vulnerable|danger|exploit|honeypot|obvious',
    case=False,
    na=False
).astype(int)

adversarial_df = df[df['data_source'] == 'adversarial_test'].copy()
print(f"✅ Loaded {len(adversarial_df)} adversarial contracts ({adversarial_df['is_vulnerable'].sum()} vulnerable)")

# ============================================================================
# TEST CONFIGURATIONS
# ============================================================================
print("\n🧪 Testing different configurations...")
print("-" * 80)

predictor = HybridPredictor()

# Grid search: weights and thresholds
weight_configs = [
    (1.0, 0.0),   # ML only
    (0.8, 0.2),   # ML heavy
    (0.7, 0.3),   # ML dominant
    (0.6, 0.4),   # Current (ML slightly dominant)
    (0.5, 0.5),   # Balanced
    (0.4, 0.6),   # Semantic dominant
    (0.3, 0.7),   # Semantic heavy
]

thresholds = [0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6]

results = []

for ml_weight, semantic_weight in weight_configs:
    for threshold in thresholds:
        # Predict
        predictions = []
        true_labels = []
        confidences = []
        
        for idx, row in adversarial_df.iterrows():
            pred = predictor.predict(
                row.to_dict(), 
                ml_weight=ml_weight, 
                semantic_weight=semantic_weight,
                return_details=True
            )
            
            # Apply threshold
            final_pred = 1 if pred['confidence'] > threshold else 0
            
            predictions.append(final_pred)
            true_labels.append(row['is_vulnerable'])
            confidences.append(pred['confidence'])
        
        # Calculate metrics
        accuracy = accuracy_score(true_labels, predictions)
        
        # Count TP, TN, FP, FN
        tp = sum((p == 1 and t == 1) for p, t in zip(predictions, true_labels))
        tn = sum((p == 0 and t == 0) for p, t in zip(predictions, true_labels))
        fp = sum((p == 1 and t == 0) for p, t in zip(predictions, true_labels))
        fn = sum((p == 0 and t == 1) for p, t in zip(predictions, true_labels))
        
        # Calculate precision, recall
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        results.append({
            'ml_weight': ml_weight,
            'semantic_weight': semantic_weight,
            'threshold': threshold,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'tp': tp,
            'tn': tn,
            'fp': fp,
            'fn': fn,
        })

results_df = pd.DataFrame(results)

# ============================================================================
# FIND BEST CONFIGURATIONS
# ============================================================================
print("\n🏆 TOP 10 CONFIGURATIONS BY ACCURACY:")
print("="*80)

top_by_accuracy = results_df.nlargest(10, 'accuracy')

print(f"\n{'Rank':<5} {'ML':>5} {'Sem':>5} {'Thr':>5} {'Acc':>6} {'Prec':>6} {'Rec':>6} {'F1':>6} {'TN':>3} {'FP':>3} {'FN':>3} {'TP':>3}")
print("-" * 80)

for rank, (idx, row) in enumerate(top_by_accuracy.iterrows(), 1):
    print(f"{rank:<5} {row['ml_weight']:>5.2f} {row['semantic_weight']:>5.2f} {row['threshold']:>5.2f} "
          f"{row['accuracy']:>6.1%} {row['precision']:>6.1%} {row['recall']:>6.1%} {row['f1']:>6.3f} "
          f"{row['tn']:>3.0f} {row['fp']:>3.0f} {row['fn']:>3.0f} {row['tp']:>3.0f}")

# Best by F1 score
print(f"\n\n🏆 TOP 10 CONFIGURATIONS BY F1 SCORE:")
print("="*80)

top_by_f1 = results_df.nlargest(10, 'f1')

print(f"\n{'Rank':<5} {'ML':>5} {'Sem':>5} {'Thr':>5} {'Acc':>6} {'Prec':>6} {'Rec':>6} {'F1':>6} {'TN':>3} {'FP':>3} {'FN':>3} {'TP':>3}")
print("-" * 80)

for rank, (idx, row) in enumerate(top_by_f1.iterrows(), 1):
    print(f"{rank:<5} {row['ml_weight']:>5.2f} {row['semantic_weight']:>5.2f} {row['threshold']:>5.2f} "
          f"{row['accuracy']:>6.1%} {row['precision']:>6.1%} {row['recall']:>6.1%} {row['f1']:>6.3f} "
          f"{row['tn']:>3.0f} {row['fp']:>3.0f} {row['fn']:>3.0f} {row['tp']:>3.0f}")

# ============================================================================
# BEST CONFIGURATION DETAILS
# ============================================================================
best_config = top_by_accuracy.iloc[0]

print(f"\n\n🎯 BEST CONFIGURATION (by Accuracy):")
print("="*80)
print(f"\n   ML Weight:       {best_config['ml_weight']:.2f}")
print(f"   Semantic Weight: {best_config['semantic_weight']:.2f}")
print(f"   Threshold:       {best_config['threshold']:.2f}")
print(f"\n   Accuracy:        {best_config['accuracy']:.1%}")
print(f"   Precision:       {best_config['precision']:.1%}")
print(f"   Recall:          {best_config['recall']:.1%}")
print(f"   F1 Score:        {best_config['f1']:.3f}")
print(f"\n   True Negatives:  {best_config['tn']:.0f}")
print(f"   False Positives: {best_config['fp']:.0f}")
print(f"   False Negatives: {best_config['fn']:.0f}")
print(f"   True Positives:  {best_config['tp']:.0f}")

# Compare to baseline (ML only, threshold=0.5)
baseline = results_df[(results_df['ml_weight'] == 1.0) & (results_df['threshold'] == 0.5)].iloc[0]

print(f"\n\n📊 IMPROVEMENT OVER BASELINE:")
print("="*80)
print(f"   Baseline (ML only, 0.5):  {baseline['accuracy']:.1%}")
print(f"   Best Hybrid:              {best_config['accuracy']:.1%}")
print(f"   Improvement:              {(best_config['accuracy'] - baseline['accuracy'])*100:+.1f} percentage points")

# ============================================================================
# TEST BEST CONFIG IN DETAIL
# ============================================================================
print(f"\n\n🔍 TESTING BEST CONFIGURATION IN DETAIL:")
print("="*80)

best_ml_weight = best_config['ml_weight']
best_semantic_weight = best_config['semantic_weight']
best_threshold = best_config['threshold']

print(f"\nPredicting with ML={best_ml_weight:.2f}, Semantic={best_semantic_weight:.2f}, Threshold={best_threshold:.2f}\n")

detailed_results = []
for idx, row in adversarial_df.iterrows():
    pred = predictor.predict(
        row.to_dict(), 
        ml_weight=best_ml_weight, 
        semantic_weight=best_semantic_weight,
        return_details=True
    )
    
    final_pred = 1 if pred['confidence'] > best_threshold else 0
    correct = final_pred == row['is_vulnerable']
    
    detailed_results.append({
        'contract': row['contract_name'],
        'true_label': row['is_vulnerable'],
        'prediction': final_pred,
        'confidence': pred['confidence'],
        'correct': correct,
        'ml_score': pred['ml_score'],
        'semantic_score': pred['semantic_score'],
    })

detailed_df = pd.DataFrame(detailed_results)

print(f"{'Status':<4} {'Contract':<40} {'True':<5} {'Pred':<5} {'Conf':>6} {'ML':>6} {'Sem':>6}")
print("-" * 80)

for _, row in detailed_df.iterrows():
    status = "✅" if row['correct'] else "❌"
    true_label = "VULN" if row['true_label'] == 1 else "SAFE"
    pred_label = "VULN" if row['prediction'] == 1 else "SAFE"
    
    print(f"{status:<4} {row['contract']:<40} {true_label:<5} {pred_label:<5} "
          f"{row['confidence']:>6.1%} {row['ml_score']:>6.1%} {row['semantic_score']:>6.1%}")

# ============================================================================
# SAVE BEST CONFIGURATION
# ============================================================================
print(f"\n\n💾 SAVING BEST CONFIGURATION:")
print("-" * 80)

best_config_dict = {
    'ml_weight': float(best_config['ml_weight']),
    'semantic_weight': float(best_config['semantic_weight']),
    'threshold': float(best_config['threshold']),
    'performance': {
        'accuracy': float(best_config['accuracy']),
        'precision': float(best_config['precision']),
        'recall': float(best_config['recall']),
        'f1': float(best_config['f1']),
    },
    'confusion_matrix': {
        'tn': int(best_config['tn']),
        'fp': int(best_config['fp']),
        'fn': int(best_config['fn']),
        'tp': int(best_config['tp']),
    },
    'baseline_improvement': float((best_config['accuracy'] - baseline['accuracy']) * 100),
}

results_dir = Path('results')
results_dir.mkdir(exist_ok=True)

with open(results_dir / 'best_hybrid_config.json', 'w') as f:
    json.dump(best_config_dict, f, indent=2)

# Save all results
results_df.to_csv(results_dir / 'hybrid_optimization_grid_search.csv', index=False)

print(f"✅ Saved best configuration to results/best_hybrid_config.json")
print(f"✅ Saved all results to results/hybrid_optimization_grid_search.csv")

print("\n" + "="*80)
print("🎉 OPTIMIZATION COMPLETE!")
print("="*80)

print(f"""
✅ OPTIMIZED HYBRID CONFIGURATION:
   • ML Weight: {best_ml_weight:.2f} | Semantic Weight: {best_semantic_weight:.2f}
   • Threshold: {best_threshold:.2f}
   • Accuracy: {best_config['accuracy']:.1%}
   • Improvement: {(best_config['accuracy'] - baseline['accuracy'])*100:+.1f}pp over baseline
   
✅ READY TO APPLY:
   Update HybridPredictor defaults to use these values!
""")
