# scripts/test_integrated_pipeline.py
"""Test that pipeline now includes graph features."""
from pathlib import Path
from chainguardian.feature_extraction.pipeline import FeaturePipeline
import logging

logging.basicConfig(level=logging.INFO)

# Test on one contract
pipeline = FeaturePipeline()

# Pick a simple contract from your data
test_contract = Path("data/smartbugs_curated/dataset/access_control/arbitrary_location_write_simple.sol")
contract_name = "Wallet"  # Adjust to actual contract name

features = pipeline.analyze_contract(test_contract, contract_name)

print("\n" + "="*70)
print("INTEGRATION TEST RESULTS")
print("="*70)
print(f"Total features: {len(features)}")
print(f"Expected: 104 features (79 old + 25 new)")

# Check graph features are present
graph_feature_count = sum(1 for k in features.keys() 
                         if k.startswith(('cfg_', 'cg_', 'dfg_')))
print(f"Graph features found: {graph_feature_count}/25")

if graph_feature_count == 25:
    print("✅ Integration successful!")
    print("\nSample graph features:")
    print(f"  cfg_num_cycles: {features['cfg_num_cycles']}")
    print(f"  cg_num_external_calls: {features['cg_num_external_calls']}")
    print(f"  dfg_num_tainted_flows: {features['dfg_num_tainted_flows']}")
else:
    print("❌ Integration incomplete")

print("="*70)
