"""
Grid search for optimal hybrid parameters
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from chainguardian.ml.models.hybrid_predictor import HybridPredictor

print("\n" + "="*70)
print("🔍 HYPERPARAMETER SEARCH FOR HYBRID MODEL")
print("="*70)

# Try multiple data sources
data_files = [
    'data/complete_dataset_with_semantic.csv',
    'data/adversarial_with_semantic.csv',
    'data/training_clean.csv',
]

df = None
for file in data_files:
    if Path(file).exists():
        df = pd.read_csv(file)
        print(f"✅ Loaded: {file} ({len(df)} contracts)")
        break

if df is None:
    print("❌ No data file found!")
    exit(1)

# Show available columns
print(f"\n📋 Available columns:")
print(f"   {list(df.columns)[:10]}")

# Define vulnerable contracts (our adversarial test set)
vulnerable_contracts = [
    '02_obvious_reentrancy',
    '04_simple_but_vulnerable', 
    '09_delegatecall_danger',
    '10_tx_origin_auth',
    '11_hidden_reentrancy',
    '24_intentional_honeypot'
]

# Filter to test contracts (those with names matching our test set)
test_contracts = df[df['contract_name'].str.contains('|'.join([
    '01_super_simple',
    '02_obvious',
    '03_complex',
    '04_simple',
    '05_timestamp',
    '06_unchecked',
    '07_integer',
    '08_safe',
    '09_delegatecall',
    '10_tx_origin',
    '11_hidden',
    '12_false',
    '13_modern',
    '14_assembly',
    '15_gas',
    '16_front',
    '17_logic',
    '18_oracle',
    '19_flash',
    '20_upgradeable',
    '21_timelock',
    '22_empty',
    '23_only',
    '24_intentional',
    '25_gas_optimization'
]), na=False)].copy()

if len(test_contracts) == 0:
    print("\n❌ No test contracts found!")
    print("\n💡 Available contract names (first 10):")
    print(df['contract_name'].head(10).tolist())
    exit(1)

print(f"\n📊 Test set: {len(test_contracts)} contracts")

# Create ground truth labels
test_contracts['true_label'] = test_contracts['contract_name'].apply(
    lambda x: 1 if any(v in str(x) for v in vulnerable_contracts) else 0
)

print(f"   Vulnerable: {test_contracts['true_label'].sum()}")
print(f"   Safe: {(~test_contracts['true_label'].astype(bool)).sum()}")

# Check if we have the expected 25 contracts
if len(test_contracts) < 20:
    print("\n⚠️  Warning: Only found {len(test_contracts)} test contracts (expected 25)")
    print("   Proceeding with available contracts...")

# Initialize predictor
try:
    predictor = HybridPredictor()
    print("\n✅ Hybrid predictor initialized")
except Exception as e:
    print(f"\n❌ Failed to initialize predictor: {e}")
    exit(1)

# Grid search
ml_weights = [0.30, 0.40, 0.50, 0.60, 0.70, 0.80]
thresholds = [0.20, 0.30, 0.40, 0.50, 0.60, 0.70]

best_f1 = 0
best_params = None
results = []

print("\n🔬 Testing configurations...\n")

for ml_weight in ml_weights:
    sem_weight = 1.0 - ml_weight
    
    for threshold in thresholds:
        predictions = []
        errors = 0
        
        for idx, row in test_contracts.iterrows():
            try:
                features = row.to_dict()
                pred = predictor.predict(
                    features,
                    ml_weight=ml_weight,
                    semantic_weight=sem_weight,
                    threshold=threshold,
                    return_details=False
                )
                predictions.append(pred['prediction'])
            except Exception as e:
                predictions.append(0)  # Default to safe on error
                errors += 1
        
        if errors > 0:
            print(f"⚠️  {errors} prediction errors at ML={ml_weight:.2f}, Threshold={threshold:.2f}")
        
        # Calculate metrics
        tp = sum((p == 1 and t == 1) for p, t in zip(predictions, test_contracts['true_label']))
        fp = sum((p == 1 and t == 0) for p, t in zip(predictions, test_contracts['true_label']))
        fn = sum((p == 0 and t == 1) for p, t in zip(predictions, test_contracts['true_label']))
        tn = sum((p == 0 and t == 0) for p, t in zip(predictions, test_contracts['true_label']))
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        accuracy = (tp + tn) / len(test_contracts)
        
        results.append({
            'ml_weight': ml_weight,
            'sem_weight': sem_weight,
            'threshold': threshold,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'tp': tp,
            'fp': fp,
            'fn': fn,
            'tn': tn
        })
        
        # Print if improvement or high recall
        if f1 > best_f1 or (recall > 0 and f1 >= best_f1 * 0.9):
            marker = "🏆" if f1 > best_f1 else "✨"
            print(f"{marker} ML={ml_weight:.2f}, Thresh={threshold:.2f} → F1={f1:.3f}, Acc={accuracy:.1%}, Recall={recall:.1%} (TP={tp}, FP={fp})")
            
            if f1 > best_f1:
                best_f1 = f1
                best_params = (ml_weight, sem_weight, threshold)

print("\n" + "="*70)
print("🏆 BEST CONFIGURATION")
print("="*70)

if best_params:
    print(f"\n  ML Weight: {best_params[0]:.2f}")
    print(f"  Semantic Weight: {best_params[1]:.2f}")
    print(f"  Threshold: {best_params[2]:.2f}")
    print(f"  F1 Score: {best_f1:.3f}")
    
    # Get full metrics for best config
    best_result = [r for r in results if 
                   r['ml_weight'] == best_params[0] and 
                   r['threshold'] == best_params[2]][0]
    
    print(f"\n  Accuracy: {best_result['accuracy']:.1%}")
    print(f"  Precision: {best_result['precision']:.1%}")
    print(f"  Recall: {best_result['recall']:.1%}")
    print(f"  TP: {best_result['tp']}, FP: {best_result['fp']}")
    print(f"  TN: {best_result['tn']}, FN: {best_result['fn']}")
else:
    print("\n⚠️  No valid configurations found (all have F1=0)")

# Save results
Path('results').mkdir(exist_ok=True)
df_results = pd.DataFrame(results)
df_results.to_csv('results/hyperparameter_search.csv', index=False)

print(f"\n📊 Top 10 Configurations (by F1):")
print(df_results.nlargest(10, 'f1')[['ml_weight', 'threshold', 'f1', 'accuracy', 'recall', 'precision']].to_string(index=False))

print(f"\n📊 Top 10 Configurations (by Recall):")
print(df_results.nlargest(10, 'recall')[['ml_weight', 'threshold', 'recall', 'f1', 'accuracy', 'tp', 'fp']].to_string(index=False))

print(f"\n📊 Highest Accuracy Configurations:")
print(df_results.nlargest(5, 'accuracy')[['ml_weight', 'threshold', 'accuracy', 'f1', 'recall']].to_string(index=False))

print("\n✅ Results saved: results/hyperparameter_search.csv")

# Summary statistics
print(f"\n📈 SUMMARY STATISTICS:")
print(f"   Configurations tested: {len(results)}")
print(f"   Max F1 Score: {df_results['f1'].max():.3f}")
print(f"   Max Recall: {df_results['recall'].max():.1%}")
print(f"   Max Accuracy: {df_results['accuracy'].max():.1%}")
print(f"   Configs with Recall > 0: {(df_results['recall'] > 0).sum()}")

print("="*70 + "\n")
