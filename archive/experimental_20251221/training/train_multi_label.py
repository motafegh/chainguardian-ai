"""
Multi-Label Vulnerability Prediction - PRODUCTION VERSION

Trains Random Forest models to predict smart contract vulnerabilities
from code structure features ONLY (no detector outputs = no data leakage).

Trains models for ALL vulnerabilities with sufficient data (≥5 positive samples).

Features:
- 17 code structure metrics (function count, complexity, etc.)
- Multi-label classification (each vulnerability independently)
- Cross-validation for overfitting detection
- Automatic skipping of insufficient data
- Feature importance analysis
- Comprehensive performance metrics

Author: ChainGuardian AI Team
Date: December 2025
"""

from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)
from sklearn.ensemble import RandomForestClassifier
import joblib

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


# ====================================================================
# FEATURE DEFINITIONS
# ====================================================================

# Code structure features ONLY (no detector outputs!)
CODE_STRUCTURE_FEATURES = [
    # Function/contract complexity
    'num_functions',
    'num_external_calls',
    'num_state_vars',
    'num_modifiers',
    'max_cyclomatic_complexity',
    'num_low_level_calls',
    
    # Code size metrics
    'lines_of_code',
    'num_contracts_in_file',
    'num_dependencies',
    
    # Code quality
    'avg_function_complexity',
    'num_functions_high_complexity',
    'num_comments',
    'comment_to_code_ratio',
    
    # Security-relevant patterns
    'num_payable_functions',
    'num_library_calls',
    'inheritance_depth',
    'num_unused_functions'
]

# ALL vulnerability flags (will auto-filter based on data availability)
ALL_VULNERABILITY_TARGETS = [
    # CRITICAL SEVERITY
    'has_reentrancy',
    'has_unchecked_call',
    'has_access_control_issues',
    'has_timestamp_dependency',
    
    # HIGH SEVERITY
    'has_reentrancy_unlimited',
    'has_tx_origin',
    'has_controlled_delegatecall',
    
    # MEDIUM SEVERITY
    'has_uninitialized_state',
    'has_uninitialized_storage',
    'has_uninitialized_local',
    'has_locked_ether',
    'has_unchecked_transfer',
    
    # LOW SEVERITY / QUALITY
    'has_shadowing_state',
    'has_shadowing_builtin',
    'has_inline_assembly',
    'has_reentrancy_events',
    'has_reentrancy_benign',
    'has_unused_state_vars',
    'has_unused_return_values',
    
    # INFORMATIONAL
    'has_incorrect_solc_version',
    'has_floating_pragma',
    'has_outdated_compiler'
]


def load_dataset(min_positive_samples: int = 5):
    """
    Load and prepare dataset for multi-label training.
    
    Args:
        min_positive_samples: Minimum positive samples required to include a target
    
    Returns:
        Tuple of (X, y, target_cols, feature_names)
    """
    logger.info("Loading dataset...")
    df = pd.read_csv('data/chainguardian_features_clean.csv')
    
    logger.info(f"✓ Loaded {len(df)} contracts with {len(df.columns)} columns")
    
    # Filter to only available features
    available_features = [f for f in CODE_STRUCTURE_FEATURES if f in df.columns]
    
    # Filter targets based on data availability
    viable_targets = []
    for target in ALL_VULNERABILITY_TARGETS:
        if target not in df.columns:
            continue
        
        positive_count = df[target].sum()
        if positive_count >= min_positive_samples:
            viable_targets.append(target)
    
    X = df[available_features].fillna(0)
    y = df[viable_targets].fillna(False)
    
    logger.info(f"\n✓ Features: {len(available_features)} code structure metrics")
    logger.info(f"   Feature list:")
    for i, feat in enumerate(available_features, 1):
        logger.info(f"      {i:2d}. {feat}")
    
    logger.info(f"\n✓ Targets: {len(viable_targets)} vulnerability types")
    logger.info(f"\n   Vulnerability distribution:")
    
    for target in viable_targets:
        count = df[target].sum()
        pct = count / len(df) * 100
        
        if count >= 20:
            status = "✅"
        elif count >= 10:
            status = "⚠️ "
        else:
            status = "📊"
        
        logger.info(f"   {status} {target:<35} {count:3d} ({pct:5.1f}%)")
    
    return X, y, viable_targets, available_features


def train_single_vulnerability(
    vuln_name: str,
    X_train, y_train,
    X_test, y_test,
    feature_names: list
):
    """
    Train and evaluate model for single vulnerability type.
    
    Args:
        vuln_name: Name of vulnerability (e.g., 'has_reentrancy')
        X_train, y_train: Training data
        X_test, y_test: Test data
        feature_names: List of feature names for importance
    
    Returns:
        Dictionary with metrics, or None if insufficient data
    """
    # Check data sufficiency
    n_train_pos = y_train.sum()
    n_test_pos = y_test.sum()
    
    if n_test_pos == 0:
        logger.info(f"\n⚠️  {vuln_name}: No test samples - SKIPPING")
        return None
    
    logger.info(f"\n{'='*70}")
    logger.info(f"VULNERABILITY: {vuln_name.replace('has_', '').upper().replace('_', ' ')}")
    logger.info(f"{'='*70}")
    
    # Class distribution
    train_pos_pct = (n_train_pos / len(y_train)) * 100
    
    logger.info(f"Training data:")
    logger.info(f"  Positive: {n_train_pos:3d} ({train_pos_pct:.1f}%)")
    logger.info(f"  Negative: {(~y_train).sum():3d} ({100-train_pos_pct:.1f}%)")
    logger.info(f"Test data:")
    logger.info(f"  Positive: {n_test_pos:3d}")
    logger.info(f"  Negative: {(~y_test).sum():3d}")
    
    # Train Random Forest
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        class_weight='balanced',
        n_jobs=-1
    )
    
    logger.info(f"\nTraining Random Forest...")
    clf.fit(X_train, y_train)
    
    # Cross-validation (if enough samples)
    if len(X_train) >= 30 and n_train_pos >= 5:
        try:
            cv_scores = cross_val_score(
                clf, X_train, y_train,
                cv=min(5, len(X_train) // 10),
                scoring='f1',
                n_jobs=-1
            )
            cv_f1 = cv_scores.mean()
            cv_std = cv_scores.std()
            logger.info(f"  CV F1-Score: {cv_f1:.3f} (+/- {cv_std:.3f})")
        except Exception as e:
            logger.warning(f"  CV failed: {e}")
            cv_f1 = None
            cv_std = None
    else:
        cv_f1 = None
        cv_std = None
    
    # Predictions
    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1]
    
    # Metrics
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    
    if n_test_pos > 0 and (~y_test).sum() > 0:
        try:
            auc = roc_auc_score(y_test, y_prob)
        except:
            auc = 0.0
    else:
        auc = 0.0
    
    cm = confusion_matrix(y_test, y_pred)
    
    # Log results
    logger.info(f"\nTest Performance:")
    logger.info(f"  Accuracy:  {acc*100:5.1f}%")
    logger.info(f"  Precision: {prec:5.3f}")
    logger.info(f"  Recall:    {rec:5.3f}")
    logger.info(f"  F1-Score:  {f1:5.3f}")
    if auc > 0:
        logger.info(f"  ROC-AUC:   {auc:5.3f}")
    
    logger.info(f"\nConfusion Matrix:")
    logger.info(f"  TN={cm[0,0]:3d}  FP={cm[0,1]:3d}")
    logger.info(f"  FN={cm[1,0]:3d}  TP={cm[1,1]:3d}")
    
    # Feature importance (top 5)
    feature_importance = pd.DataFrame({
        'feature': feature_names,
        'importance': clf.feature_importances_
    }).sort_values('importance', ascending=False)
    
    logger.info(f"\nTop 5 Important Features:")
    for idx, row in feature_importance.head(5).iterrows():
        logger.info(f"  {row['feature']:<35} {row['importance']:.4f}")
    
    # Save model
    models_dir = Path('models/vulnerability_specific')
    models_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = models_dir / f'{vuln_name}_rf.pkl'
    joblib.dump(clf, model_path)
    logger.info(f"\n✓ Model saved: {model_path.name}")
    
    return {
        'vulnerability': vuln_name,
        'accuracy': acc,
        'precision': prec,
        'recall': rec,
        'f1_score': f1,
        'roc_auc': auc if auc > 0 else None,
        'cv_f1': cv_f1,
        'cv_std': cv_std,
        'n_train_positive': int(n_train_pos),
        'n_test_positive': int(n_test_pos),
        'tn': int(cm[0,0]),
        'fp': int(cm[0,1]),
        'fn': int(cm[1,0]),
        'tp': int(cm[1,1]),
        'top_feature': feature_importance.iloc[0]['feature'],
        'top_importance': float(feature_importance.iloc[0]['importance'])
    }


def main():
    """Execute complete multi-label training pipeline."""
    
    print("="*70)
    print("MULTI-LABEL VULNERABILITY PREDICTION")
    print("Predicting vulnerabilities from CODE STRUCTURE only")
    print("="*70)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    
    # ================================================================
    # STEP 1: LOAD DATA
    # ================================================================
    X, y_multi, target_cols, feature_names = load_dataset(min_positive_samples=5)
    
    # ================================================================
    # STEP 2: TRAIN/TEST SPLIT
    # ================================================================
    logger.info(f"\n{'='*70}")
    logger.info("TRAIN/TEST SPLIT (80/20)")
    logger.info(f"{'='*70}")
    
    X_train, X_test, y_train_multi, y_test_multi = train_test_split(
        X, y_multi,
        test_size=0.2,
        random_state=42
    )
    
    logger.info(f"Train: {len(X_train)} samples")
    logger.info(f"Test:  {len(X_test)} samples")
    
    # ================================================================
    # STEP 3: TRAIN ALL MODELS
    # ================================================================
    results = []
    
    for vuln_col in target_cols:
        try:
            result = train_single_vulnerability(
                vuln_col,
                X_train, y_train_multi[vuln_col],
                X_test, y_test_multi[vuln_col],
                feature_names
            )
            if result:
                results.append(result)
        except Exception as e:
            logger.error(f"❌ Failed to train {vuln_col}: {e}")
    
    # ================================================================
    # STEP 4: SUMMARY
    # ================================================================
    logger.info(f"\n{'='*70}")
    logger.info("SUMMARY - ALL VULNERABILITIES")
    logger.info(f"{'='*70}\n")
    
    if not results:
        logger.error("No models trained successfully!")
        return
    
    df_results = pd.DataFrame(results)
    
    # Format display
    display_df = df_results.copy()
    display_df['Vulnerability'] = display_df['vulnerability'].str.replace('has_', '').str.replace('_', ' ').str.title()
    display_df['Acc%'] = (display_df['accuracy'] * 100).round(1).astype(str) + '%'
    display_df['Prec'] = display_df['precision'].round(3)
    display_df['Rec'] = display_df['recall'].round(3)
    display_df['F1'] = display_df['f1_score'].round(3)
    
    print(display_df[['Vulnerability', 'Acc%', 'Prec', 'Rec', 'F1', 'top_feature']].to_string(index=False))
    
    # Overall statistics
    logger.info(f"\n{'='*70}")
    logger.info("OVERALL STATISTICS")
    logger.info(f"{'='*70}")
    
    avg_acc = df_results['accuracy'].mean()
    avg_f1 = df_results['f1_score'].mean()
    avg_prec = df_results['precision'].mean()
    avg_rec = df_results['recall'].mean()
    
    logger.info(f"Models trained:    {len(results)}")
    logger.info(f"Average accuracy:  {avg_acc*100:.1f}%")
    logger.info(f"Average precision: {avg_prec:.3f}")
    logger.info(f"Average recall:    {avg_rec:.3f}")
    logger.info(f"Average F1-score:  {avg_f1:.3f}")
    
    # Best model
    best = df_results.loc[df_results['f1_score'].idxmax()]
    logger.info(f"\n🏆 Best performing:")
    logger.info(f"   {best['vulnerability']}")
    logger.info(f"   F1-Score: {best['f1_score']:.3f}")
    logger.info(f"   Accuracy: {best['accuracy']*100:.1f}%")
    logger.info(f"   Precision: {best['precision']:.3f}")
    logger.info(f"   Recall: {best['recall']:.3f}")
    
    # ================================================================
    # STEP 5: SAVE REPORTS
    # ================================================================
    reports_dir = Path('models/reports')
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Full results CSV
    results_path = reports_dir / f'multi_label_results_{timestamp}.csv'
    df_results.to_csv(results_path, index=False)
    logger.info(f"\n✓ Full results saved: {results_path}")
    
    # Summary text report
    summary_path = reports_dir / f'multi_label_summary_{timestamp}.txt'
    with open(summary_path, 'w') as f:
        f.write("="*70 + "\n")
        f.write("MULTI-LABEL VULNERABILITY PREDICTION SUMMARY\n")
        f.write("="*70 + "\n\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Total contracts: {len(X)}\n")
        f.write(f"Features used: {len(feature_names)}\n")
        f.write(f"Vulnerabilities predicted: {len(results)}\n\n")
        f.write(display_df[['Vulnerability', 'Acc%', 'Prec', 'Rec', 'F1']].to_string(index=False))
        f.write(f"\n\nOverall Statistics:\n")
        f.write(f"  Average accuracy: {avg_acc*100:.1f}%\n")
        f.write(f"  Average F1-score: {avg_f1:.3f}\n")
        f.write(f"\nBest Model:\n")
        f.write(f"  {best['vulnerability']}\n")
        f.write(f"  F1-Score: {best['f1_score']:.3f}\n")
    
    logger.info(f"✓ Summary saved: {summary_path}")
    logger.info(f"✓ Models saved: models/vulnerability_specific/")
    
    logger.info(f"\n{'='*70}")
    logger.info("TRAINING COMPLETE!")
    logger.info(f"{'='*70}\n")


if __name__ == "__main__":
    main()
