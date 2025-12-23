# 🌳 ChainGuardian AI - Final Project Structure

**Status:** Production Ready  
**Date:** December 22, 2024

---

## 📁 Root Directory
```
chainguardian-ai/
├── README.md                    # Project overview
├── pyproject.toml              # Poetry dependencies
├── poetry.lock                 # Locked dependencies
├── cleanup_to_archive.sh       # Cleanup script
└── .gitignore                  # Git ignore rules
```

---

## 🗄️ Data & Artifacts
```
├── data/                       # Datasets & exports
│   ├── training_dataset_20251222.csv      # ML-ready dataset (429 contracts)
│   ├── db_verification_summary.json       # Database health report
│   └── custom_contract_predictions.csv    # Test results (when created)
│
├── models/                     # Trained models (PRODUCTION)
│   ├── production_model.pkl              # XGBoost calibrated (8.2 MB)
│   ├── production_scaler.pkl             # RobustScaler (12 KB)
│   ├── feature_metadata.json             # 91 feature names + metrics
│   ├── feature_importance_20251222_1341.csv
│   └── backup_20251222_1425/             # Latest model backup
│       ├── production_model.pkl
│       └── production_scaler.pkl
│
├── mlruns/                     # MLflow experiment tracking
│   ├── 1/                     # Experiment: smart_contract_robust_calibrated
│   ├── 2/                     # Experiment: chainguardian_robust_calibrated  
│   └── 3/                     # Experiment: chainguardian_production ⭐
│       ├── 15a97fc15ae34dc8a9b5c4d7504c1be5/   # Latest run
│       │   └── artifacts/
│       │       ├── model/                      # Saved model
│       │       ├── calibration_curve.png
│       │       ├── confusion_matrix.png
│       │       └── roc_curve.png
│       └── models/
│
├── reports/                    # Analysis reports
│   ├── feature_importance.csv
│   ├── model_comparison.csv
│   ├── hybrid_optimization_production.csv
│   ├── hybrid_adversarial_results.csv
│   ├── hybrid_cei_results.csv
│   ├── hybrid_optimization_grid_search.csv
│   ├── hyperparameter_search.csv
│   └── figures/               # Visualizations (if any)
│
└── logs/                       # Application logs
    └── (empty after cleanup)
```

---

## 📜 Scripts (Production)
```
scripts/
├── 1_setup/                    # Database initialization
│   ├── create_tables.py                 # Create schema
│   ├── check_db_schema.py               # Verify schema
│   ├── apply_semantic_schema.py         # Add CEI features
│   └── update_schema_semantic.sql       # Schema migration
│
├── 2_collection/               # Data collection pipelines
│   ├── download_smartbugs_curated.py    # SmartBugs dataset
│   ├── import_openzeppelin_with_mocks.py # OpenZeppelin contracts
│   ├── trail_of_bits_collector.py       # Trail of Bits examples
│   ├── import_production_dataset.py     # Production contracts
│   ├── master_collector.py              # Orchestrator
│   └── (other collectors for future use)
│
├── 3_training/                 # ML Training ⭐ PRODUCTION
│   ├── train_production_model.py        # ONE SCRIPT - Main training
│   └── test_custom_contracts.py         # Test on .sol files (to create)
│
├── 4_fixes/                    # Debugging & optimization
│   ├── hyperparameter_search.py
│   ├── analyze_tradeoff.py
│   └── (diagnostic scripts)
│
└── 9_utils/                    # Utilities ⭐ ESSENTIAL
    ├── database_info.py                 # Quick database stats
    ├── verify_database_standalone.py    # Full database validation
    ├── quick_db_queries.sh              # Bash queries
    ├── verify_data_integrity.py
    └── verify_dataset.py
```

---

## 🐍 Source Code (Production)
```
src/chainguardian/
├── __init__.py
│
├── database/                   # Database layer
│   ├── __init__.py
│   ├── manager.py             # DatabaseManager (production)
│   └── models.py              # SQLAlchemy models
│
├── feature_extraction/         # Feature engineering ⭐ CORE
│   ├── __init__.py
│   ├── pipeline.py                      # Main extraction pipeline
│   ├── contract_analyzer.py             # Slither integration (58 features)
│   ├── ast_analyzer.py                  # AST parsing (19 features)
│   ├── graph_extractor.py               # CFG/CG/DFG (25 features)
│   ├── semantic_analyzer.py ⭐          # CEI detection (8 features)
│   └── layer2/
│       └── base_tool_parser.py
│
├── ml/                         # Machine Learning
│   ├── __init__.py
│   └── models/
│       ├── __init__.py
│       └── hybrid_predictor.py ⭐       # Production predictor
│
├── mlops/                      # MLOps utilities
│   ├── __init__.py
│   └── experiment_tracker.py            # MLflow wrapper
│
├── data_collection/            # Data collection utilities
│   ├── __init__.py
│   ├── collectors/
│   │   ├── base.py
│   │   ├── coingecko.py
│   │   ├── defi_llama.py
│   │   └── (other collectors)
│   └── strategies/
│       └── stratified_sampling.py
│
├── api/                        # API (future)
│   └── __init__.py
│
└── llm/                        # LLM (future)
    ├── __init__.py
    └── generation/
        └── __init__.py
```

---

## 📚 Documentation
```
docs/
├── DATABASE_COMPLETE_REFERENCE.md  ⭐   # Full database guide
├── FINAL_PROJECT_STRUCTURE.md      ⭐   # This file
├── PROJECT_PROGRESS.md                  # Development history (to create)
├── api/                                 # API docs (future)
└── learning_notes/                      # Study notes
    └── LEARNING_NOTES_WEEK1.md         # Week 1 concepts (to create)
```

---

## 🧪 Tests
```
tests/
├── __init__.py
├── integration/
│   ├── __init__.py
│   └── test_collection_only.py
└── unit/
    └── __init__.py
```

---

## 🧪 Test Contracts
```
test_contracts/                 # 25 .sol files for testing
├── 01_super_simple_safe.sol
├── 02_obvious_reentrancy.sol
├── 03_complex_but_safe.sol
├── ... (22 more)
└── 25_gas_optimization_extreme.sol
```

---

## 📦 Archive (Old Experiments)
```
archive/
├── experimental_20251221/      # Week 1 experiments
├── training_experiments_dec19/ # Early training attempts
├── models_dec19/              # Old models
├── notebooks_old/             # Old notebooks
└── cleanup_20251222/          # Today's cleanup
    ├── scripts/               # Old training scripts
    ├── models/                # Old model backups
    ├── reports/               # Experimental reports
    ├── notebooks/             # Old notebooks
    ├── logs/                  # Old logs
    └── backups/               # SQL backups
```

---

## 🎯 KEY FILES BY PURPOSE

### 🚀 To Train Model
```bash
poetry run python scripts/3_training/train_production_model.py
```

### 🧪 To Test Model
```bash
poetry run python scripts/3_training/test_custom_contracts.py
```

### �� To Verify Database
```bash
poetry run python scripts/9_utils/database_info.py
# or
bash scripts/9_utils/quick_db_queries.sh
```

### 📊 To View Experiments
```bash
poetry run mlflow ui --host 0.0.0.0 --port 5000
# Visit: http://localhost:5000
```

### 🗄️ To Connect Database
```python
from sqlalchemy import create_engine
engine = create_engine("postgresql://chainguardian_user:2220128@localhost:5432/chainguardian")
```

### 🤖 To Use Model
```python
import joblib
model = joblib.load("models/production_model.pkl")
scaler = joblib.load("models/production_scaler.pkl")
```

---

## 📊 File Counts
```
Production Files:
├── Source code:        ~40 Python files
├── Scripts:           ~35 Python + bash files
├── Models:             3 files (model + scaler + metadata)
├── MLflow artifacts:  ~50 files
├── Documentation:      5 markdown files
└── Test contracts:    25 Solidity files

Total: ~160 production files

Archived: ~80 experimental files
```

---

## 🎯 Next Development Phases

### Week 2: Deployment
```
├── scripts/5_deployment/
│   ├── build_fastapi_service.py
│   ├── create_dockerfile.py
│   └── setup_monitoring.py
└── Update: src/chainguardian/api/
```

### Week 3: LLM Integration
```
├── scripts/6_llm/
│   ├── collect_exploits.py
│   ├── create_rag_index.py
│   └── fine_tune_llama.py
└── Update: src/chainguardian/llm/
```

---

## ✅ Verification Commands
```bash
# Check structure
tree -L 2 -I '__pycache__|*.pyc|.venv|data|mlruns|archive'

# Count production files
find scripts src -name "*.py" -type f | grep -v __pycache__ | wc -l

# Check model files
ls -lh models/production*

# Verify database
poetry run python scripts/9_utils/database_info.py

# Test imports
python -c "from chainguardian.ml.models.hybrid_predictor import HybridPredictor; print('✅ OK')"
```

---

**Project Status:** ✅ Clean, organized, production-ready
**Last Cleanup:** December 22, 2024
