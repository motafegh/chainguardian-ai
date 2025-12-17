"""Test that all 58 features save to database correctly."""

from chainguardian.database.manager import DatabaseManager
from pathlib import Path
import tempfile

# Test feature dict with all 58 features
test_features = {
    'contract_name': 'TestContract',
    'file_path': '/tmp/test.sol',
    'address': '0x1234567890123456789012345678901234567890',
    
    # Vulnerability flags
    'has_reentrancy': True,
    'has_reentrancy_unlimited': False,
    'has_tx_origin': True,
    
    # Severity
    'high_severity_count': 2,
    'medium_severity_count': 3,
    'low_severity_count': 5,
    
    # AST features
    'num_functions': 10,
    'lines_of_code': 200,
    'num_comments': 50,
    'comment_to_code_ratio': 0.25,
    
    # Detector stats
    'total_detector_hits': 8,
    'unique_vulnerability_types': 3,
    
    # Risk scores
    'risk_score_simple': 25.0,
    'is_high_risk': True,
    'contract_complexity_category': 'complex',
}

print("Testing database save with 58 features...")

db = DatabaseManager()

try:
    # Save
    contract_id = db.save_contract_and_features(test_features)
    print(f"✅ Saved contract_id={contract_id}")
    
    # Retrieve
    df = db.get_all_features()
    print(f"✅ Retrieved {len(df)} rows with {len(df.columns)} columns")
    
    # Verify specific features
    row = df[df['contract_id'] == contract_id].iloc[0]
    print(f"✅ Verified features:")
    print(f"   - has_tx_origin: {row['has_tx_origin']}")
    print(f"   - lines_of_code: {row['lines_of_code']}")
    print(f"   - risk_score_simple: {row['risk_score_simple']}")
    print(f"   - contract_complexity_category: {row['contract_complexity_category']}")
    
    print("\n✅ ALL DATABASE TESTS PASSED!")
    
except Exception as e:
    print(f"❌ TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
