"""Test Slither JSON parsing"""

from pathlib import Path
from contract_analyzer import SlitherParser

def test_vulnerable_bank():
    json_path = Path("slither_output.json")
    
    if not json_path.exists():
        print("❌ Run Slither first: poetry run slither blockchain/contracts/examples/VulnerableBank.sol --json slither_output.json")
        return
    
    parser = SlitherParser(json_path)
    features = parser.extract_features("VulnerableBank")
    
    print("\n🎯 Extracted Features:")
    print(f"  Reentrancy: {features.has_reentrancy}")
    print(f"  Access Control Issues: {features.has_access_control_issues}")
    print(f"  Timestamp Dependency: {features.has_timestamp_dependency}")
    print(f"  High Severity: {features.high_severity_count}")
    print(f"  Medium Severity: {features.medium_severity_count}")
    
    # Validation: We KNOW VulnerableBank has these issues
    assert features.has_reentrancy, "Should detect reentrancy!"
    assert features.has_access_control_issues, "Should detect access control!"
    
    print("\n✅ Parser works correctly!")

if __name__ == "__main__":
    test_vulnerable_bank()
