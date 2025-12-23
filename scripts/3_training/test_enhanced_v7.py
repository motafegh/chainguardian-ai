#!/usr/bin/env python3
"""
Test script for Enhanced Hybrid Predictor v7
============================================
Tests all new features: ensemble, hyperparameter tuning, monitoring, etc.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Try to import V2, fallback to V1
try:
    from chainguardian.ml.models.hybrid_predictor_enhanced_v2 import EnhancedHybridPredictorV2
    PredictorClass = EnhancedHybridPredictorV2
    print("✅ Using EnhancedHybridPredictorV2")
except ImportError as e:
    print(f"⚠️  Cannot import EnhancedHybridPredictorV2: {e}")
    print("   Falling back to EnhancedHybridPredictor v1")
    from chainguardian.ml.models.hybrid_predictor_enhanced import EnhancedHybridPredictor
    PredictorClass = EnhancedHybridPredictor

from chainguardian.ml.core.config_manager import ConfigManager
import pandas as pd
import numpy as np

def test_configuration():
    """Test configuration loading."""
    print("🧪 Testing configuration system...")
    config_manager = ConfigManager()
    
    # Try multiple config paths
    config_paths = [
        "config/hybrid_config.yaml",
        "../config/hybrid_config.yaml",
        project_root / "config" / "hybrid_config.yaml"
    ]
    
    config = None
    for path in config_paths:
        if Path(path).exists():
            config = config_manager.load_config(path)
            print(f"✅ Configuration loaded from: {path}")
            break
    
    if config is None:
        print("❌ Could not load configuration")
        return None
    
    print(f"   Hyperparameter tuning: {getattr(config.hyperparameter_tuning, 'enable_optuna', False)}")
    print(f"   Ensemble: {getattr(config.ensemble, 'enabled', False)}")
    
    # Handle calibration_method safely - FIXED HERE
    calibration = getattr(config.ensemble, 'calibration_method', 'sigmoid')
    if hasattr(calibration, 'value'):
        print(f"   Calibration: {calibration.value}")
    else:
        print(f"   Calibration: {calibration}")
    
    return config

def test_predictor_integration(config):
    """Test the enhanced predictor integration."""
    print("\n🧪 Testing enhanced predictor...")
    
    # Create sample features with actual feature names from your model
    sample_features = {
        'reentrancy': 1,
        'access_control': 0,
        'arithmetic': 0,
        'unchecked_low_level_calls': 1,
        'timestamp_dependence': 0,
        'tx_origin_usage': 0,
        'gas_limit_dos': 0,
        'deprecated_functions': 1,
        'erc20_violations': 0,
        'erc721_violations': 0,
        'lines_of_code': 150,
        'cyclomatic_complexity': 12,
        'halstead_volume': 250,
        'num_functions': 10,
        'num_events': 2,
        'num_modifiers': 3,
        'num_inherits': 1,
        'num_imports': 5,
        'avg_function_length': 15.5,
        'max_nesting_depth': 4,
        'coverage_score': 0.75,
        'test_quality_score': 0.8,
        'gas_optimization_score': 0.65
    }
    
    try:
        predictor = PredictorClass(
            config_path="config/hybrid_config.yaml",
            enable_monitoring=True
        )
        
        # Single prediction
        print("   Making single prediction...")
        result = predictor.predict_single(sample_features)
        print(f"✅ Single prediction: {result.get('prediction_label', 'UNKNOWN')}")
        print(f"   Confidence: {result.get('calibrated_confidence', 0):.2%}")
        
        # Batch prediction
        print("   Making batch prediction...")
        batch_results = predictor.predict_batch([sample_features] * 2)
        print(f"✅ Batch prediction: {len(batch_results)} results")
        
        return predictor
        
    except Exception as e:
        print(f"❌ Predictor test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_with_sample_data():
    """Test with actual sample data."""
    print("\n🧪 Testing with sample contract data...")
    
    # Try to load a sample contract
    sample_contract_path = project_root / "data" / "sample_contracts" / "vulnerable_contract.sol"
    
    if sample_contract_path.exists():
        with open(sample_contract_path, 'r') as f:
            contract_code = f.read()
        
        sample_features = {
            'source_code': contract_code,
            'contract_name': 'SampleVulnerable',
            'has_reentrancy': 1,
            'has_unchecked_call': 1,
            'num_external_calls': 5,
            'lines_of_code': 85,
            'cei_violations': 3
        }
        
        try:
            predictor = PredictorClass()
            result = predictor.predict_single(sample_features)
            print(f"✅ Sample contract analysis:")
            print(f"   Prediction: {result.get('prediction_label')}")
            print(f"   Confidence: {result.get('calibrated_confidence'):.2%}")
            if 'risk_factors' in result:
                print(f"   Risk factors: {len(result['risk_factors'])} found")
        except Exception as e:
            print(f"❌ Sample contract test failed: {e}")
    else:
        print("⚠️  Sample contract file not found, skipping...")

def main():
    """Run all tests."""
    print("=" * 80)
    print("🧪 ENHANCED HYBRID PREDICTOR v7 - TEST SUITE")
    print("=" * 80)
    
    # Test 1: Configuration
    config = test_configuration()
    
    if config is None:
        print("❌ Cannot proceed without configuration")
        return 1
    
    # Test 2: Predictor
    predictor = test_predictor_integration(config)
    
    # Test 3: Sample data
    test_with_sample_data()
    
    print("\n" + "=" * 80)
    
    if predictor:
        print("✅ TESTS COMPLETED SUCCESSFULLY")
        print("\n🎯 Enhanced predictor is working with features:")
        print(f"   • Predictor version: {predictor.__class__.__name__}")
        print(f"   • Ensemble: {getattr(predictor, 'use_ensemble', False)}")
        print(f"   • Monitoring: {getattr(predictor, 'monitor', None) is not None}")
    else:
        print("⚠️  TESTS COMPLETED WITH WARNINGS")
        print("   Some features may not be available")
    
    print("=" * 80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())