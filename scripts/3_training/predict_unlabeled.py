"""
Predict on 84 unlabeled contracts using LLM feeder pipeline.
"""

import pandas as pd
import joblib
import json
from pathlib import Path

print("\n" + "="*70)
print("🔮 PREDICTING UNLABELED CONTRACTS")
print("="*70)

# Load unlabeled data
df_unlabeled = pd.read_csv('data/prediction_clean.csv')
df_unlabeled_full = pd.read_csv('data/prediction_unlabeled_full.csv')

print(f"\nUnlabeled contracts: {len(df_unlabeled)}")

# Load models
models_dir = Path('models')
risk_scorer = joblib.load(models_dir / 'risk_scorer.pkl')
severity_clf = joblib.load(models_dir / 'severity_classifier.pkl')
multilabel_clf = joblib.load(models_dir / 'multilabel_classifier.pkl')

with open(models_dir / 'vulnerability_labels.json', 'r') as f:
    vuln_labels = json.load(f)

print(f"✅ Models loaded")

# Predict
predictions = []

for idx, row in df_unlabeled.iterrows():
    features = row.values.reshape(1, -1)
    
    # Risk score
    risk = risk_scorer.predict(features)[0]
    
    # Severity
    severity_pred = severity_clf.predict(features)[0]
    severity_proba = severity_clf.predict_proba(features)[0]
    severity_names = ['Low', 'Medium', 'High', 'Critical']
    
    # Vulnerabilities
    vuln_pred = multilabel_clf.predict(features)[0]
    
    # Get contract info
    contract_info = df_unlabeled_full.iloc[idx]
    
    predictions.append({
        'contract_name': contract_info.get('contract_name', f'Contract_{idx}'),
        'address': contract_info.get('address', 'N/A'),
        'data_source': contract_info.get('data_source', 'manual'),
        'risk_score': float(risk),
        'severity': severity_names[severity_pred],
        'severity_confidence': float(severity_proba[severity_pred]),
        'vulnerabilities': {
            vuln_labels[i]: bool(vuln_pred[i]) 
            for i in range(len(vuln_labels))
        }
    })

# Convert to DataFrame
df_predictions = pd.DataFrame(predictions)

# Sort by risk score
df_predictions = df_predictions.sort_values('risk_score', ascending=False)

# Save
df_predictions.to_csv('reports/unlabeled_predictions.csv', index=False)

print(f"\n✅ Predictions complete!")

# Show statistics
print(f"\n📊 PREDICTION STATISTICS:")
print(f"\nRisk Score Distribution:")
print(f"  Mean: {df_predictions['risk_score'].mean():.1f}")
print(f"  Std: {df_predictions['risk_score'].std():.1f}")
print(f"  Min: {df_predictions['risk_score'].min():.1f}")
print(f"  Max: {df_predictions['risk_score'].max():.1f}")

print(f"\nSeverity Distribution:")
for sev in ['Low', 'Medium', 'High', 'Critical']:
    count = (df_predictions['severity'] == sev).sum()
    pct = count / len(df_predictions) * 100
    print(f"  {sev:15s}: {count:2d} ({pct:5.1f}%)")

print(f"\n🚨 TOP 10 HIGHEST RISK CONTRACTS:")
print(f"{'Rank':4s} {'Risk':6s} {'Severity':10s} {'Contract':40s}")
print("-" * 70)

for i, row in df_predictions.head(10).iterrows():
    rank = i + 1
    risk = f"{row['risk_score']:.1f}"
    sev = row['severity']
    name = row['contract_name'][:38]
    print(f"{rank:4d} {risk:6s} {sev:10s} {name:40s}")

print(f"\n✅ Saved: reports/unlabeled_predictions.csv")
print("="*70 + "\n")
