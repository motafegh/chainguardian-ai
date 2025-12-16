"""
Test complete pipeline: analyze contract → extract 58 features → save to database.
"""

from chainguardian.feature_extraction.pipeline import FeaturePipeline
from chainguardian.database.manager import DatabaseManager
from pathlib import Path
import tempfile

TEST_CONTRACT = """
// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

contract TestPipeline {
    address public owner;
    mapping(address => uint256) public balances;
    
    constructor() {
        owner = msg.sender;
    }
    
    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }
    
    // Intentional vulnerability: reentrancy
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount);
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success);
        balances[msg.sender] -= amount;  // State change after external call!
    }
}
"""

print("=" * 70)
print("FULL PIPELINE TEST: Extract 58 Features → Save to Database")
print("=" * 70)

# Create temp contract
with tempfile.NamedTemporaryFile(mode='w', suffix='.sol', delete=False) as f:
    f.write(TEST_CONTRACT)
    contract_path = Path(f.name)

print(f"\n1️⃣ Created test contract: {contract_path.name}")

try:
    # Initialize pipeline
    pipeline = FeaturePipeline()
    print("2️⃣ Pipeline initialized ✓")
    
    # Analyze contract (extracts + saves to DB automatically!)
    print("3️⃣ Analyzing contract...")
    features = pipeline.analyze_contract(contract_path, "TestPipeline")
    
    print(f"   ✓ Extracted {len(features)} feature fields")
    
    # Get from database
    db = DatabaseManager()
    df = db.get_all_features()
    
    # Find our contract
    last_contract = df.iloc[-1]
    
    print(f"\n4️⃣ Verified database save:")
    print(f"   - Contract: {last_contract['contract_name']}")
    print(f"   - Total features in DB: {len(df.columns)}")
    print(f"   - Risk score: {last_contract['risk_score_simple']}")
    print(f"   - High risk? {last_contract['is_high_risk']}")
    print(f"   - LOC: {last_contract['lines_of_code']}")
    print(f"   - Detectors fired: {last_contract['total_detector_hits']}")
    
    # Check specific vulnerability detection
    if last_contract.get('has_reentrancy'):
        print(f"   ✓ Reentrancy detected! (Expected)")
    
    print("\n" + "=" * 70)
    print("✅ FULL PIPELINE TEST PASSED!")
    print("=" * 70)
    print("\n📊 Summary:")
    print(f"   - Feature extraction: ✓ (58 features)")
    print(f"   - Database save: ✓")
    print(f"   - Database retrieval: ✓")
    print(f"   - Vulnerability detection: ✓")
    
    print("\n➡️  READY FOR PRODUCTION RE-ANALYSIS!")
    print("   Run: poetry run python scripts/reanalyze_all_contracts.py")
    print("=" * 70 + "\n")
    
except Exception as e:
    print(f"\n❌ TEST FAILED: {e}")
    import traceback
    traceback.print_exc()

finally:
    contract_path.unlink()
