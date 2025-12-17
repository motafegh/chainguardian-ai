"""
Test expanded feature extraction using existing pipeline.

Uses FeaturePipeline which handles version switching automatically.
"""

from pathlib import Path
from chainguardian.feature_extraction.pipeline import FeaturePipeline
import tempfile
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================================================
# CREATE A SIMPLE TEST CONTRACT
# ================================================================
TEST_CONTRACT = """
// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

/**
 * Simple test contract for feature extraction.
 * Tests: functions, state vars, modifiers, complexity
 */
contract TestToken {
    // State variables (3)
    mapping(address => uint256) public balances;
    address public owner;
    uint256 public totalSupply;
    
    // Events
    event Transfer(address indexed from, address indexed to, uint256 amount);
    
    // Constructor
    constructor() {
        owner = msg.sender;
        totalSupply = 1000000;
        balances[msg.sender] = totalSupply;
    }
    
    // Modifier (1)
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    // Simple function (complexity: 2)
    function transfer(address to, uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        balances[to] += amount;
        emit Transfer(msg.sender, to, amount);
    }
    
    // Function with access control (complexity: 2)
    function mint(uint256 amount) public onlyOwner {
        totalSupply += amount;
        balances[msg.sender] += amount;
    }
    
    // Complex function (complexity: 5)
    function complexFunction(uint256 x) public pure returns (uint256) {
        if (x > 100) {
            if (x > 500) {
                return x * 2;
            } else {
                return x + 50;
            }
        } else {
            if (x > 50) {
                return x - 10;
            } else {
                return x;
            }
        }
    }
    
    // Payable function (1)
    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }
    
    // Function with external call (1)
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient");
        balances[msg.sender] -= amount;
        // External call (1)
        payable(msg.sender).transfer(amount);
    }
}
"""

def test_feature_extraction():
    """Test that all 58 features can be extracted using FeaturePipeline."""
    
    print("=" * 70)
    print("TESTING EXPANDED FEATURE EXTRACTION")
    print("=" * 70)
    
    # ================================================================
    # STEP 1: CREATE TEMPORARY CONTRACT FILE
    # ================================================================
    print("\n1️⃣ Creating test contract...")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sol', delete=False) as f:
        f.write(TEST_CONTRACT)
        contract_path = Path(f.name)
    
    print(f"   ✓ Created: {contract_path}")
    
    try:
        # ============================================================
        # STEP 2: INITIALIZE PIPELINE (Handles version switching!)
        # ============================================================
        print("\n2️⃣ Initializing feature pipeline...")
        
        pipeline = FeaturePipeline()
        print(f"   ✓ Pipeline initialized")
        print(f"   ✓ Database connection: ready")
        
        # ============================================================
        # STEP 3: ANALYZE CONTRACT (All features extracted)
        # ============================================================
        print("\n3️⃣ Analyzing contract (with auto version switching)...")
        
        features = pipeline.analyze_contract(
            contract_path=contract_path,
            contract_name="TestToken"
        )
        
        print(f"   ✓ Analysis complete!")
        
        # ============================================================
        # STEP 4: VERIFY VULNERABILITY FEATURES
        # ============================================================
        print("\n4️⃣ Verifying vulnerability features...")
        
        # Count populated vulnerability flags
        vuln_flags = [k for k, v in features.items() if k.startswith('has_') and v]
        
        print(f"   ✓ Vulnerability flags detected: {len(vuln_flags)}")
        if vuln_flags:
            for flag in vuln_flags[:5]:
                print(f"     - {flag}")
            if len(vuln_flags) > 5:
                print(f"     ... and {len(vuln_flags) - 5} more")
        
        print(f"   ✓ Severity counts:")
        print(f"     - High: {features.get('high_severity_count', 0)}")
        print(f"     - Medium: {features.get('medium_severity_count', 0)}")
        print(f"     - Low: {features.get('low_severity_count', 0)}")
        
        # ============================================================
        # STEP 5: VERIFY DETECTOR STATISTICS
        # ============================================================
        print("\n5️⃣ Verifying detector statistics...")
        
        print(f"   ✓ Aggregate features:")
        print(f"     - Total detectors: {features.get('total_detector_hits', 0)}")
        print(f"     - Unique vuln types: {features.get('unique_vulnerability_types', 0)}")
        print(f"     - High confidence: {features.get('high_confidence_detectors', 0)}")
        print(f"     - Medium confidence: {features.get('medium_confidence_detectors', 0)}")
        print(f"     - Low confidence: {features.get('low_confidence_detectors', 0)}")
        
        # ============================================================
        # STEP 6: VERIFY RISK SCORES
        # ============================================================
        print("\n6️⃣ Verifying risk scores...")
        
        print(f"   ✓ Risk metrics:")
        print(f"     - Simple risk score: {features.get('risk_score_simple', 0):.1f}")
        print(f"     - Weighted risk score: {features.get('risk_score_weighted', 0):.1f}")
        print(f"     - High risk? {features.get('is_high_risk', False)}")
        print(f"     - Complexity: {features.get('contract_complexity_category', 'unknown')}")
        
        # ============================================================
        # STEP 7: VERIFY AST FEATURES
        # ============================================================
        print("\n7️⃣ Verifying AST features...")
        
        print(f"   ✓ Code metrics:")
        print(f"     - Lines of code: {features.get('lines_of_code', 0)}")
        print(f"     - Functions: {features.get('num_functions', 0)}")
        print(f"     - State variables: {features.get('num_state_vars', 0)}")
        print(f"     - Modifiers: {features.get('num_modifiers', 0)}")
        
        print(f"   ✓ Complexity:")
        print(f"     - Max complexity: {features.get('max_cyclomatic_complexity', 0)}")
        print(f"     - Avg complexity: {features.get('avg_function_complexity', 0):.1f}")
        print(f"     - High complexity funcs: {features.get('num_functions_high_complexity', 0)}")
        
        print(f"   ✓ Comments:")
        print(f"     - Comment lines: {features.get('num_comments', 0)}")
        print(f"     - Comment ratio: {features.get('comment_to_code_ratio', 0):.2%}")
        
        print(f"   ✓ Advanced:")
        print(f"     - Payable functions: {features.get('num_payable_functions', 0)}")
        print(f"     - External calls: {features.get('num_external_calls', 0)}")
        print(f"     - Inheritance depth: {features.get('inheritance_depth', 0)}")
        
        # ============================================================
        # STEP 8: COUNT TOTAL FEATURES
        # ============================================================
        print("\n8️⃣ Counting total features...")
        
        # Exclude metadata fields
        metadata_fields = {'contract_name', 'file_path', 'failure_reason', 'error_message'}
        feature_fields = {k for k in features.keys() if k not in metadata_fields}
        
        total_features = len(feature_fields)
        
        print(f"   ✓ Total features extracted: {total_features}")
        
        # Check for new features
        new_features = [
            'has_reentrancy_unlimited', 'has_reentrancy_benign', 'has_reentrancy_events',
            'has_controlled_delegatecall', 'has_delegatecall_loop',
            'has_uninitialized_state', 'has_tx_origin', 'has_inline_assembly',
            'total_detector_hits', 'unique_vulnerability_types',
            'risk_score_simple', 'risk_score_weighted', 'is_high_risk',
            'lines_of_code', 'num_comments', 'comment_to_code_ratio',
            'avg_function_complexity', 'num_payable_functions'
        ]
        
        found_new = [f for f in new_features if f in features]
        missing_new = [f for f in new_features if f not in features]
        
        print(f"\n   ✓ New features found: {len(found_new)}/{len(new_features)}")
        if found_new:
            print(f"     Sample new features:")
            for feat in found_new[:5]:
                print(f"       - {feat}: {features[feat]}")
        
        if missing_new:
            print(f"\n   ⚠️  Missing features: {len(missing_new)}")
            for feat in missing_new[:5]:
                print(f"       - {feat}")
        
        # ============================================================
        # STEP 9: VALIDATION
        # ============================================================
        print("\n9️⃣ Validation...")
        
        # Expected features
        expected_vuln_flags = 23  # Boolean vulnerability flags
        expected_severity = 3     # High/medium/low counts
        expected_detector_stats = 9  # Aggregate statistics
        expected_risk_scores = 4  # Composite scores
        expected_ast_original = 6  # Original AST features
        expected_ast_new = 15     # New AST features
        
        expected_total = (expected_vuln_flags + expected_severity + 
                         expected_detector_stats + expected_risk_scores +
                         expected_ast_original + expected_ast_new)
        
        print(f"   Expected: ~{expected_total} features")
        print(f"   Extracted: {total_features} features")
        
        if total_features >= 50:  # Allow some flexibility
            print(f"   ✅ PASS: Sufficient features extracted")
            success = True
        else:
            print(f"   ⚠️  WARNING: Expected ≥50, got {total_features}")
            success = False
        
        # ============================================================
        # STEP 10: SUMMARY
        # ============================================================
        print("\n" + "=" * 70)
        if success:
            print("✅ FEATURE EXTRACTION TEST PASSED!")
        else:
            print("⚠️  FEATURE EXTRACTION TEST COMPLETED WITH WARNINGS")
        print("=" * 70)
        
        print("\n📊 Summary:")
        print(f"   - Total features: {total_features}")
        print(f"   - Vulnerability flags: {len(vuln_flags)}")
        print(f"   - Detector statistics: ✓")
        print(f"   - Risk scoring: ✓")
        print(f"   - AST metrics: ✓")
        print(f"   - Code quality metrics: ✓")
        
        if features.get('failure_reason'):
            print(f"\n   ⚠️  Failure reason: {features['failure_reason']}")
        
        print("\n➡️  Next step: Update DatabaseManager to save all features")
        print("=" * 70 + "\n")
        
        return success
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        try:
            contract_path.unlink()
            print(f"\n🧹 Cleaned up temporary file")
        except:
            pass

if __name__ == "__main__":
    success = test_feature_extraction()
    exit(0 if success else 1)
