#!/usr/bin/env python3
"""Test predictor on vulnerable contracts only."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from chainguardian.ml.hybrid_predictor import HybridVulnerabilityPredictor
import pandas as pd

print("="*80)
print("TESTING VULNERABLE CONTRACTS ONLY")
print("="*80)

df = pd.read_csv("data/training_with_semantic_20251222.csv")

# Filter vulnerable contracts
vuln_df = df[df['label'] == 1].head(10)
safe_df = df[df['label'] == 0].head(5)

print(f"Testing {len(vuln_df)} vulnerable + {len(safe_df)} safe contracts")

predictor = HybridVulnerabilityPredictor(mode="db_calibrated")

results = []
for idx, row in vuln_df.iterrows():
    features = row.drop(['label']).to_dict()
    result = predictor.predict(features)
    results.append((idx, 1, result['label'], result['prob_vulnerable'], result['risk_category']))

for idx, row in safe_df.iterrows():
    features = row.drop(['label']).to_dict()
    result = predictor.predict(features)
    results.append((idx, 0, result['label'], result['prob_vulnerable'], result['risk_category']))

print("\n📊 RESULTS:")
print("-" * 80)
print(f"{'Contract':<25} {'Actual':<6} {'Pred':<6} {'Prob':<8} {'Risk'}")
print("-" * 80)

for idx, actual, pred, prob, risk in results:
    status = "✅" if actual == pred else "❌"
    print(f"{status} {idx:<25} {actual:<6} {pred:<6} {prob:<8.3f} {risk}")

correct = sum(1 for _, actual, pred, _, _ in results if actual == pred)
print(f"\n🎯 Accuracy: {correct}/{len(results)} ({correct/len(results)*100:.1f}%)")
