"""Test complete feature extraction pipeline"""

from pathlib import Path
from pipeline import FeaturePipeline

def test_unified_pipeline():
    print("🚀 Testing Unified Feature Pipeline\n")
    
    # Initialize pipeline
    pipeline = FeaturePipeline()
    
    # Analyze VulnerableBank
    features = pipeline.analyze_contract(
        contract_path=Path("blockchain/contracts/examples/VulnerableBank.sol"),
        contract_name="VulnerableBank",
        json_output_path=Path("slither_output.json")
    )
    
    # Display complete feature vector
    print("🎯 Complete Feature Vector:")
    print("-" * 50)
    for key, value in features.items():
        print(f"  {key:30} = {value}")
    print("-" * 50)
    
    # Convert to DataFrame
    df = pipeline.to_dataframe()
    print(f"\n📊 DataFrame shape: {df.shape}")
    print(f"   Columns: {list(df.columns)}")
    
    # Save as CSV (ready for ML training)
    output_path = Path("data/vulnerable_bank_features.csv")
    output_path.parent.mkdir(exist_ok=True)
    pipeline.save_dataset(output_path)
    
    print(f"\n✅ Pipeline complete! Dataset saved to {output_path}")
    print(f"   This is the format your ML models will consume.")

if __name__ == "__main__":
    test_unified_pipeline()
