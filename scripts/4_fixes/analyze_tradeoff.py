"""
Analyze precision-recall tradeoff to find optimal production config
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

print("\n" + "="*70)
print("📊 PRECISION-RECALL TRADEOFF ANALYSIS")
print("="*70)

# Load search results
df = pd.read_csv('results/hyperparameter_search.csv')

print(f"\n📋 Total configurations: {len(df)}")

# Find configurations with different trade-offs
print("\n🎯 RECOMMENDED CONFIGURATIONS:\n")

# 1. High Recall (Security First)
high_recall = df[df['recall'] >= 0.8].nlargest(1, 'precision')
if len(high_recall) > 0:
    print("1️⃣  SECURITY-FIRST (High Recall):")
    row = high_recall.iloc[0]
    print(f"   ML={row['ml_weight']:.2f}, Threshold={row['threshold']:.2f}")
    print(f"   Recall: {row['recall']:.1%} | Precision: {row['precision']:.1%} | F1: {row['f1']:.3f}")
    print(f"   → Catches {row['tp']:.0f}/6 vulnerabilities, {row['fp']:.0f} false alarms")
    print()

# 2. Balanced F1
balanced = df.nlargest(1, 'f1')
if len(balanced) > 0:
    print("2️⃣  BALANCED (Best F1):")
    row = balanced.iloc[0]
    print(f"   ML={row['ml_weight']:.2f}, Threshold={row['threshold']:.2f}")
    print(f"   Recall: {row['recall']:.1%} | Precision: {row['precision']:.1%} | F1: {row['f1']:.3f}")
    print(f"   → Catches {row['tp']:.0f}/6 vulnerabilities, {row['fp']:.0f} false alarms")
    print()

# 3. High Precision (Minimize False Positives)
high_precision = df[df['precision'] >= 0.5].nlargest(1, 'recall')
if len(high_precision) > 0:
    print("3️⃣  CONSERVATIVE (High Precision):")
    row = high_precision.iloc[0]
    print(f"   ML={row['ml_weight']:.2f}, Threshold={row['threshold']:.2f}")
    print(f"   Recall: {row['recall']:.1%} | Precision: {row['precision']:.1%} | F1: {row['f1']:.3f}")
    print(f"   → Catches {row['tp']:.0f}/6 vulnerabilities, {row['fp']:.0f} false alarms")
    print()

# 4. Custom recommendation: 70%+ recall with best precision
custom = df[df['recall'] >= 0.7].nlargest(1, 'precision')
if len(custom) > 0:
    print("4️⃣  RECOMMENDED (70% Recall + Best Precision):")
    row = custom.iloc[0]
    print(f"   ML={row['ml_weight']:.2f}, Threshold={row['threshold']:.2f}")
    print(f"   Recall: {row['recall']:.1%} | Precision: {row['precision']:.1%} | F1: {row['f1']:.3f}")
    print(f"   → Catches {row['tp']:.0f}/6 vulnerabilities, {row['fp']:.0f} false alarms")
    print()

# Create visualization
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# 1. Precision vs Recall
ax = axes[0, 0]
scatter = ax.scatter(df['recall'], df['precision'], 
                    c=df['f1'], cmap='RdYlGn', s=100, alpha=0.6)
ax.set_xlabel('Recall')
ax.set_ylabel('Precision')
ax.set_title('Precision vs Recall (colored by F1)')
plt.colorbar(scatter, ax=ax, label='F1 Score')
ax.grid(True, alpha=0.3)

# 2. F1 vs Threshold
ax = axes[0, 1]
for ml_weight in df['ml_weight'].unique():
    subset = df[df['ml_weight'] == ml_weight]
    ax.plot(subset['threshold'], subset['f1'], marker='o', label=f'ML={ml_weight:.1f}')
ax.set_xlabel('Threshold')
ax.set_ylabel('F1 Score')
ax.set_title('F1 Score vs Threshold')
ax.legend()
ax.grid(True, alpha=0.3)

# 3. Accuracy vs Recall
ax = axes[1, 0]
scatter = ax.scatter(df['recall'], df['accuracy'],
                    c=df['threshold'], cmap='viridis', s=100, alpha=0.6)
ax.set_xlabel('Recall')
ax.set_ylabel('Accuracy')
ax.set_title('Accuracy vs Recall (colored by threshold)')
plt.colorbar(scatter, ax=ax, label='Threshold')
ax.grid(True, alpha=0.3)

# 4. Confusion Matrix Heatmap for Best Config
ax = axes[1, 1]
best = df.nlargest(1, 'f1').iloc[0]
confusion = [[best['tn'], best['fp']], [best['fn'], best['tp']]]
im = ax.imshow(confusion, cmap='Blues', aspect='auto')
ax.set_xticks([0, 1])
ax.set_yticks([0, 1])
ax.set_xticklabels(['Pred Safe', 'Pred Vuln'])
ax.set_yticklabels(['True Safe', 'True Vuln'])
ax.set_title(f'Best Config Confusion Matrix\nML={best["ml_weight"]:.2f}, Thresh={best["threshold"]:.2f}')
for i in range(2):
    for j in range(2):
        text = ax.text(j, i, f'{int(confusion[i][j])}',
                      ha="center", va="center", color="black", fontsize=16)
plt.colorbar(im, ax=ax)

plt.tight_layout()
plt.savefig('results/hyperparameter_tradeoff.png', dpi=150, bbox_inches='tight')
print("📊 Visualization saved: results/hyperparameter_tradeoff.png")

# Generate config file for production
best_config = df.nlargest(1, 'f1').iloc[0]

config = {
    "model_version": "hybrid_v2_optimized",
    "ml_weight": float(best_config['ml_weight']),
    "semantic_weight": float(best_config['sem_weight']),
    "threshold": float(best_config['threshold']),
    "performance": {
        "f1_score": float(best_config['f1']),
        "accuracy": float(best_config['accuracy']),
        "precision": float(best_config['precision']),
        "recall": float(best_config['recall']),
        "true_positives": int(best_config['tp']),
        "false_positives": int(best_config['fp']),
        "true_negatives": int(best_config['tn']),
        "false_negatives": int(best_config['fn'])
    },
    "use_case": "balanced_security_audit",
    "notes": "Optimized for maximum vulnerability detection with acceptable false positive rate"
}

import json
with open('models/production_config_optimized.json', 'w') as f:
    json.dump(config, f, indent=2)

print("\n✅ Production config saved: models/production_config_optimized.json")
print("\n" + "="*70)
print("💡 DEPLOYMENT RECOMMENDATIONS")
print("="*70)

print("""
🎯 USE CASE SELECTION:

1. SECURITY AUDIT (Recommended):
   → Use Config #1 (High Recall)
   → Better to over-flag than miss vulnerabilities
   → Human auditor reviews all flagged contracts
   
2. TRIAGE SYSTEM:
   → Use Config #2 (Balanced F1)
   → Good first-pass filter
   → High-risk flagged for immediate review
   
3. AUTOMATED GATING:
   → Use Config #3 (High Precision)
   → Only if false positives are very costly
   → May miss some vulnerabilities!

🚀 NEXT STEPS:
   1. Update hybrid_predictor.py with optimal config
   2. Re-run production test to verify
   3. Deploy with confidence intervals
   4. Monitor false positive/negative rates
""")

print("="*70 + "\n")
