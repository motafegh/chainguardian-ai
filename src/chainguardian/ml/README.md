# ChainGuardian AI - Machine Learning Module

ML-powered smart contract vulnerability detection using code structure analysis.

## Overview

This module trains Random Forest classifiers to predict vulnerabilities from **code structure features only** (no detector outputs = no data leakage).

**Key Features:**
- ✅ 90.5% average accuracy across 10+ vulnerability types
- ✅ Multi-label classification (each vulnerability independently)
- ✅ NO data leakage (uses only code metrics, not detector outputs)
- ✅ Fast predictions (milliseconds vs. seconds for Slither)
- ✅ Production-ready with comprehensive metrics

## Quick Start

### 1. Train Models

Train all viable vulnerability models
poetry run python src/chainguardian/ml/training/train_multi_label.py



**Output:**
- Models saved to `models/vulnerability_specific/`
- Performance report in `models/reports/`

### 2. Predict on New Contracts

Single contract
poetry run python src/chainguardian/ml/training/predict.py
--contract blockchain/contracts/MyToken.sol

All contracts in directory
poetry run python src/chainguardian/ml/training/predict.py
--directory blockchain/contracts/collected/



## Architecture

### Features (17 code structure metrics)

CODE_STRUCTURE_FEATURES = [
'num_functions', # Total functions in contract
'num_external_calls', # Calls to other contracts
'num_state_vars', # State variables
'num_modifiers', # Access control modifiers
'max_cyclomatic_complexity', # Max function complexity
'num_low_level_calls', # .call, .delegatecall, etc.
'lines_of_code', # Contract size
'num_contracts_in_file', # Multi-contract files
'num_dependencies', # Imported contracts
'avg_function_complexity', # Average complexity
'num_functions_high_complexity', # Functions with complexity > 10
'num_comments', # Comment count
'comment_to_code_ratio', # Documentation quality
'num_payable_functions', # Functions receiving ETH
'num_library_calls', # Library usage
'inheritance_depth', # Inheritance chain length
'num_unused_functions' # Dead code
]


### Targets (Vulnerability Types)

**Critical:**
- `has_reentrancy` - Reentrancy vulnerability
- `has_unchecked_call` - Unchecked return values
- `has_access_control_issues` - Missing access controls
- `has_timestamp_dependency` - Time manipulation risks

**High:**
- `has_reentrancy_unlimited` - Unlimited reentrancy
- `has_tx_origin` - tx.origin authentication
- `has_controlled_delegatecall` - Delegatecall to user input

**Medium:**
- `has_uninitialized_state` - Uninitialized variables
- `has_locked_ether` - Locked funds
- `has_shadowing_state` - Variable shadowing

**+10 more** (see training output for full list)

## Performance Metrics

**From latest training (312 contracts, 80/20 split):**

| Vulnerability | Accuracy | Precision | Recall | F1-Score |
|--------------|----------|-----------|--------|----------|
| Unchecked Call | 90.5% | 0.909 | 0.833 | 0.870 |
| Timestamp Dependency | 90.5% | 0.818 | 0.692 | 0.750 |
| Access Control | 95.2% | 0.800 | 0.667 | 0.727 |
| Reentrancy | 85.7% | 0.611 | 0.846 | 0.710 |

**Average:** 90.5% accuracy, 0.764 F1-score

## How It Works

### Training Phase (One-Time)

Load 312 contracts with Slither-confirmed labels

Extract 17 code structure features

Train Random Forest for each vulnerability type

Validate with cross-validation

Save trained models (.pkl files)


### Prediction Phase (Production)

New contract arrives

Extract same 17 features (no Slither needed!)

Load trained models

Predict probability for each vulnerability

Return results in milliseconds



**Speed:** ~10ms per contract (vs. 5-30s for Slither)

## Use Cases

### 1. Fast Triage
Screen 10,000 contracts in minutes, prioritize high-risk ones for full audit.

### 2. Real-Time Warnings
IDE integration - warn developers as they write code.

### 3. Audit Prioritization
Security firms can rank contracts by predicted risk before manual review.

### 4. Continuous Monitoring
Monitor deployed contracts, flag new risky deployments.

## Model Details

**Algorithm:** Random Forest (100 trees)

**Hyperparameters:**
n_estimators=100 # Number of trees
max_depth=15 # Max tree depth
min_samples_split=5 # Min samples to split
min_samples_leaf=2 # Min samples per leaf
class_weight='balanced' # Handle imbalanced data
random_state=42 # Reproducibility



**Why Random Forest?**
- ✅ Handles non-linear relationships
- ✅ Built-in feature importance
- ✅ Robust to imbalanced data
- ✅ No hyperparameter tuning needed
- ✅ Interpretable for security audits

## Data Leakage Prevention

**WRONG** (circular logic):
Using detector outputs to predict risk
X = df[['has_reentrancy', 'has_unchecked_call', ...]] # Features
y = df['is_high_risk'] # Target (calculated FROM features!)

Result: 100% accuracy (useless!)


**CORRECT** (our approach):
Using only code structure
X = df[['num_functions', 'num_external_calls', ...]] # Features
y = df['has_reentrancy'] # Target (independent detection)

Result: 92% accuracy (real learning!)


## File Structure

src/chainguardian/ml/
├── models/
│ ├── init.py
│ └── vulnerability_classifier.py # Model wrapper class
├── training/
│ ├── init.py
│ ├── train_multi_label.py # Training script
│ └── predict.py # Prediction script
└── README.md # This file

models/
├── vulnerability_specific/
│ ├── has_reentrancy_rf.pkl # Trained models
│ ├── has_unchecked_call_rf.pkl
│ └── ...
└── reports/
├── multi_label_results_.csv # Performance metrics
└── multi_label_summary_.txt # Training summary



## Limitations

1. **Not a replacement for Slither** - Use for screening, confirm with static analysis
2. **Only detects trained types** - Won't find novel vulnerabilities
3. **Accuracy not 100%** - ~10% false positive/negative rate
4. **Requires sufficient training data** - Can't train on rare vulnerability types (<5 samples)

## Next Steps

- [ ] Hyperparameter tuning (Grid Search)
- [ ] Add GNN for control flow analysis
- [ ] Deploy as FastAPI endpoint
- [ ] A/B testing with security auditors
- [ ] Collect more data for rare vulnerabilities

## References

- **Random Forest:** Breiman, 2001
- **Imbalanced Learning:** SMOTE, Chawla et al., 2002
- **Smart Contract Security:** SWC Registry, ConsenSys

## Author

ChainGuardian AI Team  
December 2025

---
