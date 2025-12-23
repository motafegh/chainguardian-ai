"""
Test Hybrid Predictor with Clean v5 Model - FIXED
=================================================
Tests with correct llm_ready parameter.

Author: Ali
Date: December 22, 2024
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

import pandas as pd
import json
from chainguardian.ml.models.hybrid_predictor import HybridPredictor

print("\n" + "="*80)
print("🧪 HYBRID PREDICTOR v5 COMPREHENSIVE TEST")
print("="*80)

# Load test data
data_path = Path("data/ml_ready_v4.csv")
df = pd.read_csv(data_path)

vuln_samples = df[df['ground_truth_vulnerable'] == 1].sample(3, random_state=42)
safe_samples = df[df['ground_truth_vulnerable'] == 0].sample(3, random_state=42)
test_samples = pd.concat([vuln_samples, safe_samples])

print(f"\n📥 Loading test data...")
print(f"   ✅ Loaded {len(test_samples)} test samples:")
print(f"      {(test_samples['ground_truth_vulnerable'] == 1).sum()} vulnerable")
print(f"      {(test_samples['ground_truth_vulnerable'] == 0).sum()} safe")

# Initialize predictor
print(f"\n🔧 Initializing HybridPredictor...")

try:
    predictor = HybridPredictor(
        model_path="models/production_model_v5_clean.pkl",
        scaler_path="models/production_scaler_v5_clean.pkl",
        metadata_path="models/feature_metadata_v5.json",
        enable_shap=True
    )
    print(f"   ✅ v5 model loaded")
except FileNotFoundError:
    print(f"   ⚠️  v5 model not found, using v4")
    predictor = HybridPredictor(enable_shap=True)

print(f"   Expected features: {len(predictor.feature_names)}")

# Test individual contracts
print("\n" + "="*80)
print("🔬 TESTING INDIVIDUAL CONTRACTS")
print("="*80)

results = []

for idx, row in test_samples.iterrows():
    print(f"\n{'─'*80}")
    
    contract_name = row['contract_name']
    ground_truth = row['ground_truth_vulnerable']
    
    print(f"📄 Contract: {contract_name}")
    print(f"   Ground Truth: {'🔴 VULNERABLE' if ground_truth else '🟢 SAFE'}")
    
    # Prepare features
    exclude_cols = ['ground_truth_vulnerable', 'contract_name', 'data_source']
    features = {col: row[col] for col in row.index if col not in exclude_cols}
    
    try:
        # CRITICAL FIX: Use llm_ready=True for structured output
        result = predictor.predict(
            features=features,
            return_details=True,
            explain=True,
            llm_ready=True  # ✅ This returns the structured format
        )
        
        # Now result['prediction'] is a dict with 'label', 'confidence', etc.
        print(f"\n   🤖 PREDICTION:")
        print(f"      Label:      {result['prediction']['label']}")
        print(f"      Confidence: {result['prediction']['confidence']:.2%}")
        print(f"      Risk Level: {result['prediction']['risk_level']}")
        print(f"      Method:     {result['prediction']['method']}")
        
        # ML analysis
        if 'ml_analysis' in result:
            print(f"\n   📊 ML ANALYSIS:")
            print(f"      Score: {result['ml_analysis']['score']:.4f}")
        
        # Semantic analysis
        if 'semantic_analysis' in result:
            print(f"\n   🔍 SEMANTIC ANALYSIS:")
            print(f"      Score: {result['semantic_analysis']['score']:.4f}")
            print(f"      CEI Violations: {result['semantic_analysis']['cei_violations']}")
            if result['semantic_analysis']['findings']:
                print(f"      Findings:")
                for finding in result['semantic_analysis']['findings'][:3]:
                    print(f"         • {finding}")
        
        # SHAP
        if 'explainability' in result and 'top_risk_factors' in result['explainability']:
            print(f"\n   💡 TOP 5 RISK FACTORS:")
            for factor in result['explainability']['top_risk_factors'][:5]:
                contrib = factor.get('contribution', 0)
                print(f"      {contrib:+.3f} | {factor['feature']}")
        
        # Override
        if 'override' in result and result['override']['triggered']:
            print(f"\n   ⚠️  OVERRIDE:")
            print(f"      {result['override']['reason']}")
        
        # Check correctness
        predicted_label = 1 if result['prediction']['label'] == 'VULNERABLE' else 0
        correct = predicted_label == ground_truth
        
        results.append({
            'contract': contract_name,
            'ground_truth': ground_truth,
            'predicted': predicted_label,
            'confidence': result['prediction']['confidence'],
            'correct': correct
        })
        
        if correct:
            print(f"\n   ✅ CORRECT PREDICTION!")
        else:
            print(f"\n   ❌ INCORRECT PREDICTION")
    
    except Exception as e:
        print(f"\n   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

# Batch summary
print("\n" + "="*80)
print("📊 BATCH RESULTS")
print("="*80)

if results:
    results_df = pd.DataFrame(results)
    accuracy = results_df['correct'].mean()
    
    print(f"\n   Total:    {len(results_df)}")
    print(f"   Correct:  {results_df['correct'].sum()}")
    print(f"   Accuracy: {accuracy:.2%}")
    
    # Method breakdown
    vuln_preds = results_df[results_df['predicted'] == 1]
    safe_preds = results_df[results_df['predicted'] == 0]
    
    print(f"\n   Predictions:")
    print(f"      Vulnerable: {len(vuln_preds)}")
    print(f"      Safe:       {len(safe_preds)}")
    
    # Errors
    if not results_df['correct'].all():
        print(f"\n   ⚠️  ERRORS:")
        errors = results_df[~results_df['correct']]
        for _, error in errors.iterrows():
            gt = 'VULN' if error['ground_truth'] else 'SAFE'
            pred = 'VULN' if error['predicted'] else 'SAFE'
            print(f"      • {error['contract']}: GT={gt}, Pred={pred}")

# LLM output test
print("\n" + "="*80)
print("🤖 LLM OUTPUT FORMAT TEST")
print("="*80)

test_contract = vuln_samples.iloc[0]
exclude_cols = ['ground_truth_vulnerable', 'contract_name', 'data_source']
features = {col: test_contract[col] for col in test_contract.index if col not in exclude_cols}

try:
    result = predictor.predict(features, llm_ready=True)
    
    print(f"\n📄 Sample LLM-Ready Output:")
    print(f"   Contract: {test_contract['contract_name']}")
    
    # Save to file
    output_path = Path("models/sample_llm_output.json")
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n   ✅ Full JSON saved to: {output_path}")
    print(f"   Structure:")
    for key in result.keys():
        print(f"      • {key}")
    
except Exception as e:
    print(f"   ❌ ERROR: {e}")

# Component health check
print("\n" + "="*80)
print("🏥 COMPONENT HEALTH CHECK")
print("="*80)

print(f"\n✅ Components:")
print(f"   Model:  {hasattr(predictor, 'ml_model')}")
print(f"   Scaler: {hasattr(predictor, 'scaler')}")
print(f"   SHAP:   {predictor.shap_explainer is not None}")
print(f"   Features: {len(predictor.feature_names)}")

print(f"\n⚙️  Configuration:")
print(f"   ML Weight:       {predictor.DEFAULT_ML_WEIGHT}")
print(f"   Semantic Weight: {predictor.DEFAULT_SEMANTIC_WEIGHT}")

print("\n" + "="*80)
print("✅ TEST COMPLETE!")
print("="*80)
