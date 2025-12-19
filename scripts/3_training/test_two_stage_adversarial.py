"""
Two-Stage Adversarial Testing
"""

import sys
import pandas as pd
import numpy as np
import joblib
import tempfile
import shutil
import uuid
import re
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from chainguardian.feature_extraction.pipeline import FeaturePipeline


def extract_contract_names(source_code: str) -> list:
    """Extract contract names from Solidity source."""
    pattern = r'(?:abstract\s+)?(?:contract|library|interface)\s+([A-Z][a-zA-Z0-9_]*)'
    return re.findall(pattern, source_code)


# Expected results
expected = {
    '01_super_simple_safe.sol': (0, 30),
    '02_obvious_reentrancy.sol': (70, 100),
    '03_complex_but_safe.sol': (30, 60),
    '04_simple_but_vulnerable.sol': (60, 100),
    '05_timestamp_manipulation.sol': (50, 80),
    '06_unchecked_external_call.sol': (60, 100),
    '07_integer_overflow_old.sol': (60, 100),
    '08_safe_with_checks.sol': (0, 40),
    '09_delegatecall_danger.sol': (70, 100),
    '10_tx_origin_auth.sol': (50, 80),
    '11_hidden_reentrancy.sol': (70, 100),
    '12_false_positive_trap.sol': (20, 50),
    '13_modern_defi_safe.sol': (20, 50),
    '14_assembly_safe.sol': (30, 60),
    '15_gas_griefing.sol': (50, 70),
    '16_front_running_vulnerable.sol': (20, 50),
    '17_logic_error.sol': (20, 50),
    '18_oracle_manipulation.sol': (70, 100),
    '19_flash_loan_attack_vector.sol': (50, 80),
    '20_upgradeable_safe.sol': (30, 50),
    '21_timelock_missing.sol': (40, 60),
    '22_empty_contract.sol': (0, 15),
    '23_only_events.sol': (0, 15),
    '24_intentional_honeypot.sol': (80, 100),
    '25_gas_optimization_extreme.sol': (20, 50),
}

print("\n" + "="*70)
print("🧪 TWO-STAGE ADVERSARIAL TESTING")
print("="*70)

# Find test contracts
test_dir = Path('test_contracts')
test_files = sorted(test_dir.glob('*.sol'))

print(f"\n📂 Test directory: {test_dir.absolute()}")
print(f"📝 Found {len(test_files)} contracts\n")

if len(test_files) == 0:
    print("❌ No .sol files found in test_contracts/")
    sys.exit(1)

# Load models
print("📦 Loading models...")
stage1 = joblib.load('models/stage1_code_detector.pkl')
stage2 = joblib.load('models/stage2_risk_scorer.pkl')
scaler = joblib.load('models/feature_scaler.pkl')
metadata = joblib.load('models/two_stage_metadata.pkl')

code_features = metadata['code_features']
detector_features = metadata['detector_features']

print(f"✅ Loaded: Stage 1 ({len(code_features)} features) + Stage 2 ({len(detector_features)} features)\n")

# Test each contract
results = []

for test_file in test_files:
    print(f"📄 {test_file.name}")
    
    try:
        source = test_file.read_text()
        names = extract_contract_names(source)
        
        if not names:
            print(f"   ⚠️  No contract found\n")
            continue
        
        contract_name = names[0]
        print(f"   Contract: {contract_name}")
        
        # Create temp copy
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_file = Path(tmpdir) / test_file.name
            shutil.copy(test_file, tmp_file)
            
            # Extract features
            pipeline = FeaturePipeline()
            success = pipeline.analyze_contract(
                tmp_file,
                contract_name,
                {'address': f"0x{uuid.uuid4().hex[:40]}", 'data_source': 'adversarial'}
            )
            
            if not success:
                print(f"   ❌ Extraction failed\n")
                continue
            
            df = pipeline.to_dataframe()
            if len(df) == 0:
                print(f"   ❌ No features\n")
                continue
            
            row = df.iloc[-1]
            
            # Build feature vectors
            X_code = []
            for f in code_features:
                val = row.get(f, 0)
                if isinstance(val, bool):
                    val = int(val)
                if pd.isna(val):
                    val = 0
                X_code.append(val)
            
            X_code = pd.DataFrame([X_code], columns=code_features)
            X_code_scaled = scaler.transform(X_code)
            
            # Stage 1: Vulnerability probability
            vuln_prob = stage1.predict_proba(X_code_scaled)[0, 1]
            
            # Stage 2: Build features
            X_det = []
            for f in detector_features:
                val = row.get(f, 0)
                if isinstance(val, bool):
                    val = int(val)
                if pd.isna(val):
                    val = 0
                X_det.append(val)
            
            X_det = pd.DataFrame([X_det], columns=detector_features)
            X_det['code_vulnerability_prob'] = vuln_prob
            X_det['code_vulnerability_confidence'] = abs(vuln_prob - 0.5) * 2
            
            # Stage 2: Risk score
            risk = stage2.predict(X_det)[0]
            risk = np.clip(risk, 10, 100)
            
            # Check expected
            exp_min, exp_max = expected.get(test_file.name, (0, 100))
            correct = exp_min <= risk <= exp_max
            
            print(f"   Stage 1: {vuln_prob:.3f} | Stage 2: {risk:.1f}")
            print(f"   Expected: {exp_min}-{exp_max} | {'✅' if correct else '❌'}\n")
            
            results.append({
                'contract': test_file.name,
                'vuln_prob': vuln_prob,
                'risk_score': risk,
                'expected_min': exp_min,
                'expected_max': exp_max,
                'correct': correct
            })
    
    except Exception as e:
        print(f"   ❌ Error: {e}\n")

# Summary
print("="*70)
print("📊 RESULTS")
print("="*70)

if len(results) > 0:
    df_res = pd.DataFrame(results)
    df_res.to_csv('reports/two_stage_adversarial_results.csv', index=False)
    
    passed = df_res['correct'].sum()
    total = len(df_res)
    acc = passed / total * 100
    
    print(f"\n🎯 ACCURACY: {passed}/{total} ({acc:.1f}%)\n")
    
    print(f"{'Contract':45s} {'Vuln':>7s} {'Risk':>6s} {'Expected':>12s} {'Result':>6s}")
    print("-" * 85)
    
    for _, r in df_res.iterrows():
        print(f"{r['contract']:45s} {r['vuln_prob']*100:>6.1f}% {r['risk_score']:>6.1f} {r['expected_min']:>5.0f}-{r['expected_max']:<5.0f} {'✅' if r['correct'] else '❌':>6s}")
    
    print(f"\n✅ Saved: reports/two_stage_adversarial_results.csv")
else:
    print("\n❌ No results")

print("="*70)
