#!/usr/bin/env python3
"""
Path Infrastructure Smoke Test
================================
Validates path resolution, config loading, and file operations
without running expensive training.

Run: poetry run python scripts/3_training/test_paths.py
"""

import sys
from pathlib import Path
import numpy as np
import joblib
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("🔍 PATH INFRASTRUCTURE SMOKE TEST")
print("=" * 80)

# Test 1: Path Resolver
print("\n[TEST 1] Path Resolver")
try:
    from chainguardian.ml.core.path_resolver import path_resolver
    
    print(f"✅ Project Root: {path_resolver.project_root}")
    print(f"✅ Config Dir: {path_resolver.config_dir}")
    print(f"✅ Models Dir: {path_resolver.models_dir}")
    print(f"✅ Registry Dir: {path_resolver.registry_dir}")
    print(f"✅ Logs Dir: {path_resolver.logs_dir}")
    
    # Verify directories exist
    assert path_resolver.config_dir.exists(), "Config dir doesn't exist"
    assert path_resolver.models_dir.exists(), "Models dir doesn't exist"
    assert path_resolver.registry_dir.exists(), "Registry dir doesn't exist"
    
    print("✅ Path Resolver: PASSED")
except Exception as e:
    print(f"❌ Path Resolver: FAILED - {e}")
    sys.exit(1)

# Test 2: Config Loading
print("\n[TEST 2] Config Manager")
try:
    from chainguardian.ml.core.config_manager import ConfigManager
    
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    print(f"✅ Config loaded successfully")
    print(f"✅ Ensemble enabled: {config.ensemble.enabled}")
    print(f"✅ Calibration: {config.ensemble.calibration_method.value}")
    print(f"✅ Optuna trials: {config.hyperparameter_tuning.n_trials}")
    
    print("✅ Config Manager: PASSED")
except Exception as e:
    print(f"❌ Config Manager: FAILED - {e}")
    sys.exit(1)

# Test 3: Model Registry (Initialization)
print("\n[TEST 3] Model Registry Initialization")
try:
    from chainguardian.ml.core.model_registry import ModelRegistry
    
    # Test with default path
    registry = ModelRegistry()
    print(f"✅ Registry path: {registry.registry_path}")
    print(f"✅ Index file: {registry.index_file}")
    
    # Verify it's absolute and correct
    assert registry.registry_path.is_absolute(), "Registry path not absolute!"
    assert str(registry.registry_path).endswith("config/models/registry"), \
        f"Registry path wrong: {registry.registry_path}"
    
    # Check for nested config/config
    if "config/config" in str(registry.registry_path):
        raise ValueError("❌ NESTED PATH DETECTED: config/config/")
    
    print("✅ Model Registry Init: PASSED")
except Exception as e:
    print(f"❌ Model Registry Init: FAILED - {e}")
    sys.exit(1)

# Test 4: Dummy Model Save/Load
print("\n[TEST 4] Model Save/Load Operations")
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import RobustScaler
    
    # Create dummy model
    dummy_model = RandomForestClassifier(n_estimators=10, max_depth=3, random_state=42)
    X_dummy = np.random.rand(100, 10)
    y_dummy = np.random.randint(0, 2, 100)
    dummy_model.fit(X_dummy, y_dummy)
    
    # Create dummy scaler
    dummy_scaler = RobustScaler()
    dummy_scaler.fit(X_dummy)
    
    # Save to models directory
    test_model_path = path_resolver.models_dir / "test_model.pkl"
    test_scaler_path = path_resolver.models_dir / "test_scaler.pkl"
    
    joblib.dump(dummy_model, test_model_path)
    joblib.dump(dummy_scaler, test_scaler_path)
    
    print(f"✅ Saved model to: {test_model_path}")
    print(f"✅ Saved scaler to: {test_scaler_path}")
    
    # Verify they exist and are in correct location
    assert test_model_path.exists(), "Model file not saved!"
    assert test_scaler_path.exists(), "Scaler file not saved!"
    assert str(test_model_path).count("/models/") == 1, "Multiple /models/ in path!"
    
    # Load them back
    loaded_model = joblib.load(test_model_path)
    loaded_scaler = joblib.load(test_scaler_path)
    
    print(f"✅ Loaded model successfully")
    print(f"✅ Model type: {type(loaded_model).__name__}")
    
    # Cleanup test files
    test_model_path.unlink()
    test_scaler_path.unlink()
    print(f"✅ Cleaned up test files")
    
    print("✅ Model Save/Load: PASSED")
except Exception as e:
    print(f"❌ Model Save/Load: FAILED - {e}")
    sys.exit(1)

# Test 5: Registry Save/Load
print("\n[TEST 5] Model Registry Save/Load")
try:
    from chainguardian.ml.core.model_registry import ModelRegistry
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import RobustScaler
    
    # Create dummy model
    dummy_model = RandomForestClassifier(n_estimators=10, random_state=42)
    X_dummy = np.random.rand(50, 10)
    y_dummy = np.random.randint(0, 2, 50)
    dummy_model.fit(X_dummy, y_dummy)
    
    dummy_scaler = RobustScaler()
    dummy_scaler.fit(X_dummy)
    
    # Initialize registry
    registry = ModelRegistry()
    
    # Register model
    model_info = {
        "model": dummy_model,
        "scaler": dummy_scaler,
        "feature_names": [f"feature_{i}" for i in range(10)],
        "performance_metrics": {
            "test_auc": 0.95,
            "test_accuracy": 0.92
        },
        "training_info": {
            "version": "test_v1",
            "dataset_size": 50
        }
    }
    
    version = registry.register_model(model_info, description="Test model for path validation")
    print(f"✅ Registered model as version: {version}")
    
    # Verify version directory location
    version_dir = registry.registry_path / f"v{version}"
    assert version_dir.exists(), f"Version directory not created: {version_dir}"
    assert (version_dir / "model.pkl").exists(), "Model not saved in registry"
    assert (version_dir / "scaler.pkl").exists(), "Scaler not saved in registry"
    assert (version_dir / "metadata.json").exists(), "Metadata not saved in registry"
    
    print(f"✅ Version directory: {version_dir}")
    print(f"✅ Files created: model.pkl, scaler.pkl, metadata.json")
    
    # Check for nested paths
    if "config/config" in str(version_dir):
        raise ValueError("❌ NESTED PATH IN REGISTRY: config/config/")
    
    # Load model back
    loaded_info = registry.get_model(version)
    print(f"✅ Loaded model version {version} successfully")
    print(f"✅ Model type: {type(loaded_info['model']).__name__}")
    print(f"✅ Feature count: {len(loaded_info['metadata']['feature_names'])}")
    
    # List models
    models = registry.list_models()
    print(f"✅ Registry contains {len(models)} model(s)")
    
    print("✅ Model Registry Save/Load: PASSED")
except Exception as e:
    print(f"❌ Model Registry Save/Load: FAILED - {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Data File Access
print("\n[TEST 6] Data File Access")
try:
    import pandas as pd
    
    datafile = path_resolver.data_dir / "ml_ready_v4.csv"
    
    if datafile.exists():
        df = pd.read_csv(datafile)
        print(f"✅ Found dataset at: {datafile}")
        print(f"✅ Loaded {len(df)} samples, {len(df.columns)} columns")
        print("✅ Data File Access: PASSED")
    else:
        print(f"⚠️  Dataset not found at: {datafile}")
        print("⚠️  Data File Access: SKIPPED (not critical for path test)")
except Exception as e:
    print(f"❌ Data File Access: FAILED - {e}")
    sys.exit(1)

# Test 7: Path Consistency Check
print("\n[TEST 7] Path Consistency Check")
try:
    # All paths should be under project root
    assert str(path_resolver.models_dir).startswith(str(path_resolver.project_root)), \
        "Models dir not under project root!"
    
    assert str(path_resolver.registry_dir).startswith(str(path_resolver.project_root)), \
        "Registry dir not under project root!"
    
    # No duplicate config/ in paths
    models_path_str = str(path_resolver.models_dir)
    assert models_path_str.count("/config/") == 1, \
        f"Multiple /config/ in path: {models_path_str}"
    
    registry_path_str = str(path_resolver.registry_dir)
    assert registry_path_str.count("/config/") == 1, \
        f"Multiple /config/ in path: {registry_path_str}"
    
    print(f"✅ All paths under project root")
    print(f"✅ No duplicate /config/ directories")
    print("✅ Path Consistency: PASSED")
except Exception as e:
    print(f"❌ Path Consistency: FAILED - {e}")
    sys.exit(1)

# Final Summary
print("\n" + "=" * 80)
print("✅ ALL TESTS PASSED - INFRASTRUCTURE READY")
print("=" * 80)
print("\n📊 Path Summary:")
print(f"   Project Root: {path_resolver.project_root}")
print(f"   Models Dir:   {path_resolver.models_dir}")
print(f"   Registry Dir: {path_resolver.registry_dir}")
print(f"\n✅ You can now run full training safely:")
print(f"   poetry run python scripts/3_training/train_production_v7.py")
print("=" * 80)
