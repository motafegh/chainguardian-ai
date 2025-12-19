"""
Random Forest Baseline Training - PRODUCTION VERSION
====================================================

Trains a Random Forest classifier for smart contract vulnerability detection.
"""

from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, roc_auc_score
from imblearn.over_sampling import SMOTE
import joblib
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    logger.info("="*70)
    logger.info("CHAINGUARDIAN AI - RANDOM FOREST TRAINING")
    logger.info("="*70)
    
    # ================================================================
    # STEP 1: LOAD DATASET
    # ================================================================
    logger.info("\n[1/9] Loading dataset...")
    dataset_path = Path('data/ml_dataset_clean_dedup.csv')
    
    if not dataset_path.exists():
        logger.error(f"❌ Dataset not found at: {dataset_path}")
        logger.info("Run data preparation first:")
        logger.info("  poetry run python scripts/prepare_ml_dataset.py")
        return
    
    df = pd.read_csv(dataset_path)
    logger.info(f"✓ Loaded dataset: {len(df)} contracts, {len(df.columns)} columns")
    
    # ================================================================
    # STEP 2: PREPARE FEATURES AND TARGET
    # ================================================================
    logger.info("\n[2/9] Preparing features and target...")
    
    target_col = 'has_reentrancy'
    metadata_cols = ['contract_name', 'file_path']
    
    # Remove metadata and target from features
    drop_cols = metadata_cols + [target_col]
    drop_cols = [col for col in drop_cols if col in df.columns]
    
    X = df.drop(columns=drop_cols)
    y = df[target_col]
    
    logger.info(f"✓ Features shape: {X.shape}")
    logger.info(f"✓ Feature names: {X.columns.tolist()}")
    logger.info(f"✓ Target distribution:")
    logger.info(f"  - Negative (safe): {(~y).sum()} ({(~y).sum()/len(y)*100:.1f}%)")
    logger.info(f"  - Positive (vulnerable): {y.sum()} ({y.sum()/len(y)*100:.1f}%)")
    
    # Check if enough data
    if len(df) < 50:
        logger.warning(f"\n⚠️ Only {len(df)} samples - results may not be reliable")
    
    # ================================================================
    # STEP 3: TRAIN/TEST SPLIT
    # ================================================================
    logger.info("\n[3/9] Splitting into train/test sets (80/20)...")
    
    # Use stratify if minority class >= 2
    stratify_param = y if y.sum() >= 2 and (~y).sum() >= 2 else None
    
    if stratify_param is None:
        logger.warning("⚠️ Cannot stratify - one class has < 2 samples")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=0.2, 
        random_state=42, 
        stratify=stratify_param
    )
    
    logger.info(f"✓ Train set: {len(X_train)} samples")
    logger.info(f"  - Negative: {(~y_train).sum()}")
    logger.info(f"  - Positive: {y_train.sum()}")
    logger.info(f"✓ Test set: {len(X_test)} samples")
    logger.info(f"  - Negative: {(~y_test).sum()}")
    logger.info(f"  - Positive: {y_test.sum()}")
    
    # ================================================================
    # STEP 4: HANDLE CLASS IMBALANCE WITH SMOTE
    # ================================================================
    logger.info("\n[4/9] Handling class imbalance with SMOTE...")
    
    minority_count = min(y_train.sum(), (~y_train).sum())
    
    if minority_count >= 6:  # SMOTE needs at least k+1 samples (default k=5)
        k_neighbors = min(minority_count - 1, 5)
        
        logger.info(f"Applying SMOTE with k_neighbors={k_neighbors}...")
        logger.info(f"Before SMOTE:")
        logger.info(f"  - Train set size: {len(X_train)}")
        logger.info(f"  - Negative: {(~y_train).sum()}")
        logger.info(f"  - Positive: {y_train.sum()}")
        
        smote = SMOTE(random_state=42, k_neighbors=k_neighbors)
        X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)
        
        logger.info(f"After SMOTE:")
        logger.info(f"  - Train set size: {len(X_train_balanced)}")
        logger.info(f"  - Negative: {(~y_train_balanced).sum()}")
        logger.info(f"  - Positive: {y_train_balanced.sum()}")
    else:
        logger.warning(f"⚠️ Not enough samples for SMOTE (need >= 6, have {minority_count})")
        logger.warning("   Training without SMOTE - model may have low recall")
        X_train_balanced = X_train
        y_train_balanced = y_train
    
    # ================================================================
    # STEP 5: TRAIN RANDOM FOREST
    # ================================================================
    logger.info("\n[5/9] Training Random Forest classifier...")
    
    # Adjust model complexity based on dataset size
    n_estimators = 100 if len(X_train) >= 50 else 50
    max_depth = 10 if len(X_train) >= 50 else 5
    
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
        verbose=1,
        class_weight='balanced'  # Additional balancing
    )
    
    logger.info(f"Model hyperparameters:")
    logger.info(f"  - n_estimators: {n_estimators}")
    logger.info(f"  - max_depth: {max_depth}")
    logger.info(f"  - class_weight: balanced")
    
    model.fit(X_train_balanced, y_train_balanced)
    logger.info("✓ Training complete!")
    
    # ================================================================
    # STEP 6: CROSS-VALIDATION (if enough samples)
    # ================================================================
    if len(X_train) >= 30:
        logger.info("\n[6/9] Running 5-fold cross-validation...")
        
        cv_scores = cross_val_score(
            model, X_train_balanced, y_train_balanced,
            cv=min(5, len(X_train) // 10),  # Adjust folds for small datasets
            scoring='accuracy'
        )
        
        logger.info(f"✓ CV Accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")
    else:
        logger.info("\n[6/9] Skipping cross-validation (dataset too small)")
    
    # ================================================================
    # STEP 7: EVALUATE ON TEST SET
    # ================================================================
    logger.info("\n[7/9] Evaluating model on test set...")
    
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    accuracy = accuracy_score(y_test, y_pred)
    
    logger.info(f"\n{'='*70}")
    logger.info("TEST SET RESULTS")
    logger.info(f"{'='*70}")
    logger.info(f"Accuracy: {accuracy*100:.2f}%")
    
    # ROC-AUC (if both classes present in test set)
    if y_test.sum() > 0 and (~y_test).sum() > 0:
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        logger.info(f"ROC-AUC: {roc_auc:.3f}")
    
    logger.info(f"\nClassification Report:")
    report = classification_report(
        y_test, y_pred,
        target_names=['Safe', 'Vulnerable'],
        zero_division=0
    )
    logger.info(f"\n{report}")
    
    logger.info(f"\nConfusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    logger.info(f"\n{cm}")
    logger.info(f"\nInterpretation:")
    logger.info(f"  True Negatives (TN):  {cm[0,0]} (Correctly predicted safe)")
    logger.info(f"  False Positives (FP): {cm[0,1]} (False alarms)")
    logger.info(f"  False Negatives (FN): {cm[1,0]} (⚠️ Missed vulnerabilities!)")
    logger.info(f"  True Positives (TP):  {cm[1,1]} (✓ Caught vulnerabilities)")
    
    # ================================================================
    # STEP 8: FEATURE IMPORTANCE
    # ================================================================
    logger.info("\n[8/9] Analyzing feature importance...")
    
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    logger.info(f"\nTop 10 Most Important Features:")
    for idx, row in feature_importance.head(10).iterrows():
        logger.info(f"  {row['feature']:.<40} {row['importance']:.4f}")
    
    # ================================================================
    # STEP 9: SAVE MODEL AND ARTIFACTS
    # ================================================================
    logger.info("\n[9/9] Saving model and artifacts...")
    
    models_dir = Path('models/saved_models')
    models_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    
    # Save model
    model_path = models_dir / f'random_forest_baseline_v1_{timestamp}.pkl'
    joblib.dump(model, model_path)
    logger.info(f"✓ Model saved to: {model_path}")
    
    # Save feature importance
    importance_path = models_dir / f'feature_importance_rf_{timestamp}.csv'
    feature_importance.to_csv(importance_path, index=False)
    logger.info(f"✓ Feature importance saved to: {importance_path}")
    
    # Save metrics
    metrics = {
        'timestamp': timestamp,
        'train_samples': len(X_train),
        'test_samples': len(X_test),
        'accuracy': accuracy,
        'confusion_matrix': cm.tolist(),
    }
    
    import json
    metrics_path = models_dir / f'metrics_rf_{timestamp}.json'
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"✓ Metrics saved to: {metrics_path}")
    
    # ================================================================
    # FINAL SUMMARY
    # ================================================================
    logger.info(f"\n{'='*70}")
    logger.info("TRAINING COMPLETE!")
    logger.info(f"{'='*70}")
    logger.info(f"Model accuracy: {accuracy*100:.2f}%")
    logger.info(f"Model saved: {model_path.name}")
    logger.info(f"\nNext steps:")
    logger.info(f"  1. Review feature importance to understand model decisions")
    logger.info(f"  2. Test model on new contracts")
    logger.info(f"  3. Consider training XGBoost for comparison")
    logger.info(f"{'='*70}")


if __name__ == "__main__":
    main()
