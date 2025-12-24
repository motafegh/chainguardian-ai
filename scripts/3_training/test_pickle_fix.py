#!/usr/bin/env python3
"""
Quick test for pickle serialization fix
Tests ONLY the ensemble pickle issue, not full training
"""
import sys
from pathlib import Path
import joblib
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

print("="*80)
print("🧪 TESTING PICKLE FIX FOR HETEROGENEOUS ENSEMBLE")
print("="*80)

# Step 1: Import the fixed ensemble
try:
    from chainguardian.ml.core.heterogeneous_ensemble import HeterogeneousEnsemble
    print("✅ Import successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Step 2: Create minimal mock config (MODULE-LEVEL CLASSES for pickle)
class MockHyperparameterConfig:
    """Mock config that CAN be pickled."""
    enable_optuna = False

class MockAugmentationConfig:
    """Mock augmentation config."""
    enabled = False
    strategy = 'none'

class MockMonitoringConfig:
    """Mock monitoring config."""
    enable_performance_logging = True

class MockConfig:
    """Mock config with proper nested classes."""
    def __init__(self):
        self.hyperparameter_tuning = MockHyperparameterConfig()
        self.augmentation = {'enabled': False}
        self.monitoring = {'enable_performance_logging': True}
        self.weights = {}
        self.thresholds = {}

config = MockConfig()
print("✅ Mock config created (missing ensemble config - will trigger fallback)")

# Step 3: Create ensemble (should trigger _validate_and_fix_config)
try:
    feature_names = ['feature_' + str(i) for i in range(10)]
    ensemble = HeterogeneousEnsemble(config, feature_names)
    print("✅ Ensemble created with fallback config")
    
    # Verify fallback config was applied
    if hasattr(config.ensemble, 'calibration_method'):
        print(f"   Calibration method: {config.ensemble.calibration_method.value}")
    if hasattr(config.ensemble, 'uncertainty'):
        print(f"   Uncertainty enabled: {config.ensemble.uncertainty.enable_bootstrap}")
        
except Exception as e:
    print(f"❌ Ensemble creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 4: Create minimal training data
X_train = np.random.rand(50, 10)
y_train = np.random.randint(0, 2, 50)
print("✅ Mock training data created (50 samples)")

# Step 5: Train ensemble (quick training with small data)
print("\n🔧 Training ensemble (this takes ~10 seconds)...")
try:
    ensemble.fit(X_train, y_train)
    print("✅ Ensemble trained")
except Exception as e:
    print(f"❌ Training failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 6: TEST PICKLE (the critical part!)
test_path = Path("models/test_pickle.pkl")
test_path.parent.mkdir(exist_ok=True)

try:
    print("\n" + "="*80)
    print("🔬 CRITICAL TEST: Pickling ensemble...")
    print("="*80)
    
    # This is where it was failing before
    joblib.dump(ensemble, test_path)
    print("✅ Pickle successful!")
    print(f"   File size: {test_path.stat().st_size / 1024:.1f} KB")
    
except Exception as e:
    print(f"❌ PICKLE FAILED: {e}")
    print("\n🚨 FIX NOT APPLIED CORRECTLY")
    print("   The ensemble still contains unpicklable objects")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 7: TEST UNPICKLE
try:
    loaded_ensemble = joblib.load(test_path)
    print("✅ Unpickle successful!")
except Exception as e:
    print(f"❌ Unpickle failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 8: Test loaded model still works
try:
    X_test = np.random.rand(10, 10)
    predictions = loaded_ensemble.predict_proba(X_test)
    print("✅ Loaded model can make predictions")
    print(f"   Prediction shape: {predictions[0].shape}")
except Exception as e:
    print(f"❌ Loaded model broken: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 9: TEST MODEL REGISTRY (the original failure point)
try:
    from chainguardian.ml.core.model_registry import ModelRegistry
    
    print("\n" + "="*80)
    print("🔬 TESTING MODEL REGISTRY (Original Failure Point)")
    print("="*80)
    
    # Create registry
    registry = ModelRegistry("models/test_registry")
    
    # Prepare model info (simulating what train_production_v7.py does)
    model_info = {
        'model': loaded_ensemble,
        'scaler': None,  # Not needed for test
        'feature_names': feature_names,
        'performance_metrics': {'test_auc': 0.95},
        'training_info': {'version': 'test', 'date': '2024-12-23'}
    }
    
    # This was failing before
    version = registry.register_model(model_info, description="Pickle fix test")
    print(f"✅ Model registry successful! Version: {version}")
    
except Exception as e:
    print(f"❌ Model registry failed: {e}")
    print("\n🚨 REGISTRY STILL BROKEN")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Cleanup
print("\n🧹 Cleaning up test files...")
test_path.unlink()
import shutil
if Path("models/test_registry").exists():
    shutil.rmtree("models/test_registry")

print("\n" + "="*80)
print("🎉 ALL TESTS PASSED!")
print("="*80)
print("✅ Pickle serialization: WORKING")
print("✅ Model registry: WORKING")
print("✅ Config fallback: WORKING")
print("\n🚀 You can now run full training with confidence!")
print("   poetry run python scripts/3_training/train_production_v7.py")
