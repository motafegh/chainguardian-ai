# ChainGuardian AI - ML Strategy

## 🎯 Objective
Build honest vulnerability detection model that learns REAL patterns, not dataset signatures.

---

## 📊 Current Dataset Status

### Labeled Data (For Training)
- **Total**: ~416 contracts
- **Vulnerable**: ~164 (39%)
  - SmartBugs: ~139 (85%)
  - Production: ~25 (15%)
- **Safe**: ~252 (61%)
  - OpenZeppelin: ~205 (81%)
  - Production: ~47 (19%)

### Unlabeled Data (For Prediction)
- **Total**: ~84 contracts
- **Source**: Live blockchain (manual collection)
- **Strategy**: Predict using trained model, then manually verify

---

## 🚨 Known Issues from Day 2

### Issue 1: Data Leakage (FIXED)
**Problem**: Previous models achieved 99.7% AUC due to:
- Contract ID as feature (344 dummy variables!)
- Proxy features (complexity, LOC, etc.)
- Model learned "SmartBugs vs OpenZeppelin" not vulnerabilities

**Solution**:
✅ Removed contract_id
✅ Will remove proxy features before training
✅ Added production sources (25% of dataset)

### Issue 2: Inverted Signals (DISCOVERED)
**Problem**: SmartBugs contracts were SIMPLER than OpenZeppelin
- Model learned "simple = vulnerable"
- Opposite of reality!

**Solution**:
✅ Collected complex vulnerable contracts (Trail of Bits)
✅ Mixed complexity levels in both classes

---

## 🔧 Feature Engineering Plan

### Phase 1: Remove Proxy Features
**Why**: These cause data leakage - model learns dataset signature

**Features to REMOVE**:
```python
proxy_features = [
    'lines_of_code',              # Dataset signature
    'num_functions',              # Complexity proxy
    'num_contracts_in_file',      # File structure
    'num_dependencies',           # Import count
    'contract_complexity_category', # Explicit complexity label
    'avg_function_complexity',    # Derived complexity
    'num_functions_high_complexity', # Complexity threshold
    'num_comments',               # Code style
    'comment_to_code_ratio',      # Code style
]
```

### Phase 2: Keep Security-Relevant Features
**Why**: These capture actual vulnerability patterns

**Features to KEEP**:
```python
security_features = [
    # Vulnerability flags (23 features)
    'has_reentrancy', 'has_access_control_issues', 
    'has_unchecked_call', 'has_timestamp_dependency',
    # ... all has_* features
    
    # Severity counts (3 features)
    'high_severity_count', 'medium_severity_count', 'low_severity_count',
    
    # Graph features (26 features)
    'cfg_num_nodes', 'cfg_num_cycles', 'cfg_max_depth',
    'cg_max_call_depth', 'cg_num_external_calls',
    'dfg_num_tainted_flows', 'dfg_num_sensitive_sinks',
    # ... all cfg_*, cg_*, dfg_* features
    
    # Detector stats (9 features)
    'high_confidence_detectors', 'security_detectors_triggered',
    # ... detector-related features
]
```

### Phase 3: Feature Validation
**Adversarial Validation**: Check if model can distinguish datasets
- If AUC > 0.6 → Features still leak dataset info
- If AUC ~ 0.5 → Features are dataset-independent ✅

---

## 🤖 Model Training Plan

### Approach: Semi-Supervised Learning

#### Step 1: Train on Labeled Data Only
```python
# Only use contracts with ground truth labels
X_train = labeled_contracts[security_features]
y_train = labeled_contracts['label']

# Models to try:
models = [
    'Logistic Regression',  # Baseline
    'Random Forest',        # Feature importance
    'XGBoost',             # Best performance
]
```

#### Step 2: Cross-Validation
```python
# 5-fold stratified CV
cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='roc_auc')

# Expected honest AUC: 0.65 - 0.80
# If > 0.90 → Still data leakage!
```

#### Step 3: Feature Importance Analysis
```python
# Check which features matter most
# Should see: vulnerability flags, graph metrics
# Should NOT see: complexity, LOC, etc.
```

#### Step 4: Predict Unlabeled Contracts
```python
# Use trained model on 84 unlabeled contracts
predictions = model.predict_proba(X_unlabeled)

# Prioritize high-risk for manual review
high_risk = predictions[:, 1] > 0.7  # 70% confidence
```

#### Step 5: Manual Verification
```python
# Review high-risk contracts on Etherscan
# Add verified labels to training set
# Retrain with expanded dataset
```

---

## 📏 Success Metrics

### Model Performance
- **CV AUC**: 0.65 - 0.80 (honest range)
- **Precision**: >70% (minimize false positives)
- **Recall**: >60% (catch most vulnerabilities)

### Feature Importance
- Top features should be vulnerability-specific
- No complexity/LOC features in top 10
- Graph features should rank high

### Adversarial Validation
- Dataset AUC: ~0.50 (can't distinguish sources)
- Features are dataset-independent

---

## 🎯 Training Phases

### Phase 1: Baseline (Current)
- Features: Security features only (~60 features)
- Data: 416 labeled contracts
- Goal: Establish honest baseline (AUC 0.65-0.75)

### Phase 2: Feature Engineering (Next)
- Add interaction features
- Feature selection (remove low-importance)
- Balance classes with SMOTE

### Phase 3: Advanced Models (Future)
- Ensemble methods
- Graph Neural Networks (GNN)
- Deep learning (if dataset grows to 1000+)

---

## 🚨 Red Flags to Watch For

### During Training
❌ AUC > 0.90 → Data leakage still present
❌ Perfect train accuracy → Overfitting
❌ Complexity features in top 10 → Learning dataset signature

### After Training
❌ All manual contracts predicted safe → Model too conservative
❌ All manual contracts predicted vulnerable → Model too aggressive
❌ Can't explain why model predicts vulnerability → Black box problem

---

## ✅ Definition of Success

A successful model should:
1. ✅ Achieve AUC 0.65-0.80 on cross-validation
2. ✅ Have interpretable feature importance
3. ✅ Generalize to unlabeled data
4. ✅ Help prioritize manual audits
5. ✅ Pass adversarial validation (AUC ~0.5)

**This is NOT about achieving 99% accuracy!**
**It's about learning REAL vulnerability patterns!**
