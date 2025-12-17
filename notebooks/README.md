# Notebooks
Exploratory data analysis, model experiments.
**Start:** Day 3 (after dataset collection)
# ChainGuardian AI - Analysis Notebooks

## Active Notebooks (Week 1-2)

### Week 1: Feature Engineering
- `01_deep_eda.ipynb` - Deep exploratory data analysis
- `02_graph_features.ipynb` - Control flow graph extraction
- `03_feature_selection.ipynb` - Feature selection & engineering
- `04_custom_features.ipynb` - Domain-specific features

### Week 2: Advanced ML
- `05_class_imbalance.ipynb` - SMOTE, ADASYN, cost-sensitive learning
- `06_ensemble_methods.ipynb` - RF + XGBoost + LightGBM voting
- `07_shap_explainability.ipynb` - Model interpretability

## Data Sources
- Main dataset: `../data/chainguardian_features_clean.csv` (312 contracts)
- SmartBugs: `../data/smartbugs_curated/` (vulnerable contracts)

## Model Outputs
- Trained models: `../models/saved_models/`
- Vulnerability-specific: `../models/vulnerability_specific/`