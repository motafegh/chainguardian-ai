"""
Adversarial Testing: Test TWO-STAGE model on crafted contracts
"""

import os
import sys
import pandas as pd
import numpy as np
import joblib
import json
import tempfile
import shutil
import uuid
import re
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from chainguardian.feature_extraction.pipeline import FeaturePipeline


def extract_contract_names(source_code: str) -> list:
    """Extract all contract names from Solidity source code."""
    pattern = r'(?:abstract\s+)?(?:contract|library|interface)\s+([A-Z][a-zA-Z0-9_]*)'
    return re.findall(pattern, source_code)


print("\n" + "="*70)
print("🧪 TWO-STAGE ADVERSARIAL TESTING")
print("="*70)

# Test contracts directory
test_dir = Path('test_contracts')

if not test_dir.exists():
    print(f"\n❌ Test contracts directory not found!")
    sys.exit(1)

# Get test contracts
test_files = sorted(test_dir.glob('*.sol'))
print(f"\nFound {len(test_files)} test contracts")

# Expected results
expected_results = {
    '01_super_simple_safe.sol': {'risk': 'LOW', 'range': (0, 30)},
    '02_obvious_reentrancy.sol': {'risk': 'HIGH', 'range': (70, 100)},
    '03_complex_but_safe.sol': {'risk': 'MEDIUM', 'range': (30, 60)},
    '04_simple_but_vulnerable.sol': {'risk': 'HIGH', 'range': (60, 100)},
    '05_timestamp_manipulation.sol': {'risk': 'MEDIUM-HIGH', 'range': (50, 80)},
    '06_unchecked_external_call.sol': {'risk': 'HIGH', 'range': (60, 100)},
    '07_integer_overflow_old.sol': {'risk': 'HIGH', 'range': (60, 100)},
    '08_safe_with_checks.sol': {'risk': 'LOW', 'range': (0, 40)},
    '09_delegatecall_danger.sol': {'risk': 'HIGH', 'range': (70, 100)},
    '10_tx_origin_auth.sol': {'risk': 'MEDIUM-HIGH', 'range': (50, 80)},
    '11_hidden_reentrancy.sol': {'risk': 'HIGH', 'range': (70, 100)},
    '12_false_positive_trap.sol': {'risk': 'LOW-MEDIUM', 'range': (20, 50)},
    '13_modern_defi_safe.sol': {'risk': 'LOW-MEDIUM', 'range': (20, 50)},
    '14_assembly_safe.sol': {'risk': 'MEDIUM', 'range': (30, 60)},
    '15_gas_griefing.sol': {'risk': 'MEDIUM-HIGH', 'range': (50, 70)},
    '16_front_running_vulnerable.sol': {'risk': 'LOW-MEDIUM', 'range': (20, 50)},
    '17_logic_error.sol': {'risk': 'LOW-MEDIUM', 'range': (20, 50)},
    '18_oracle_manipulation.sol': {'risk': 'HIGH', 'range': (70, 100)},
    '19_flash_loan_attack_vector.sol': {'risk': 'MEDIUM-HIGH', 'range': (50, 80)},
    '20_upgradeable_safe.sol': {'risk': 'LOW-MEDIUM', 'range': (30, 50)},
    '21_timelock_missing.sol': {'risk': 'MEDIUM', 'range': (40, 60)},
    '22_empty_contract.sol': {'risk': 'VERY LOW', 'range': (0, 15)},
    '23_only_events.sol': {'risk': 'VERY LOW', 'range': (0, 15)},
    '24_intentional_honeypot.sol': {'risk': 'HIGH', 'range': (80, 100)},
    '25_gas_optimization_extreme.sol': {'risk': 'LOW-MEDIUM', 'range': (20, 50)},
}

# Load TWO-STAGE models
print("\n" + "="*70)
print("📦 LOADING TWO-STAGE MODELS")
print("="*70)

models_dir = Path('models')

# Load Stage 1: Code-based vulnerability detector
stage1_model = joblib.load(models_dir / 'stage1_code_detector.pkl')
print("✅ Stage 1 (Code Detector) loaded")

# Load Stage 2: Risk scorer
stage2_model = joblib.load(models_dir / 'stage2_risk_scorer.pkl')
print("✅ Stage 2 (Risk Scorer) loaded")

# Load scaler and metadata
scaler = joblib.load(models_dir / 'feature_scaler.pkl')
metadata = joblib.load(models_dir / 'two_stage_metadata.pkl')

code_features = metadata['code_features']
detector_features = metadata['detector_features']

print(f"✅ Feature groups loaded ({len(code_features)} code + {len(detector_features)} detector)")

# Extract features and predict
print("\n" + "="*70)
print("🔬 EXTRACTING FEATURES & PREDICTING")
print("="*70)

results = []

for test_file in test_files:
    print(f"\n📄 {test_file.name}")
    
    try:
        # Extract actual contract name from source
        source_code = test_file.read_text(encoding='utf-8')
        contract_names = extract_contract_names(source_code)
        
        if not contract_names:
            print(f"   ⚠️  No contract definition found - skipping")
            continue
        
        actual_contract_name = contract_names[0]
        print(f"   📝 Contract name: {actual_contract_name}")
        
        # Create UNIQUE address
        unique_address = f"0x{uuid.uuid4().hex[:40]}"
        
        # Create temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_contract = Path(temp_dir) / test_file.name
            shutil.copy(test_file, temp_contract)
            
            # Initialize pipeline
            pipeline = FeaturePipeline()
            
            metadata_dict = {
                'address': unique_address,
                'data_source': 'adversarial_test',
                'compiler_version': None
            }
            
            # Analyze contract
            success = pipeline.analyze_contract(
                contract_path=temp_contract,
                contract_name=actual_contract_name,
                metadata=metadata_dict
            )
            
            if not success:
                print(f"   ❌ Extraction failed")
                continue
            
            # Get features
            df_features = pipeline.to_dataframe()
            
            if len(df_features) == 0:
                print(f"   ❌ No features extracted")
                continue
            
            features_row = df_features.iloc[-1]
            
            # ================================================================
            # STAGE 1: CODE-BASED VULNERABILITY DETECTION
            # ================================================================
            
            # Build Stage 1 feature vector
            X_code = []
            for feat_name in code_features:
                if feat_name in features_row.index:
                    val = features_row[feat_name]
                    if isinstance(val, bool):
                        val = int(val)
                    if pd.isna(val):
                        val = 0
                    X_code.append(val)
                else:
                    X_code.append(0)
            
            X_code = pd.DataFrame([X_code], columns=code_features)
            
            # Scale features
            X_code_scaled = scaler.transform(X_code)
            
            # Predict vulnerability probability
            vuln_proba = stage1_model.predict_proba(X_code_scaled)[0, 1]
            vuln_pred = stage1_model.predict(X_code_scaled)[0]
            
            # ================================================================
            # STAGE 2: RISK SCORING
            # ================================================================
            
            # Build Stage 2 feature vector
            X_detector = []
            for feat_name in detector_features:
                if feat_name in features_row.index:
                    val = features_row[feat_name]
                    if isinstance(val, bool):
                        val = int(val)
                    if pd.isna(val):
                        val = 0
                    X_detector.append(val)
                else:
                    X_detector.append(0)
            
            X_detector = pd.DataFrame([X_detector], columns=detector_features)
            
            # Add Stage 1 outputs
            X_detector['code_vulnerability_prob'] = vuln_proba
            X_detector['code_vulnerability_confidence'] = abs(vuln_proba - 0.5) * 2
            
            # Predict risk score
            risk_score = stage2_model.predict(X_detector)[0]
            risk_score = np.clip(risk_score, 10, 100)
            
            # Check against expected
            expected = expected_results.get(test_file.name, {'risk': 'UNKNOWN', 'range': (0, 100)})
            expected_min, expected_max = expected['range']
            correct = expected_min <= risk_score <= expected_max
            
            print(f"   Stage 1: {vuln_proba:.3f} vuln prob | Stage 2: {risk_score:.1f} risk")
            print(f"   Expected: {expected['risk']} | {'✅' if correct else '❌'}")
            
            results.append({
                'contract': test_file.name,
                'contract_name': actual_contract_name,
                'vulnerability_probability': vuln_proba,
                'vulnerability_predicted': int(vuln_pred),
                'risk_score': risk_score,
                'expected_risk': expected['risk'],
                'expected_range': f"{expected_min}-{expected_max}",
                'correct': correct
            })
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

# Summary
print("\n" + "="*70)
print("📊 RESULTS")
print("="*70)

df_results = pd.DataFrame(results)

if len(df_results) > 0:
    df_results.to_csv('reports/two_stage_adversarial_results.csv', index=False)
    
    passed = df_results['correct'].sum()
    total = len(df_results)
    accuracy = (passed / total * 100) if total > 0 else 0
    
    print(f"\n🎯 ACCURACY: {passed}/{total} ({accuracy:.1f}%)")
    print(f"\n{'Contract':45s} {'Vuln%':>7s} {'Risk':>6s} {'Expected':>12s} {'Result':>8s}")
    print("-" * 85)
    
    for _, row in df_results.iterrows():
        contract = row['contract'][:43]
        vuln_prob = f"{row['vulnerability_probability']*100:.1f}%"
        risk = f"{row['risk_score']:.1f}"
        expected = row['expected_risk'][:10]
        result = '✅' if row['correct'] else '❌'
        print(f"{contract:45s} {vuln_prob:>7s} {risk:>6s} {expected:>12s} {result:>8s}")
    
    # Category analysis
    print(f"\n📊 CATEGORY BREAKDOWN:")
    
    print(f"\n1️⃣  Obvious Vulnerabilities:")
    for contract in ['02_obvious_reentrancy.sol', '04_simple_but_vulnerable.sol']:
        row = df_results[df_results['contract'] == contract]
        if len(row) > 0:
            print(f"   {row['contract'].values[0]:40s} Prob:{row['vulnerability_probability'].values[0]:.3f} Risk:{row['risk_score'].values[0]:5.1f}")
    
    print(f"\n2️⃣  Obviously Safe:")
    for contract in ['01_super_simple_safe.sol', '22_empty_contract.sol']:
        row = df_results[df_results['contract'] == contract]
        if len(row) > 0:
            print(f"   {row['contract'].values[0]:40s} Prob:{row['vulnerability_probability'].values[0]:.3f} Risk:{row['risk_score'].values[0]:5.1f}")
    
    # Stage 1 analysis
    print(f"\n📊 STAGE 1 PERFORMANCE (Vulnerability Detection):")
    vuln_contracts = df_results[df_results['vulnerability_predicted'] == 1]
    safe_contracts = df_results[df_results['vulnerability_predicted'] == 0]
    print(f"   Predicted vulnerable: {len(vuln_contracts)}")
    print(f"   Predicted safe: {len(safe_contracts)}")
    print(f"   Mean prob (predicted vuln): {df_results[df_results['vulnerability_predicted']==1]['vulnerability_probability'].mean():.3f}")
    print(f"   Mean prob (predicted safe): {df_results[df_results['vulnerability_predicted']==0]['vulnerability_probability'].mean():.3f}")
    
    print(f"\n✅ Saved: reports/two_stage_adversarial_results.csv")

else:
    print("\n❌ No results!")

print("="*70 + "\n")
