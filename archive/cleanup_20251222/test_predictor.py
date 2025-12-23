#!/usr/bin/env python3
"""Test the hybrid predictor with database export."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from chainguardian.ml.hybrid_predictor import HybridVulnerabilityPredictor
import pandas as pd

print("="*80)
print("TESTING HYBRID PREDICTOR WITH REAL DATA")
print("="*80)

# Load dataset
df = pd.read_csv("data/training_with_semantic_20251222.csv")
print(f"\n✅ Loaded {len(df)} contracts")

# Initialize predictor
predictor = HybridVulnerabilityPredictor(mode="db_calibrated")
print(f"✅ Predictor loaded")

# Test on first 5 contracts
print(f"\n🧪 Testing on 5 sample contracts:")
print("-"*80)

for idx in range(5):
    row = df.iloc[idx]
    features = row.drop(['label']).to_dict()
    
    result = predictor.predict(features)
    actual = int(row['label'])
    
    match = "✅" if result['label'] == actual else "❌"
    print(f"{match} Contract {idx+1}:")
    print(f"   Predicted: {result['label']} ({result['risk_category']}, prob={result['prob_vulnerable']:.3f})")
    print(f"   Actual:    {actual}")

print("\n" + "="*80 + "\n")
