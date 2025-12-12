"""
Day 4: Random Forest Baseline Training
ChainGuardian AI - Smart Contract Vulnerability Detection
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from imblearn.over_sampling import SMOTE
import joblib
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main training workflow"""
    
    logger.info("="*70)
    logger.info("CHAINGUARDIAN AI - RANDOM FOREST TRAINING (DAY 4)")
    logger.info("="*70)
    
    # =====================================================================
    # STEP 1: LOAD DATASET
    # =====================================================================
    logger.info("\n[1/8] Loading dataset...")
    
    # Path relative to project root
    dataset_path = Path(__file__).parents[4] / 'data' / 'ml_dataset_fixed.csv'
    
    if not dataset_path.exists():
        logger.error(f"Dataset not found at: {dataset_path}")
        sys.exit(1)
    
    df = pd.read_csv(dataset_path)
    logger.info(f"✓ Loaded dataset: {df.shape[0]} contracts, {df.shape[1]} columns")
    logger.info(f"Columns: {df.columns.tolist()}")
    
    # =====================================================================
    # STEP 2: PREPARE FEATURES
    # =====================================================================
    logger.info("\n[2/8] Preparing features and target...")
    
    # Target variable
    target_col = 'has_reentrancy'
    
    # Check if target exists
    if target_col not in df.columns:
        logger.error(f"Target column '{target_col}' not found!")
        logger.info(f"Available columns: {df.columns.tolist()}")
        sys.exit(1)
    
    # Drop non-feature columns
    # Drop non-feature columns (including file_path which is text)
    drop_cols = ['contract_name', 'file_path', target_col]
    X = df.drop(columns=drop_cols)
    y = df[target_col]
    
    logger.info(f"✓ Features shape: {X.shape}")
    logger.info(f"✓ Feature names: {X.columns.tolist()}")
    logger.info(f"✓ Target distribution:")
    logger.info(f"  - False (no vulnerability): {(y == False).sum()} ({(y == False).sum()/len(y)*100:.1f}%)")
    logger.info(f"  - True (has vulnerability): {(y == True).sum()} ({(y == True).sum()/len(y)*100:.1f}%)")
    
    # =====================================================================
    # STEP 3: TRAIN/TEST SPLIT
    # =====================================================================
    logger.info("\n[3/8] Splitting into train/test sets...")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        stratify=y,  # Maintain class distribution
        random_state=42
    )
    
    logger.info(f"✓ Train set: {X_train.shape[0]} samples")
    logger.info(f"✓ Test set: {X_test.shape[0]} samples")
    
    # =====================================================================
    # STEP 4: HANDLE CLASS IMBALANCE (SMOTE)
    # =====================================================================
    logger.info("\n[4/8] Applying SMOTE for class imbalance...")
    
    logger.info(f"Before SMOTE:")
    logger.info(f"  - Train set size: {X_train.shape[0]}")
    logger.info(f"  - Class 0: {(y_train == False).sum()}")
    logger.info(f"  - Class 1: {(y_train == True).sum()}")
    
    smote = SMOTE(random_state=42)
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)
    
    logger.info(f"After SMOTE:")
    logger.info(f"  - Train set size: {X_train_balanced.shape[0]}")
    logger.info(f"  - Class 0: {(y_train_balanced == False).sum()}")
    logger.info(f"  - Class 1: {(y_train_balanced == True).sum()}")
    logger.info(f"✓ Classes are now balanced!")
    
    # =====================================================================
    # STEP 5: TRAIN RANDOM FOREST
    # =====================================================================
    logger.info("\n[5/8] Training Random Forest classifier...")
    
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=None,
        random_state=42,
        n_jobs=-1,  # Use all CPU cores
        verbose=1   # Show progress
    )
    
    model.fit(X_train_balanced, y_train_balanced)
    
    logger.info("✓ Training complete!")
    
    # =====================================================================
    # STEP 6: EVALUATE ON TEST SET
    # =====================================================================
    logger.info("\n[6/8] Evaluating model on test set...")
    
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    logger.info(f"\n{'='*70}")
    logger.info(f"TEST SET RESULTS")
    logger.info(f"{'='*70}")
    logger.info(f"Accuracy: {accuracy:.2%}")
    
    logger.info(f"\nClassification Report:")
    logger.info("\n" + classification_report(y_test, y_pred, target_names=['No Vulnerability', 'Has Vulnerability']))
    
    logger.info(f"\nConfusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    logger.info(f"\n{cm}")
    logger.info(f"\nInterpretation:")
    logger.info(f"  True Negatives:  {cm[0][0]} (Correctly predicted safe)")
    logger.info(f"  False Positives: {cm[0][1]} (False alarms)")
    logger.info(f"  False Negatives: {cm[1][0]} (Missed vulnerabilities)")
    logger.info(f"  True Positives:  {cm[1][1]} (Correctly detected vulnerabilities)")
    
    # =====================================================================
    # STEP 7: FEATURE IMPORTANCE
    # =====================================================================
    logger.info("\n[7/8] Analyzing feature importance...")
    
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    logger.info(f"\nTop 10 Most Important Features:")
    for idx, row in feature_importance.head(10).iterrows():
        logger.info(f"  {row['feature']:.<40} {row['importance']:.4f}")
    
    # =====================================================================
    # STEP 8: SAVE MODEL
    # =====================================================================
    logger.info("\n[8/8] Saving model...")
    
    # Create models directory
    models_dir = Path(__file__).parents[4] / 'models' / 'saved_models'
    models_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = models_dir / 'random_forest_baseline_v1.pkl'
    joblib.dump(model, model_path)
    
    logger.info(f"✓ Model saved to: {model_path}")
    
    # Save feature importance
    importance_path = models_dir / 'feature_importance_rf.csv'
    feature_importance.to_csv(importance_path, index=False)
    logger.info(f"✓ Feature importance saved to: {importance_path}")
    
    # =====================================================================
    # SUMMARY
    # =====================================================================
    logger.info("\n" + "="*70)
    logger.info("TRAINING COMPLETE!")
    logger.info("="*70)
    logger.info(f"Model accuracy: {accuracy:.2%}")
    logger.info(f"Model saved: {model_path}")
    logger.info(f"Next step: Train XGBoost model (Day 5)")
    logger.info("="*70 + "\n")


if __name__ == "__main__":
    main()