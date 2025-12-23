#!/usr/bin/env python3
"""
Test script for Enhanced Hybrid Predictor v7
============================================
Tests all new features: ensemble, hyperparameter tuning, monitoring, etc.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.chainguardian.ml.core.config_manager import ConfigManager
from src.chainguardian.ml.core.hyperparameter_tuner import HyperparameterTuner
from src.chainguardian.ml.models.hybrid_predictor_enhanced_v2 import EnhancedHybridPredictorV2
import pandas as pd
import numpy as np

def test_configuration():
    """Test configuration loading."""
    print("🧪 Testing configuration system...")
    config_manager = ConfigManager()
    config = config_manager.load_config("config/hybrid_config.yaml")
    
    print(f"✅ Configuration loaded:")
    print(f"   Hyperparameter tuning: {config.hyperparameter_tuning.enable_optuna}")
    print(f"   Ensemble: {config.ensemble.enabled}")
    print(f"   Calibration: {config.ensemble.calibration_method.value}")
    
    return config

def test_hyperparameter_tuning():
    """Test hyperparameter tuning with small dataset."""
    print("\n🧪 Testing hyperparameter tuning...")
    
    # Create synthetic data for testing
    X = np.random.randn(100, 50)
    y = np.random.randint(0, 2, 100)
    
    config = get_config()
    tuner = HyperparameterTuner(config, [f"feature_{i}" for i in range(50)])
    
    # Quick test with small number of trials
    results = tuner.optimize(X, y, n_trials=5)
    
    print(f"✅ Hyperparameter tuning completed:")
    print(f"   Best score: {results['best_score']:.4f}")
    print(f"   Best model: {results['best_params'].get('model_type')}")
    
    return tuner

def test_predictor_integration():
    """Test the enhanced predictor integration."""
    print("\n🧪 Testing enhanced predictor...")
    
    # Create sample features
    sample_features = {
        'has_reentrancy': 1,
        'has_unchecked_call': 0,
        'num_external_calls': 3,
        'lines_of_code': 150,
        'num_functions': 10,
        'cei_violations': 2,
        'cei_pattern_score': 0.6,
        'source_code': "contract Test { function withdraw() public {} }"
    }
    
    try:
        predictor = EnhancedHybridPredictorV2(
            config_path="config/hybrid_config.yaml",
            enable_monitoring=True
        )
        
        # Single prediction
        result = predictor.predict_single(sample_features)
        print(f"✅ Single prediction: {result['prediction_label']}")
        print(f"   Confidence: {result['calibrated_confidence']:.2%}")
        
        # Batch prediction
        batch_results = predictor.predict_batch([sample_features] * 3)
        print(f"✅ Batch prediction: {len(batch_results)} results")
        
        return predictor
        
    except Exception as e:
        print(f"❌ Predictor test failed: {e}")
        return None

def test_monitoring():
    """Test monitoring system."""
    print("\n🧪 Testing monitoring system...")
    
    from src.chainguardian.ml.core.monitoring import MLMonitor
    from src.chainguardian.ml.core.config_manager import get_config
    
    config = get_config()
    monitor = MLMonitor(config)
    
    # Log some predictions
    for i in range(10):
        monitor.log_prediction(
            features={'has_reentrancy': i % 2, 'num_external_calls': i},
            prediction={'prediction': i % 2, 'calibrated_confidence': 0.7},
            ground_truth=i % 2
        )
    
    # Get performance report
    report = monitor.get_performance_report(window_size=5)
    print(f"✅ Monitoring report generated:")
    print(f"   Accuracy: {report.get('accuracy', 0):.2%}")
    print(f"   Samples: {report.get('window_size', 0)}")
    
    return monitor

def main():
    """Run all tests."""
    print("=" * 80)
    print("🧪 ENHANCED HYBRID PREDICTOR v7 - TEST SUITE")
    print("=" * 80)
    
    # Test 1: Configuration
    config = test_configuration()
    
    # Test 2: Hyperparameter tuning (optional - can be slow)
    if config.hyperparameter_tuning.enable_optuna:
        test_hyperparameter_tuning()
    else:
        print("\n⚠️ Hyperparameter tuning disabled in config")
    
    # Test 3: Predictor
    predictor = test_predictor_integration()
    
    # Test 4: Monitoring
    if config.monitoring.get('enable_performance_logging', False):
        test_monitoring()
    else:
        print("\n⚠️ Monitoring disabled in config")
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 80)
    
    if predictor:
        print(f"\n🎯 Enhanced predictor ready with features:")
        print(f"   • Ensemble: {predictor.use_ensemble}")
        print(f"   • Configuration: Loaded from YAML")
        print(f"   • Monitoring: {predictor.monitor is not None}")
        print(f"   • Batch support: Enabled")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
