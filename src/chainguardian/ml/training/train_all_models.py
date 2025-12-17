"""
Train ALL models and compare performance.

Trains: Logistic, Random Forest, XGBoost, Ensemble
Outputs: Performance comparison + Best model
"""

from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import json
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)
import joblib

from chainguardian.ml.models.vulnerability_classifier import VulnerabilityClassifier

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def load_dataset():
    """Load and prepare dataset."""
    
    dataset_path = Path('data/chainguardian_features_clean.csv')
    df = pd.read_csv(dataset_path)
    
    logger.info(f"✓ Loaded {len(df)} contracts with {len(df.columns)} columns")
    
    # Target column
    target_col = 'is_high_risk'
    
    # Metadata columns to remove
    metadata_cols = [
        'contract_id', 'contract_name', 'address', 'file_path',
        'compiler_version', 'failure_reason', 'error_message',
        'contract_complexity_category'
    ]
    
    drop_cols = [c for c in metadata_cols + [target_col] if c in df.columns]
    
    X = df.drop(columns=drop_cols).fillna(0)
    y = df[target_col]
    
    logger.info(f"✓ Features: {X.shape}")
    logger.info(f"✓ Target: High risk={y.sum()} ({y.sum()/len(y)*100:.1f}%), Low/Med={(~y).sum()} ({(~y).sum()/len(y)*100:.1f}%)")
    
    return X, y


def train_model(model_type, X_train, y_train, X_test, y_test):
    """Train and evaluate single model."""
    
    logger.info(f"\n{'='*70}")
    logger.info(f"TRAINING: {model_type.upper()}")
    logger.info(f"{'='*70}")
    
    # Train
    clf = VulnerabilityClassifier(model_type=model_type)
    clf.fit(X_train, y_train)
    
    # Predict
    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1]
    
    # Metrics
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    auc = roc_auc_score(y_test, y_prob) if y_test.sum() > 0 else 0
    cm = confusion_matrix(y_test, y_pred)
    
    logger.info(f"Accuracy:  {acc*100:5.1f}%")
    logger.info(f"Precision: {prec:5.3f}")
    logger.info(f"Recall:    {rec:5.3f}")
    logger.info(f"F1-Score:  {f1:5.3f}")
    logger.info(f"ROC-AUC:   {auc:5.3f}")
    logger.info(f"Confusion: TN={cm[0,0]} FP={cm[0,1]} FN={cm[1,0]} TP={cm[1,1]}")
    
    # Save model
    Path('models/saved_models').mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    model_path = Path(f'models/saved_models/{model_type}_{timestamp}.pkl')
    joblib.dump(clf, model_path)
    
    return {
        'model_type': model_type,
        'accuracy': acc,
        'precision': prec,
        'recall': rec,
        'f1_score': f1,
        'roc_auc': auc,
        'model_path': str(model_path)
    }


def main():
    print("="*70)
    print("CHAINGUARDIAN AI - MULTI-MODEL TRAINING")
    print("="*70)
    
    # Load data
    X, y = load_dataset()
    
    # Split
    logger.info(f"\n{'='*70}")
    logger.info("TRAIN/TEST SPLIT (80/20)")
    logger.info(f"{'='*70}")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    logger.info(f"Train: {len(X_train)} samples")
    logger.info(f"Test:  {len(X_test)} samples")
    
    # Train all models
    models = ['logistic', 'random_forest', 'xgboost', 'ensemble']
    results = []
    
    for model_type in models:
        try:
            result = train_model(model_type, X_train, y_train, X_test, y_test)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to train {model_type}: {e}")
    
    # Compare
    logger.info(f"\n{'='*70}")
    logger.info("MODEL COMPARISON")
    logger.info(f"{'='*70}\n")
    
    df_results = pd.DataFrame(results)
    df_results['Model'] = df_results['model_type'].str.replace('_', ' ').str.title()
    
    print(df_results[['Model', 'accuracy', 'precision', 'recall', 'f1_score', 'roc_auc']].to_string(index=False))
    
    # Best model
    best = max(results, key=lambda x: x['f1_score'])
    
    logger.info(f"\n{'='*70}")
    logger.info(f"🏆 BEST MODEL: {best['model_type'].upper()}")
    logger.info(f"   F1-Score: {best['f1_score']:.3f}")
    logger.info(f"   Accuracy: {best['accuracy']*100:.1f}%")
    logger.info(f"{'='*70}\n")
    
    # Save comparison
    Path('models/reports').mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    df_results.to_csv(f'models/reports/comparison_{timestamp}.csv', index=False)
    
    logger.info(f"✓ Results saved to models/reports/comparison_{timestamp}.csv")
    logger.info(f"✓ Models saved to models/saved_models/")


if __name__ == "__main__":
    main()
