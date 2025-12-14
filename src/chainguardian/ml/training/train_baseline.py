"""
Random Forest Baseline Training - Day 4
"""

from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from imblearn.over_sampling import SMOTE
import joblib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    logger.info("="*70)
    logger.info("CHAINGUARDIAN AI - RANDOM FOREST TRAINING (DAY 4)")
    logger.info("="*70)
    
    # ✅ FIX: Correct path to dataset
    logger.info("\n[1/8] Loading dataset...")
    dataset_path = Path('data/ml_dataset_clean_dedup.csv')
    
    if not dataset_path.exists():
        logger.error(f"❌ Dataset not found at: {dataset_path}")
        logger.info("Available files:")
        for f in Path('data').glob('*.csv'):
            logger.info(f"  - {f}")
        return
    
    df = pd.read_csv(dataset_path)
    logger.info(f"✓ Loaded dataset: {len(df)} contracts, {len(df.columns)} columns")
    
    # Prepare features and target
    logger.info("\n[2/8] Preparing features and target...")
    
    target_col = 'has_reentrancy'
    drop_cols = ['contract_name', 'file_path', target_col]
    drop_cols = [col for col in drop_cols if col in df.columns]
    
    X = df.drop(columns=drop_cols)
    y = df[target_col]
    
    logger.info(f"✓ Features shape: {X.shape}")
    logger.info(f"✓ Feature names: {X.columns.tolist()}")
    logger.info(f"✓ Target distribution:")
    logger.info(f"  - False (no vulnerability): {(~y).sum()} ({(~y).sum()/len(y)*100:.1f}%)")
    logger.info(f"  - True (has vulnerability): {y.sum()} ({y.sum()/len(y)*100:.1f}%)")
    
    # Train/test split
    logger.info("\n[3/8] Splitting into train/test sets...")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    logger.info(f"✓ Train set: {len(X_train)} samples")
    logger.info(f"✓ Test set: {len(X_test)} samples")
    
    # Apply SMOTE
    logger.info("\n[4/8] Applying SMOTE for class imbalance...")
    
    logger.info("Before SMOTE:")
    logger.info(f"  - Train set size: {len(X_train)}")
    logger.info(f"  - Class 0: {(~y_train).sum()}")
    logger.info(f"  - Class 1: {y_train.sum()}")
    
    minority_count = min(y_train.sum(), (~y_train).sum())
    
    if minority_count >= 2:
        k_neighbors = min(minority_count - 1, 5)
        smote = SMOTE(random_state=42, k_neighbors=k_neighbors)
        X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)
        
        logger.info("After SMOTE:")
        logger.info(f"  - Train set size: {len(X_train_balanced)}")
        logger.info(f"  - Class 0: {(~y_train_balanced).sum()}")
        logger.info(f"  - Class 1: {y_train_balanced.sum()}")
    else:
        logger.warning(f"Not enough samples for SMOTE")
        X_train_balanced = X_train
        y_train_balanced = y_train
    
    # Train model
    logger.info("\n[5/8] Training Random Forest classifier...")
    
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1,
        verbose=1
    )
    
    model.fit(X_train_balanced, y_train_balanced)
    logger.info("✓ Training complete!")
    
    # Evaluate
    logger.info("\n[6/8] Evaluating model on test set...")
    
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    logger.info(f"\n{'='*70}")
    logger.info("TEST SET RESULTS")
    logger.info(f"{'='*70}")
    logger.info(f"Accuracy: {accuracy*100:.2f}%")
    
    logger.info(f"\nClassification Report:")
    report = classification_report(
        y_test, y_pred,
        target_names=['No Vulnerability', 'Has Vulnerability']
    )
    logger.info(f"\n{report}")
    
    logger.info(f"\nConfusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    logger.info(f"\n{cm}")
    
    logger.info(f"\nInterpretation:")
    logger.info(f"  True Negatives:  {cm[0,0]} (Correctly predicted safe)")
    logger.info(f"  False Positives: {cm[0,1]} (False alarms)")
    logger.info(f"  False Negatives: {cm[1,0]} (Missed vulnerabilities)")
    logger.info(f"  True Positives:  {cm[1,1]} (Correctly detected vulnerabilities)")
    
    # Feature importance
    logger.info("\n[7/8] Analyzing feature importance...")
    
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    logger.info(f"\nTop 10 Most Important Features:")
    for idx, row in feature_importance.head(10).iterrows():
        logger.info(f"  {row['feature']:.<40} {row['importance']:.4f}")
    
    # Save model
    logger.info("\n[8/8] Saving model...")
    
    models_dir = Path('models/saved_models')
    models_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = models_dir / 'random_forest_baseline_v1.pkl'
    joblib.dump(model, model_path)
    logger.info(f"✓ Model saved to: {model_path}")
    
    importance_path = models_dir / 'feature_importance_rf.csv'
    feature_importance.to_csv(importance_path, index=False)
    logger.info(f"✓ Feature importance saved to: {importance_path}")
    
    logger.info(f"\n{'='*70}")
    logger.info("TRAINING COMPLETE!")
    logger.info(f"{'='*70}")
    logger.info(f"Model accuracy: {accuracy*100:.2f}%")
    logger.info(f"Next step: Train XGBoost model (Day 5)")
    logger.info(f"{'='*70}")


if __name__ == "__main__":
    main()
