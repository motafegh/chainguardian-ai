"""Test AST feature extraction"""

from pathlib import Path
from ast_analyzer import ASTFeatureExtractor

def test_ast_features():
    contract_path = Path("blockchain/contracts/examples/VulnerableBank.sol")
    
    extractor = ASTFeatureExtractor(contract_path)
    features = extractor.extract_features("VulnerableBank")
    
    print("\n🎯 AST Features:")
    for key, value in features.items():
        print(f"  {key}: {value}")
    
    # Validation: VulnerableBank has 6 functions
    assert features['num_functions'] > 0, "Should have functions!"
    assert features['num_external_calls'] > 0, "Should have external calls!"
    
    print("\n✅ AST extraction works!")

if __name__ == "__main__":
    test_ast_features()
