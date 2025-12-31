#!/usr/bin/env python3
"""
Test script for new tier-based feature extraction.

Tests all 4 tiers on a sample contract to verify correct implementation.
"""

import sys
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def test_tier_extraction():
    """Test all tier modules on a sample contract."""

    print("=" * 80)
    print("TESTING NEW TIER-BASED FEATURE EXTRACTION")
    print("=" * 80)

    # Import new modules
    try:
        from chainguardian.feature_extraction.pipeline import FeaturePipeline
        from slither import Slither
        from chainguardian.feature_extraction.utils import resolve_contract
        from chainguardian.feature_extraction.tier1_core import extract_tier1_features
        from chainguardian.feature_extraction.tier2_semantic_graph import extract_tier2_features
        from chainguardian.feature_extraction.tier3_advanced import extract_tier3_features
        from chainguardian.feature_extraction.tier4_detectors import extract_tier4_features

        print("✓ All imports successful\n")
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

    # Test contract
    contract_path = Path("test_contract_simple.sol")
    contract_name = "SimpleVulnerable"

    if not contract_path.exists():
        print(f"✗ Contract not found: {contract_path}")
        return False

    print(f"📄 Test Contract: {contract_path}")
    print(f"📝 Contract Name: {contract_name}\n")

    # Test 1: Use pipeline to compile (handles version switching)
    print("-" * 80)
    print("TEST 1: Pipeline Compilation with Auto Version Switching")
    print("-" * 80)
    try:
        # Use pipeline's compile method which handles version switching
        pipeline_test = FeaturePipeline(mode="comprehensive")
        slither = pipeline_test._compile_contract(contract_path)
        print(f"✓ Compilation successful")
        print(f"  Found {len(slither.contracts)} contracts in file\n")
    except Exception as e:
        print(f"✗ Compilation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 2: Contract Resolution
    print("-" * 80)
    print("TEST 2: Contract Resolution")
    print("-" * 80)
    try:
        contract = resolve_contract(slither, contract_name)
        if contract:
            print(f"✓ Contract resolved: {contract.name}")
            print(f"  Functions: {len(contract.functions)}")
            print(f"  State variables: {len(contract.state_variables)}\n")
        else:
            print(f"✗ Contract not found: {contract_name}")
            return False
    except Exception as e:
        print(f"✗ Resolution failed: {e}")
        return False

    # Run detectors once
    print("-" * 80)
    print("RUNNING SLITHER DETECTORS")
    print("-" * 80)
    try:
        detector_results = slither.run_detectors()
        print(f"✓ Detectors ran successfully")
        print(f"  Results: {len(detector_results)} detector outputs\n")
    except Exception as e:
        print(f"✗ Detector run failed: {e}")
        detector_results = []

    # Test 3: Tier 1 Extraction
    print("-" * 80)
    print("TEST 3: Tier 1 Extraction (Core Features)")
    print("-" * 80)
    try:
        tier1_features = extract_tier1_features(slither, contract, detector_results)
        print(f"✓ Tier 1 extraction successful")
        print(f"  Features extracted: {len(tier1_features)}")

        # Show sample features
        print("\n  Sample features:")
        sample_keys = [
            'has_reentrancy', 'high_severity_count', 'num_functions',
            'lines_of_code', 'security_risk_score'
        ]
        for key in sample_keys:
            if key in tier1_features:
                print(f"    {key}: {tier1_features[key]}")
        print()
    except Exception as e:
        print(f"✗ Tier 1 extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 4: Tier 2 Extraction
    print("-" * 80)
    print("TEST 4: Tier 2 Extraction (Semantic + Graph)")
    print("-" * 80)
    try:
        tier2_features = extract_tier2_features(contract)
        print(f"✓ Tier 2 extraction successful")
        print(f"  Features extracted: {len(tier2_features)}")

        # Show sample features
        print("\n  Sample features:")
        sample_keys = [
            'cei_violations', 'has_reentrancy_guard', 'cfg_num_cycles',
            'call_graph_depth', 'dataflow_num_tainted_flows'
        ]
        for key in sample_keys:
            if key in tier2_features:
                print(f"    {key}: {tier2_features[key]}")
        print()
    except Exception as e:
        print(f"✗ Tier 2 extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 5: Tier 3 Extraction
    print("-" * 80)
    print("TEST 5: Tier 3 Extraction (Advanced)")
    print("-" * 80)
    try:
        tier3_features = extract_tier3_features(slither, contract)
        print(f"✓ Tier 3 extraction successful")
        print(f"  Features extracted: {len(tier3_features)}")

        # Show sample features
        print("\n  Sample features:")
        sample_keys = [
            'ir_highlevelcall_count', 'ir_taint_sources', 'num_public_functions',
            'high_confidence_ratio', 'vulnerability_density'
        ]
        for key in sample_keys:
            if key in tier3_features:
                print(f"    {key}: {tier3_features[key]}")
        print()
    except Exception as e:
        print(f"✗ Tier 3 extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 6: Tier 4 Extraction
    print("-" * 80)
    print("TEST 6: Tier 4 Extraction (Individual Detectors)")
    print("-" * 80)
    try:
        tier4_features = extract_tier4_features(slither, contract, detector_results)
        print(f"✓ Tier 4 extraction successful")
        print(f"  Features extracted: {len(tier4_features)}")

        # Count how many detectors fired
        fired = sum(1 for v in tier4_features.values() if v)
        print(f"  Detectors fired: {fired}/{len(tier4_features)}")

        # Show fired detectors
        if fired > 0:
            print("\n  Fired detectors:")
            for key, value in tier4_features.items():
                if value:
                    print(f"    {key}: {value}")
        print()
    except Exception as e:
        print(f"✗ Tier 4 extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 7: Full Pipeline (Comprehensive Mode)
    print("-" * 80)
    print("TEST 7: Full Pipeline - Comprehensive Mode")
    print("-" * 80)
    try:
        pipeline = FeaturePipeline(mode="comprehensive")
        features = pipeline.analyze_contract(contract_path, contract_name)

        print(f"✓ Pipeline extraction successful")
        print(f"  Total features: {len(features)}")
        print(f"  Status: {features.get('extraction_status', 'unknown')}")
        print(f"  Mode: {features.get('extraction_mode', 'unknown')}")

        # Show risk assessment
        print("\n  Risk Assessment:")
        print(f"    Security Risk Score: {features.get('security_risk_score', 'N/A')}")
        print(f"    Is High Risk: {features.get('is_high_risk', 'N/A')}")
        print(f"    High Severity Count: {features.get('high_severity_count', 'N/A')}")
        print()
    except Exception as e:
        print(f"✗ Pipeline extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 8: Full Pipeline (Maximum Mode)
    print("-" * 80)
    print("TEST 8: Full Pipeline - Maximum Mode")
    print("-" * 80)
    try:
        pipeline_max = FeaturePipeline(mode="maximum")
        features_max = pipeline_max.analyze_contract(contract_path, contract_name)

        print(f"✓ Pipeline extraction successful")
        print(f"  Total features: {len(features_max)}")
        print(f"  Expected: ~226 features")

        # Compare with comprehensive mode
        comprehensive_count = len(features)
        maximum_count = len(features_max)
        diff = maximum_count - comprehensive_count
        print(f"\n  Feature count difference:")
        print(f"    Maximum mode: {maximum_count} features")
        print(f"    Comprehensive mode: {comprehensive_count} features")
        print(f"    Tier 4 contribution: +{diff} features")
        print()
    except Exception as e:
        print(f"✗ Pipeline extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print("✓ All tests passed!")
    print(f"\nFeature Counts:")
    print(f"  Tier 1 (Core): {len(tier1_features)} features")
    print(f"  Tier 2 (Semantic+Graph): {len(tier2_features)} features")
    print(f"  Tier 3 (Advanced): {len(tier3_features)} features")
    print(f"  Tier 4 (Detectors): {len(tier4_features)} features")
    print(f"\nMode Totals:")
    print(f"  Comprehensive (T1+T2+T3): {len(features)} features")
    print(f"  Maximum (T1+T2+T3+T4): {len(features_max)} features")
    print("\n✅ New tier-based extraction is working correctly!")
    print("=" * 80)

    return True


if __name__ == "__main__":
    success = test_tier_extraction()
    sys.exit(0 if success else 1)
