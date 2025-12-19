"""
LLM Feeder Models - Multi-Output ML System

FIXED VERSION:
- Handles categorical features (encodes contract_complexity_category)
- Works with balanced dataset (39% vulnerable, 61% safe)
- Trains 3 models: Risk Scorer, Multi-Label Classifier, Severity Classifier

PURPOSE:
Trains multiple models to provide rich, structured input to LLM phase.
Accepts that Slither features are useful and focuses on organizing
outputs for LLM consumption rather than replacing Slither.

Author: Ali - ChainGuardian AI Project
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier
from sklearn.multioutput import MultiOutputClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, classification_report, multilabel_confusion_matrix
import xgboost as xgb
import joblib
from pathlib import Path
import json
import warnings
warnings.filterwarnings('ignore')

print("\n" + "="*70)
print("🎯 LLM FEEDER MODELS: Multi-Output ML System (FIXED)")
print("="*70)
print("\nPurpose: Create rich, structured output for LLM/RAG phase")
print("Approach: Accept Slither usefulness, focus on organization")


# ============================================================
# HELPER FUNCTION: ENCODE CATEGORICAL FEATURES
# ============================================================
def encode_categorical_features(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Encode string categorical features to numeric.
    
    Handles:
    - contract_complexity_category: simple/moderate/complex/critical → 0/1/2/3
    
    Args:
        dataframe: DataFrame with potential categorical columns
        
    Returns:
        DataFrame with encoded features
    """
    if 'contract_complexity_category' in dataframe.columns:
        # Define encoding order (ordinal: simple < moderate < complex < critical)
        complexity_map = {
            'simple': 0,
            'moderate': 1, 
            'complex': 2,
            'critical': 3
        }
        
        # Create numeric version
        dataframe['complexity_level'] = dataframe['contract_complexity_category'].map(complexity_map)
        
        # Fill missing values with 0 (assume simple if unknown)
        dataframe['complexity_level'] = dataframe['complexity_level'].fillna(0).astype(int)
        
        # Log encoding stats
        if dataframe['contract_complexity_category'].notna().sum() > 0:
            print(f"\n✅ Encoded contract_complexity_category:")
            counts = dataframe['contract_complexity_category'].value_counts()
            for cat, count in counts.items():
                print(f"   {cat:12s} → {complexity_map[cat]} ({count:3d} contracts)")
    
    return dataframe


# ============================================================
# 1. LOAD DATA
# ============================================================
print("\n" + "="*70)
print("1️⃣ LOADING DATA")
print("="*70)

df = pd.read_csv('data/training_clean.csv')
df_full = pd.read_csv('data/training_labeled_full.csv')

# ================================================================
# PREPROCESS: ENCODE CATEGORICAL FEATURES
# ================================================================
print(f"\n🔧 Preprocessing features...")
df = encode_categorical_features(df)
df_full = encode_categorical_features(df_full)

# ================================================================
# EXTRACT LABELS AND FEATURES
# ================================================================
y_binary = df['label']

# Select only numeric features (drops any remaining string columns)
X = df.drop('label', axis=1).select_dtypes(include=[np.number])

# Log what was dropped
all_feature_cols = set(df.columns) - {'label'}
numeric_cols = set(X.columns)
dropped_cols = all_feature_cols - numeric_cols

if dropped_cols:
    print(f"\n⚠️  Dropped non-numeric columns:")
    for col in sorted(dropped_cols):
        print(f"   - {col}")

print(f"\n📊 Final Dataset:")
print(f"  Contracts: {len(X)}")
print(f"  Features: {len(X.columns)}")
print(f"  Vulnerable: {(y_binary == 1).sum()} ({(y_binary == 1).sum()/len(y_binary)*100:.1f}%)")
print(f"  Safe: {(y_binary == 0).sum()} ({(y_binary == 0).sum()/len(y_binary)*100:.1f}%)")


# ============================================================
# 2. MODEL A: RISK SCORE REGRESSOR (0-100)
# ============================================================
print("\n" + "="*70)
print("2️⃣ MODEL A: OVERALL RISK SCORE (0-100)")
print("="*70)

# ================================================================
# IDENTIFY RISK COMPONENTS
# ================================================================
# Use Slither severity counts as base, adjust with graph features
risk_components = []

for col in X.columns:
    if 'severity' in col:
        risk_components.append(col)
    elif 'detector' in col and 'triggered' in col:
        risk_components.append(col)

print(f"\nRisk score components: {len(risk_components)}")
for comp in risk_components:
    print(f"  - {comp}")

# ================================================================
# CREATE SYNTHETIC RISK SCORE TARGET
# ================================================================
# Formula: High issues count most, medium less, low minimal
# Plus bonus for known vulnerable contracts
df['risk_score_target'] = (
    df_full['high_severity_count'] * 30 +      # High severity: 30 points each
    df_full['medium_severity_count'] * 15 +    # Medium: 15 points each
    df_full['low_severity_count'] * 5 +        # Low: 5 points each
    df_full['security_detectors_triggered'] * 3 # Detector hits: 3 points each
).clip(upper=100)

# Add binary label bonus (contracts we KNOW are vulnerable get boost)
df['risk_score_target'] = df['risk_score_target'] + (y_binary * 20)
df['risk_score_target'] = df['risk_score_target'].clip(upper=100)

y_risk = df['risk_score_target']

print(f"\n📊 Risk score distribution:")
print(f"  Mean: {y_risk.mean():.1f}")
print(f"  Std: {y_risk.std():.1f}")
print(f"  Range: {y_risk.min():.1f} - {y_risk.max():.1f}")
print(f"\n  Breakdown:")
print(f"    0-25 (Low):      {((y_risk >= 0) & (y_risk < 25)).sum():3d} contracts")
print(f"    25-50 (Medium):  {((y_risk >= 25) & (y_risk < 50)).sum():3d} contracts")
print(f"    50-75 (High):    {((y_risk >= 50) & (y_risk < 75)).sum():3d} contracts")
print(f"    75-100 (Critical): {(y_risk >= 75).sum():3d} contracts")

# ================================================================
# TRAIN RISK SCORER
# ================================================================
rf_risk = RandomForestRegressor(
    n_estimators=200,
    max_depth=15,
    random_state=42,
    n_jobs=-1
)

X_train, X_test, y_risk_train, y_risk_test = train_test_split(
    X, y_risk, test_size=0.2, random_state=42
)

print(f"\n🏋️  Training Risk Scorer...")
rf_risk.fit(X_train, y_risk_train)
y_risk_pred = rf_risk.predict(X_test)

# Calculate metrics
rmse = np.sqrt(mean_squared_error(y_risk_test, y_risk_pred))
mae = np.mean(np.abs(y_risk_test - y_risk_pred))

print(f"\n✅ Risk Scorer Performance:")
print(f"  RMSE: {rmse:.2f}")
print(f"  Mean Absolute Error: {mae:.2f}")
print(f"  R² Score: {rf_risk.score(X_test, y_risk_test):.3f}")

# Show feature importance (top 10)
feature_importance = pd.DataFrame({
    'feature': X.columns,
    'importance': rf_risk.feature_importances_
}).sort_values('importance', ascending=False)

print(f"\n🔝 Top 10 Most Important Features:")
for idx, row in feature_importance.head(10).iterrows():
    print(f"  {row['feature']:40s} {row['importance']:.4f}")


# ============================================================
# 3. MODEL B: MULTI-LABEL VULNERABILITY CLASSIFIER
# ============================================================
print("\n" + "="*70)
print("3️⃣ MODEL B: MULTI-LABEL VULNERABILITY TYPES")
print("="*70)

# ================================================================
# DEFINE VULNERABILITY LABELS
# ================================================================
vuln_labels = [
    'has_reentrancy',
    'has_access_control_issues',
    'has_timestamp_dependency',
    'has_unchecked_call',
]

# Filter to contracts with vulnerability labels
# (SmartBugs and production vulnerable have ground truth labels)
df_labeled_full = df_full[
    df_full['data_source'].isin(['smartbugs_curated', 'production_vulnerable'])
].copy()

print(f"\n📊 Contracts with vulnerability labels: {len(df_labeled_full)}")

# Check if labels exist in dataset
available_labels = [l for l in vuln_labels if l in df_labeled_full.columns]
print(f"Available labels: {len(available_labels)}/{len(vuln_labels)}")

if len(available_labels) > 0:
    # ================================================================
    # PREPARE MULTI-LABEL DATA
    # ================================================================
    # Encode categorical features in labeled subset
    df_labeled_full = encode_categorical_features(df_labeled_full)
    
    # Get features for these contracts (must match X columns)
    feature_cols = X.columns.tolist()
    X_multilabel = df_labeled_full[feature_cols].copy()
    y_multilabel = df_labeled_full[available_labels].astype(int)
    
    print(f"\n📊 Label distribution:")
    for label in available_labels:
        count = (y_multilabel[label] == 1).sum()
        pct = count / len(y_multilabel) * 100
        print(f"  {label:35s}: {count:3d} ({pct:5.1f}%)")
    
    # ================================================================
    # TRAIN MULTI-LABEL CLASSIFIER
    # ================================================================
    multilabel_clf = MultiOutputClassifier(
        RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=10,    # ← Add this (was default 2)
            min_samples_leaf=4,
            random_state=42,
            n_jobs=-1,
            class_weight='balanced'  # Handle imbalanced labels
        )
    )
    
    X_ml_train, X_ml_test, y_ml_train, y_ml_test = train_test_split(
        X_multilabel, y_multilabel, test_size=0.2, random_state=42
    )
    
    print(f"\n🏋️  Training Multi-Label Classifier...")
    multilabel_clf.fit(X_ml_train, y_ml_train)
    y_ml_pred = multilabel_clf.predict(X_ml_test)
    
    print(f"\n✅ Multi-Label Classifier trained")
    
    # Get probabilities for confidence scores
    y_ml_proba = np.array([
        est.predict_proba(X_ml_test)[:, 1] 
        for est in multilabel_clf.estimators_
    ]).T
    
    print(f"  Output shape: {y_ml_proba.shape} (samples × labels)")
    
    # Calculate per-label accuracy
    print(f"\n📊 Per-Label Performance:")
    for i, label in enumerate(available_labels):
        correct = (y_ml_pred[:, i] == y_ml_test.iloc[:, i].values).sum()
        accuracy = correct / len(y_ml_test) * 100
        print(f"  {label:35s}: {accuracy:.1f}% accuracy")
else:
    print("\n⚠️  No vulnerability labels available, skipping multi-label model")
    multilabel_clf = None


# ============================================================
# 4. MODEL C: SEVERITY CLASSIFIER
# ============================================================
print("\n" + "="*70)
print("4️⃣ MODEL C: SEVERITY LEVEL PREDICTION")
print("="*70)

# ================================================================
# CREATE SEVERITY LABELS FROM RISK SCORES
# ================================================================
def risk_to_severity(risk_score):
    """Convert risk score to severity level."""
    if risk_score >= 75:
        return 3  # Critical
    elif risk_score >= 50:
        return 2  # High
    elif risk_score >= 25:
        return 1  # Medium
    else:
        return 0  # Low

y_severity = df['risk_score_target'].apply(risk_to_severity)

print(f"\n📊 Severity distribution:")
severity_names = ['Low', 'Medium', 'High', 'Critical']
for i, name in enumerate(severity_names):
    count = (y_severity == i).sum()
    pct = count / len(y_severity) * 100
    print(f"  {name:15s}: {count:3d} ({pct:5.1f}%)")

# ================================================================
# TRAIN SEVERITY CLASSIFIER
# ================================================================
gb_severity = GradientBoostingClassifier(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.1,
    random_state=42
)

X_sev_train, X_sev_test, y_sev_train, y_sev_test = train_test_split(
    X, y_severity, test_size=0.2, stratify=y_severity, random_state=42
)

print(f"\n🏋️  Training Severity Classifier...")
gb_severity.fit(X_sev_train, y_sev_train)
y_sev_pred = gb_severity.predict(X_sev_test)

print(f"\n✅ Severity Classifier Performance:")
print(classification_report(y_sev_test, y_sev_pred, target_names=severity_names, zero_division=0))


# ============================================================
# 5. SAVE ALL MODELS
# ============================================================
print("\n" + "="*70)
print("5️⃣ SAVING MODELS")
print("="*70)

models_dir = Path('models')
models_dir.mkdir(exist_ok=True)

# Save models
joblib.dump(rf_risk, models_dir / 'risk_scorer.pkl')
print(f"✅ Saved: risk_scorer.pkl")

joblib.dump(gb_severity, models_dir / 'severity_classifier.pkl')
print(f"✅ Saved: severity_classifier.pkl")

if multilabel_clf:
    joblib.dump(multilabel_clf, models_dir / 'multilabel_classifier.pkl')
    print(f"✅ Saved: multilabel_classifier.pkl")
    
    # Save label names
    with open(models_dir / 'vulnerability_labels.json', 'w') as f:
        json.dump(available_labels, f)
    print(f"✅ Saved: vulnerability_labels.json")

# Save feature names
with open(models_dir / 'feature_names.json', 'w') as f:
    json.dump(list(X.columns), f)
print(f"✅ Saved: feature_names.json")

# Save feature importance for risk scorer
feature_importance.to_csv(models_dir / 'feature_importance_rf.csv', index=False)
print(f"✅ Saved: feature_importance_rf.csv")


# ============================================================
# 6. CREATE PREDICTION PIPELINE
# ============================================================
print("\n" + "="*70)
print("6️⃣ CREATING LLM FEEDER PIPELINE")
print("="*70)

def predict_for_llm(features):
    """
    Generate rich prediction output for LLM consumption.
    
    Args:
        features: Feature vector for contract (pandas Series or array)
        
    Returns:
        dict: Structured output for LLM with:
            - overall_risk_score (0-100)
            - severity (level + confidence)
            - vulnerabilities (detected types + confidence)
            - recommendation (priority level)
    """
    output = {}
    
    # Convert to DataFrame if needed (sklearn expects 2D)
    if isinstance(features, pd.Series):
        features_df = features.to_frame().T
    else:
        features_df = pd.DataFrame([features], columns=X.columns)
    
    # ================================================================
    # OVERALL RISK SCORE
    # ================================================================
    risk_score = rf_risk.predict(features_df)[0]
    output['overall_risk_score'] = float(np.clip(risk_score, 0, 100))
    
    # ================================================================
    # SEVERITY LEVEL
    # ================================================================
    severity_pred = gb_severity.predict(features_df)[0]
    severity_proba = gb_severity.predict_proba(features_df)[0]
    output['severity'] = {
        'level': severity_names[severity_pred],
        'confidence': float(severity_proba[severity_pred])
    }
    
    # ================================================================
    # VULNERABILITY TYPES (if model available)
    # ================================================================
    if multilabel_clf:
        vuln_pred = multilabel_clf.predict(features_df)[0]
        vuln_proba = np.array([
            est.predict_proba(features_df)[0][1]
            for est in multilabel_clf.estimators_
        ])
        
        output['vulnerabilities'] = {}
        for i, label in enumerate(available_labels):
            output['vulnerabilities'][label] = {
                'detected': bool(vuln_pred[i]),
                'confidence': float(vuln_proba[i])
            }
    
    # ================================================================
    # RECOMMENDATION
    # ================================================================
    if output['overall_risk_score'] >= 70:
        output['recommendation'] = 'immediate_review'
    elif output['overall_risk_score'] >= 50:
        output['recommendation'] = 'high_priority'
    elif output['overall_risk_score'] >= 25:
        output['recommendation'] = 'standard_review'
    else:
        output['recommendation'] = 'low_priority'
    
    return output


# ================================================================
# TEST PIPELINE ON SAMPLE
# ================================================================
sample_features = X_test.iloc[0]
sample_output = predict_for_llm(sample_features)

print(f"\n📋 Example LLM Feeder Output:")
print(json.dumps(sample_output, indent=2))

# Save pipeline function
import dill
with open(models_dir / 'llm_feeder_pipeline.pkl', 'wb') as f:
    dill.dump(predict_for_llm, f)

print(f"\n✅ Pipeline saved: llm_feeder_pipeline.pkl")


# ============================================================
# FINAL SUMMARY
# ============================================================
print("\n" + "="*70)
print("🎉 LLM FEEDER SYSTEM COMPLETE")
print("="*70)

print(f"\n📊 SYSTEM OUTPUT FOR LLM:")
print(f"  1. Overall risk score (0-100) - Continuous metric")
print(f"  2. Severity level (Low/Medium/High/Critical) - Categorical")
print(f"  3. Vulnerability types with confidence - Multi-label")
print(f"  4. Priority recommendation - Action item")

print(f"\n💡 NEXT PHASE:")
print(f"  1. LLM receives this structured output")
print(f"  2. RAG retrieves similar exploits from vector DB")
print(f"  3. LLM generates detailed audit report")
print(f"  4. Human auditor reviews prioritized contracts")

print(f"\n✅ VALUE PROPOSITION:")
print(f"  - Fast ML pre-screening (cheap)")
print(f"  - Structured input for LLM (organized)")
print(f"  - Deep LLM reasoning (expensive, targeted)")
print(f"  - Human audit (most expensive, highest value)")

print(f"\n📁 FILES CREATED:")
print(f"  models/risk_scorer.pkl")
print(f"  models/severity_classifier.pkl")
if multilabel_clf:
    print(f"  models/multilabel_classifier.pkl")
    print(f"  models/vulnerability_labels.json")
print(f"  models/feature_names.json")
print(f"  models/feature_importance_rf.csv")
print(f"  models/llm_feeder_pipeline.pkl")

print("\n" + "="*70 + "\n")
