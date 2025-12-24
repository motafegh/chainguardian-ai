#!/usr/bin/env python3
"""
Production Training v7 - Enhanced for Hybrid Predictor
=====================================================
Optimized with all new features.

KEY IMPROVEMENTS:
1. Optuna hyperparameter tuning
2. Platt scaling calibration
3. Heterogeneous ensemble
4. Data augmentation strategies
5. Model registry integration
6. Performance monitoring hooks

Author: Ali
Date: December 23, 2024
"""

import sys
import pandas as pd
import numpy as np
import joblib
import json
import yaml
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')
from chainguardian.ml.core.path_resolver import path_resolver

# ============================================================================
# CORRECTED IMPORTS - Use chainguardian, not src.chainguardian
# ============================================================================

# Add project root to path so we can import chainguardian
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import our new modules with error handling
try:
    from chainguardian.ml.core.config_manager import ConfigManager, get_config
    CONFIG_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ ConfigManager import failed: {e}")
    CONFIG_AVAILABLE = False

try:
    from chainguardian.ml.core.hyperparameter_tuner import HyperparameterTuner
    TUNER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ HyperparameterTuner import failed: {e}")
    TUNER_AVAILABLE = False

try:
    from chainguardian.ml.core.heterogeneous_ensemble import HeterogeneousEnsemble
    ENSEMBLE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ HeterogeneousEnsemble import failed: {e}")
    ENSEMBLE_AVAILABLE = False

try:
    from chainguardian.ml.core.data_augmenter import SmartContractAugmenter
    AUGMENTER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ SmartContractAugmenter import failed: {e}")
    AUGMENTER_AVAILABLE = False

try:
    from chainguardian.ml.core.model_registry import ModelRegistry
    REGISTRY_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ ModelRegistry import failed: {e}")
    REGISTRY_AVAILABLE = False

print("\n" + "="*80)
print("🚀 PRODUCTION TRAINING v7 - FIXED VERSION")
print("="*80)

# ============================================================================
# 1. LOAD CONFIGURATION
# ============================================================================

if CONFIG_AVAILABLE:
    config_manager = ConfigManager()
    
    # Try multiple config paths
    config_paths = [
        project_root / "config" / "hybrid_config.yaml",
        "config/hybrid_config.yaml",
        "../config/hybrid_config.yaml",
    ]
    
    config_loaded = False
    for config_path in config_paths:
        config_path = Path(config_path)
        if config_path.exists():
            print(f"✅ Found config at: {config_path}")
            config = config_manager.load_config(str(config_path))
            config_loaded = True
            break
    
    if not config_loaded:
        print("❌ Config file not found! Searched:")
        for path in config_paths:
            print(f"   - {Path(path).absolute()}")
        print("\n⚠️  Using default config")
        
        # Create proper default config using dataclasses
        from chainguardian.ml.core.config_manager import (
            Config, 
            EnsembleConfig, 
            HyperparameterConfig,
            CalibrationMethod
        )
        
        config = Config(
            hyperparameter_tuning=HyperparameterConfig(enable_optuna=False),
            ensemble=EnsembleConfig(
                enabled=True,
                calibration_method=CalibrationMethod.SIGMOID  # Proper Enum!
            ),
            augmentation={'enabled': False, 'strategy': 'none'},
            monitoring={'enable_performance_logging': True},
            weights={'data_quality_profiles': {}},
            thresholds={'vulnerability_prediction': 0.2}
        )

else:
    # CONFIG_AVAILABLE is False - create minimal default config
    print("⚠️  ConfigManager not available, using minimal defaults")
    
    from chainguardian.ml.core.config_manager import (
        Config, 
        EnsembleConfig, 
        HyperparameterConfig,
        CalibrationMethod,
        UncertaintyConfig  
    )
    
    config = Config(
        hyperparameter_tuning=HyperparameterConfig(enable_optuna=False),
        ensemble=EnsembleConfig(
            enabled=True,
            calibration_method=CalibrationMethod.SIGMOID,
            uncertainty=UncertaintyConfig()
        ),
        augmentation={'enabled': False, 'strategy': 'none'},
        monitoring={'enable_performance_logging': True},
        weights={},
        thresholds={}
    )

# Display loaded configuration
print(f"\n📁 Configuration:")
print(f"   Config type: {type(config).__name__}")
print(f"   Hyperparameter tuning: {'Enabled' if config.hyperparameter_tuning.enable_optuna else 'Disabled'}")
print(f"   Ensemble: {'Enabled' if config.ensemble.enabled else 'Disabled'}")
print(f"   Calibration method: {config.ensemble.calibration_method.value}")  # Access Enum value
print(f"   Augmentation: {config.augmentation.get('strategy', 'none')}")

# ============================================================================
# 2. LOAD DATA & PREPROCESSING
# ============================================================================

print(f"\n📥 Looking for dataset...")
print("=" * 80)
print(f"📂 PATHS (Running from: {Path.cwd()})")
print(f"📂 Project Root: {path_resolver.project_root}")
print("=" * 80)

# Use absolute path for dataset
datafile = path_resolver.data_dir / "ml_ready_v4.csv"

if not datafile.exists():
    print(f"❌ Could not find ml_ready_v4.csv at {datafile}")
    print(f"   Expected: {datafile.absolute()}")
    sys.exit(1)

print(f"✅ Found dataset at: {datafile}")
df = pd.read_csv(datafile)
print(f"✅ Loaded {len(df)} samples, {len(df.columns)} columns")


# Define leakage features to REMOVE
LEAKAGE_FEATURES = [
    'id', 'contract_name', 'data_source',
    'high_severity_count', 'medium_severity_count', 'low_severity_count',
    'total_detector_hits', 'security_detectors_triggered', 'unique_vulnerability_types',
    'risk_score_simple', 'risk_score_weighted',
    'high_confidence_detectors', 'medium_confidence_detectors', 'low_confidence_detectors',
    'has_delegatecall_loop', 'has_msg_value_loop', 'has_incorrect_solc_version',
    'has_outdated_compiler', 'num_dependencies', 'num_unused_functions',
    'detectors_per_function', 'detectors_per_loc',
    'cei_violations', 'cei_pattern_score',
]

# Separate features
exclude_cols = ['ground_truth_vulnerable'] + LEAKAGE_FEATURES
available_features = [col for col in df.columns if col not in exclude_cols and col in df.columns]

X = df[available_features]
y = df['ground_truth_vulnerable']

# Remove constant features
constant_features = X.columns[X.nunique() == 1].tolist()
if constant_features:
    print(f"\n⚠️  Removing {len(constant_features)} constant features")
    X = X.drop(columns=constant_features)

print(f"\n📊 Dataset Summary:")
print(f"   Features: {len(X.columns)}")
print(f"   Samples:  {len(X)}")
print(f"   Positive: {y.sum()} ({y.mean()*100:.1f}%)")

# Handle missing/infinite
X = X.fillna(0)
X = X.replace([np.inf, -np.inf], 999999)

# ============================================================================
# 3. DATA AUGMENTATION
# ============================================================================

if AUGMENTER_AVAILABLE and config.augmentation.get('enabled', False):
    print(f"\n🔄 Applying data augmentation: {config.augmentation.get('strategy')}")
    
    augmenter = SmartContractAugmenter(config)
    X_aug, y_aug = augmenter.augment(X, y)
    
    print(f"   Augmented: {len(X_aug)} samples (from {len(X)})")
    print(f"   Positive ratio: {y_aug.mean()*100:.1f}%")
    
    X, y = X_aug, y_aug
else:
    print(f"\n⚠️  Data augmentation disabled or not available")

# ============================================================================
# 4. TRAIN/VAL/TEST SPLIT (FIXED - HANDLES IMBALANCE)
# ============================================================================

# ============================================================================
# 4. TRAIN/VAL/TEST SPLIT (UPDATED - HANDLES CONTINUOUS LABELS FROM MIXUP)
# ============================================================================

print("\n" + "="*80)
print("🎯 TRAIN/VALIDATION/TEST SPLIT")
print("="*80)

from sklearn.model_selection import train_test_split

# Check if labels are binary or continuous (after mixup augmentation)
labels_are_binary = set(np.unique(y)) == {0, 1}

if labels_are_binary:
    print(f"\n📊 Class distribution (binary labels):")
    print(f"   Class 0 (SAFE): {(y == 0).sum()} samples")
    print(f"   Class 1 (VULNERABLE): {(y == 1).sum()} samples")
    
    # Use stratified split for binary labels
    if (y == 0).sum() >= 2 and (y == 1).sum() >= 2:
        X_train_val, X_test, y_train_val, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_train_val, y_train_val, test_size=0.25, random_state=42, stratify=y_train_val
        )
    else:
        print("⚠️  One class has too few samples for stratified split")
        print("   Using non-stratified split...")
        X_train_val, X_test, y_train_val, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=None
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_train_val, y_train_val, test_size=0.25, random_state=42, stratify=None
        )
else:
    # For continuous labels (after mixup augmentation), use non-stratified split
    print(f"\n📊 Label distribution (continuous from mixup):")
    print(f"   Min: {y.min():.3f}, Max: {y.max():.3f}, Mean: {y.mean():.3f}")
    print(f"   Using non-stratified split for continuous labels...")
    
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=None
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=0.25, random_state=42, stratify=None
    )

print(f"\n📈 Data Splits:")
print(f"   Training:    {len(X_train)} samples ({len(X_train)/len(X)*100:.1f}%)")
print(f"   Validation:  {len(X_val)} samples ({len(X_val)/len(X)*100:.1f}%)")
print(f"   Test:        {len(X_test)} samples ({len(X_test)/len(X)*100:.1f}%)")

# ============================================================================
# 5. FEATURE SCALING
# ============================================================================

print("\n🔧 Scaling features...")
from sklearn.preprocessing import RobustScaler
scaler = RobustScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# ============================================================================
# 6. HYPERPARAMETER TUNING (OPTUNA) - OPTIONAL
# ============================================================================

best_model = None
tuning_results = None

if TUNER_AVAILABLE and CONFIG_AVAILABLE and config.hyperparameter_tuning.enable_optuna:
    print("\n" + "="*80)
    print("🔬 OPTUNA HYPERPARAMETER OPTIMIZATION")
    print("="*80)
    
    try:
        # Initialize tuner
        tuner = HyperparameterTuner(config, X.columns.tolist())
        
        # Run optimization on training data (small trial for testing)
        tuning_results = tuner.optimize(X_train_scaled, y_train, n_trials=5)
        
        # Analyze results
        analysis = tuner.analyze_results()
        
        # Train best model
        best_model = tuner.get_best_model(X_train_scaled, y_train)
        
        # Evaluate on validation set
        from sklearn.metrics import roc_auc_score
        val_proba = best_model.predict_proba(X_val_scaled)[:, 1]
        val_auc = roc_auc_score(y_val, val_proba)
        
        print(f"\n✅ Best Model Performance:")
        print(f"   Validation AUC: {val_auc:.4f}")
        print(f"   Model Type: {tuning_results['best_params'].get('model_type')}")
        
    except Exception as e:
        print(f"⚠️  Hyperparameter tuning failed: {e}")
        print("   Continuing without tuning...")
else:
    print("\n⚠️  Hyperparameter tuning disabled or not available")


# ============================================================================
# 7. HETEROGENEOUS ENSEMBLE TRAINING
# ============================================================================

if ENSEMBLE_AVAILABLE and CONFIG_AVAILABLE and config.ensemble.enabled:
    print("\n" + "="*80)
    print("🤖 HETEROGENEOUS ENSEMBLE TRAINING")
    print("="*80)
    
    try:
        # ✅ Config is already properly typed by ConfigManager!
        print(f"   Calibration method: {config.ensemble.calibration_method.value}")
        print(f"   Type: {type(config.ensemble.calibration_method).__name__}")
        
        # Create ensemble (no manual fixing needed!)
        ensemble = HeterogeneousEnsemble(config, X.columns.tolist())
        
        # Train ensemble
        print("   Training ensemble...")
        ensemble.fit(X_train_scaled, y_train)
        
        # Optimize weights on validation set
        print("⚖️  Optimizing ensemble weights...")
        optimized_weights = ensemble.optimize_weights(X_val_scaled, y_val)
        
        # Evaluate ensemble on validation set
        val_predictions, val_probas, val_intervals = ensemble.predict_with_uncertainty(X_val_scaled)
        val_auc = roc_auc_score(y_val, val_probas[:, 1])
        from sklearn.metrics import accuracy_score, brier_score_loss
        val_acc = accuracy_score(y_val, val_predictions)
        val_brier = brier_score_loss(y_val, val_probas[:, 1])
        
        print(f"\n📊 Ensemble Validation Performance:")
        print(f"   AUC:           {val_auc:.4f}")
        print(f"   Accuracy:      {val_acc:.4f}")
        print(f"   Calibration:   Brier score: {val_brier:.4f}")
        
        final_model = ensemble
        use_ensemble = True
        
    except Exception as e:
        print(f"⚠️  Ensemble training failed: {e}")
        print("   Falling back to single model...")
        use_ensemble = False
else:
    print("\n⚠️  Ensemble disabled or not available")
    use_ensemble = False

# ============================================================================
# 8. SINGLE MODEL TRAINING (FALLBACK)
# ============================================================================

if not use_ensemble:
    print("\n" + "="*80)
    print("🎯 SINGLE MODEL TRAINING (XGBoost)")
    print("="*80)
    
    try:
        import xgboost as xgb
        from sklearn.calibration import CalibratedClassifierCV
        from sklearn.model_selection import StratifiedKFold
        
        # Train XGBoost with calibration
        base_model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,
            scale_pos_weight=(len(y_train) - y_train.sum()) / y_train.sum()
        )
        
        # Calibrate with Platt scaling
        calibrated_model = CalibratedClassifierCV(
            base_model,
            method='sigmoid',
            cv=StratifiedKFold(n_splits=min(5, min(y_train.value_counts())), shuffle=True, random_state=42),
            n_jobs=-1
        )
        
        calibrated_model.fit(X_train_scaled, y_train)
        final_model = calibrated_model
        
        # Evaluate
        test_proba = calibrated_model.predict_proba(X_test_scaled)[:, 1]
        test_predictions = (test_proba > 0.5).astype(int)
        
        from sklearn.metrics import roc_auc_score, accuracy_score, brier_score_loss
        test_auc = roc_auc_score(y_test, test_proba)
        test_acc = accuracy_score(y_test, test_predictions)
        test_brier = brier_score_loss(y_test, test_proba)
        
        print(f"\n📊 Single Model Test Performance:")
        print(f"   AUC:          {test_auc:.4f}")
        print(f"   Accuracy:     {test_acc:.4f}")
        print(f"   Brier Score:  {test_brier:.4f}")
        
    except Exception as e:
        print(f"❌ Single model training failed: {e}")
        sys.exit(1)

# ============================================================================
# 9. FINAL EVALUATION
# ============================================================================

print("\n" + "="*80)
print("🧪 FINAL TEST EVALUATION")
print("="*80)

from sklearn.metrics import roc_auc_score, accuracy_score, brier_score_loss, classification_report

if use_ensemble:
    # Use ensemble for final evaluation
    test_predictions, test_probas, test_intervals = final_model.predict_with_uncertainty(X_test_scaled)
    test_proba = test_probas[:, 1]
else:
    # Use single model
    test_proba = final_model.predict_proba(X_test_scaled)[:, 1]
    test_predictions = (test_proba > 0.5).astype(int)

# Calculate metrics
test_auc = roc_auc_score(y_test, test_proba)
test_acc = accuracy_score(y_test, test_predictions)
test_brier = brier_score_loss(y_test, test_proba)

print(f"\n🎯 Final Test Results:")
print(f"   AUC:          {test_auc:.4f}")
print(f"   Accuracy:     {test_acc:.4f}")
print(f"   Brier Score:  {test_brier:.4f}")
print(f"   Calibration:  {'EXCELLENT' if test_brier < 0.01 else 'GOOD' if test_brier < 0.025 else 'FAIR'}")

# Classification report
print(f"\n📋 Classification Report:")
print(classification_report(y_test, test_predictions, target_names=['SAFE', 'VULNERABLE']))

# ============================================================================
# 10. SAVE MODEL
# ============================================================================

print("=" * 80)
print("💾 SAVING MODEL")
print("=" * 80)

# Use absolute paths from path_resolver
MODELS_DIR = path_resolver.models_dir
print(f"📂 Models directory: {MODELS_DIR}")

if use_ensemble:
    model_path = MODELS_DIR / "ensemble_model_v7.pkl"
    scaler_path = MODELS_DIR / "ensemble_scaler_v7.pkl"
    
    # Ensemble has its own save method
    if hasattr(final_model, 'save'):
        final_model.save(str(model_path))
        print(f"✅ Ensemble saved to: {model_path}")
    else:
        joblib.dump(final_model, model_path)
        print(f"✅ Ensemble saved to: {model_path}")
else:
    model_path = MODELS_DIR / "production_model_v7.pkl"
    scaler_path = MODELS_DIR / "production_scaler_v7.pkl"
    joblib.dump(final_model, model_path)
    print(f"✅ Single model saved to: {model_path}")

# Save scaler
joblib.dump(scaler, scaler_path)
print(f"✅ Scaler saved to: {scaler_path}")

# Save metadata
metadata = {
    "feature_names": X.columns.tolist(),
    "model_type": "ensemble" if use_ensemble else "single",
    "performance_metrics": {
        "test_auc": float(test_auc),
        "test_accuracy": float(test_acc),
        "test_brier": float(test_brier)
    },
    "training_info": {
        "version": "v7_enhanced",
        "date": datetime.now().isoformat(),
        "dataset_size": len(X),
        "ensemble_used": use_ensemble,
        "hyperparameter_tuning": tuning_results is not None if TUNER_AVAILABLE else False
    }
}

if CONFIG_AVAILABLE:
    metadata["config"] = config.to_dict() if hasattr(config, 'to_dict') else str(config)

metadata_path = MODELS_DIR / "feature_metadata_v7.json"
with open(metadata_path, 'w') as f:
    json.dump(metadata, f, indent=2)
print(f"✅ Metadata saved to: {metadata_path}")

# ============================================================================
# 11. MODEL REGISTRY INTEGRATION (OPTIONAL)
# ============================================================================

if REGISTRY_AVAILABLE:
    print("=" * 80)
    print("📚 MODEL REGISTRY INTEGRATION")
    print("=" * 80)
    
    try:
        # Use absolute path from config or default
        registry_path = None
        if CONFIG_AVAILABLE and hasattr(config, 'model_registry'):
            registry_path_str = config.model_registry.get('registry_path')
            if registry_path_str:
                # Convert to absolute
                registry_path = path_resolver.project_root / registry_path_str
        
        # Initialize registry (will use default if registry_path is None)
        registry = ModelRegistry(str(registry_path) if registry_path else None)
        
        model_info = {
            "model": final_model,
            "scaler": scaler,
            "feature_names": X.columns.tolist(),
            "performance_metrics": metadata["performance_metrics"],
            "training_info": metadata["training_info"]
        }
        
        if CONFIG_AVAILABLE:
            model_info["config"] = config.to_dict() if hasattr(config, 'to_dict') else {}
        
        version = registry.register_model(model_info, description="Enhanced v7 model")
        print(f"✅ Model registered as version: {version}")
    except Exception as e:
        print(f"⚠️  Model registry failed: {e}")


# ============================================================================
# 12. SUMMARY
# ============================================================================

print("\n" + "="*80)
print("🏆 TRAINING v7 COMPLETE - SUMMARY")
print("="*80)

print(f"\n📊 MODEL PERFORMANCE:")
print(f"   AUC:           {test_auc:.4f}")
print(f"   Accuracy:      {test_acc:.4f}")
print(f"   Calibration:   {test_brier:.4f} Brier score")

print(f"\n🔧 FEATURES ENABLED:")
print(f"   Hyperparameter Tuning: {'✅' if TUNER_AVAILABLE and tuning_results else '❌'}")
print(f"   Ensemble: {'✅' if use_ensemble else '❌'}")
print(f"   Data Augmentation: {'✅' if AUGMENTER_AVAILABLE and config.augmentation.get('enabled', False) else '❌'}")
print(f"   Platt Scaling: {'✅' if not use_ensemble else '❌'} (ensemble uses its own calibration)")

print(f"\n💾 SAVED ASSETS:")
if use_ensemble:
    print(f"   • Ensemble model: ensemble_model_v7.pkl")
    print(f"   • Scaler: ensemble_scaler_v7.pkl")
else:
    print(f"   • Single model: production_model_v7.pkl")
    print(f"   • Scaler: production_scaler_v7.pkl")
print(f"   • Metadata: feature_metadata_v7.json")
if REGISTRY_AVAILABLE:
    print(f"   • Registry entry: v{version if 'version' in locals() else 'N/A'}")
print(f"   1. Test the model: python scripts/3_training/test_enhanced_v7.py")
print(f"\n🚀 NEXT STEPS:")
print(f"   1. Test the model: python scripts/3_training/test_enhanced_v7.py")
print(f"   2. Update your application to use EnhancedHybridPredictor")
print(f"   3. Monitor performance with the new monitoring system")

print(f"\n✅ TRAINING v7 COMPLETED SUCCESSFULLY!")