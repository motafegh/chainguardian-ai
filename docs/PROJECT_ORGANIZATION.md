# ChainGuardian AI - Project Organization

**Date**: 2025-12-31
**Status**: ✅ Fully Organized

---

## 📁 Complete Project Structure

```
chainguardian-ai/
├── 📦 SOURCE CODE
│   └── src/chainguardian/
│       ├── feature_extraction/      # ✨ Tier-based extraction system (NEW)
│       ├── database/                # PostgreSQL operations
│       ├── ml/                      # ML models & training
│       ├── api/                     # FastAPI application
│       ├── data_collection/         # Dataset collection
│       ├── llm/                     # LLM integration
│       ├── mlops/                   # MLOps & monitoring
│       └── monitoring/              # Metrics & observability
│
├── 🔧 SCRIPTS
│   └── scripts/
│       ├── build_database.py        # ✨ NEW: Main database builder
│       ├── 1_setup/                 # Database setup scripts
│       ├── 2_collection/            # Data collection scripts
│       ├── 3_training/              # ML training scripts
│       ├── 4_fixes/                 # Bug fix scripts
│       ├── 9_utils/                 # Utility scripts
│       ├── data_quality/            # Quality control
│       └── ml_production/           # Production ML tools
│
├── 🧪 TESTS
│   └── tests/
│       ├── unit/                    # Unit tests
│       ├── integration/             # Integration tests
│       ├── manual_tests/            # ✨ NEW: Manual verification
│       └── fixtures/                # ✨ NEW: Test data
│
├── 📚 DOCUMENTATION
│   ├── 📖 Root Documentation (keep in root)
│   │   ├── README.md                # Project overview
│   │   ├── Full_RoadMap.md          # Development roadmap
│   │   ├── STRUCTURE.md             # Project structure
│   │   └── WORKFLOW.md              # Development workflow
│   │
│   └── docs/
│       ├── 📄 Current Documentation
│       │   ├── BUILD_COMPARISON.md                 # ✨ NEW: Build analysis
│       │   ├── DATABASE_AND_CODE_SUMMARY.md        # ✨ NEW: Complete summary
│       │   ├── FEATURE_EXTRACTION_FIXES.md         # ✨ NEW: Fix details
│       │   ├── FINAL_SOURCE_CODE_STRUCTURE.md      # ✨ NEW: Code structure
│       │   ├── PROJECT_ORGANIZATION.md             # ✨ NEW: This file
│       │   ├── TEST_SUITE_DOCUMENTATION.md         # Test documentation
│       │   └── ml_training_pipeline_documentation.md # ML guide
│       │
│       └── archive/
│           ├── DATABASE_BUILD_GUIDE.md
│           ├── DEPLOYMENT_READY.md
│           ├── FINAL_DEPLOYMENT_SUMMARY.md
│           ├── IMPLEMENTATION_SUMMARY.md
│           ├── PRODUCTION_DEPLOYMENT_COMPLETE.md
│           ├── PRODUCTION_TRIANGLE_LAYERS_4-7-10.md
│           ├── SESSION_REPORT_20251221.md
│           └── plan-for-new-features-extraction.md
│
├── 📝 LOGS & STATS
│   ├── logs/builds/                 # ✨ NEW: Build logs
│   │   ├── database_build_*.log
│   │   ├── build.log
│   │   └── test_*.log
│   │
│   ├── backups/                     # ✨ NEW: Old build stats
│   │   ├── database_build_stats_20251230_211118.json
│   │   └── database_build_stats_20251230_213815.json
│   │
│   └── database_build_stats_20251231_000135.json  # ✅ Latest (in root)
│
├── 🗄️ DATA & MODELS
│   ├── blockchain/                  # Contract datasets
│   │   ├── SolidiFI-benchmark/
│   │   ├── solidity-by-example.github.io/
│   │   ├── damn-vulnerable-defi/
│   │   ├── compound-protocol/
│   │   └── contracts/
│   │
│   ├── data/                        # Generated datasets
│   ├── models/                      # Trained models
│   └── outputs/                     # Analysis outputs
│
├── ⚙️ CONFIGURATION
│   ├── pyproject.toml               # Poetry dependencies
│   ├── Dockerfile                   # Docker config
│   ├── docker-compose.yml           # Docker Compose
│   ├── railway.json                 # Railway deployment
│   ├── package.json                 # Node.js (if needed)
│   └── .env.example                 # Environment variables template
│
└── 📦 ARCHIVES
    ├── archive/                     # Old code (from cleanup_20251222)
    ├── archived_tests/              # Old test files
    └── EIPs/                        # Ethereum Improvement Proposals
```

---

## 📊 File Count Summary

| Category | Location | Files | Purpose |
|----------|----------|-------|---------|
| **Source Code** | `src/chainguardian/` | ~60 files | Core application |
| **Scripts** | `scripts/` | ~100 files | Automation & utilities |
| **Tests** | `tests/` | ~20 files | Unit & integration tests |
| **Documentation** | `docs/` | 15 files | Current documentation |
| **Archived Docs** | `docs/archive/` | 8 files | Historical documentation |
| **Logs** | `logs/builds/` | 11 files | Build logs |
| **Config** | Root | 6 files | Project configuration |
| **Main Docs** | Root | 4 files | README, roadmap, etc. |

---

## 🗂️ Key Files & Their Locations

### Scripts (scripts/)

#### Main Database Builder ✨ NEW
```
scripts/build_database.py
```
**Purpose**: Build production database from contract datasets
**Usage**: `poetry run python scripts/build_database.py`

#### Organized by Category
```
scripts/
├── 1_setup/              # Database initialization
│   ├── setup_database.py
│   ├── create_tables.py
│   └── apply_semantic_schema.py
│
├── 2_collection/         # Data collection
│   ├── master_collector.py
│   ├── download_smartbugs_curated.py
│   └── import_openzeppelin_with_mocks.py
│
├── 3_training/           # ML training
│   ├── train_production_v7.py
│   ├── test_hybrid_predictor_v7.py
│   └── validate_hybrid_integration.py
│
├── 4_fixes/              # Bug fixes
│   ├── fix_pipeline_contract_detection.py
│   └── hyperparameter_search.py
│
├── 9_utils/              # Utilities
│   ├── verify_database_standalone.py
│   └── inspect_data.py
│
└── data_quality/         # Quality control
    ├── data_quality_report_v4.py
    └── database_quality_control.py
```

### Documentation (docs/)

#### Current Documentation
```
docs/
├── BUILD_COMPARISON.md                  # Before/after build analysis
├── DATABASE_AND_CODE_SUMMARY.md         # Complete overview
├── FEATURE_EXTRACTION_FIXES.md          # Technical fixes
├── FINAL_SOURCE_CODE_STRUCTURE.md       # Code structure
├── PROJECT_ORGANIZATION.md              # This file
├── TEST_SUITE_DOCUMENTATION.md          # Test guide
└── ml_training_pipeline_documentation.md # ML training
```

#### Archived Documentation
```
docs/archive/
├── DATABASE_BUILD_GUIDE.md              # Old build guide
├── DEPLOYMENT_READY.md                  # Deployment notes
├── FINAL_DEPLOYMENT_SUMMARY.md          # Old summary
├── IMPLEMENTATION_SUMMARY.md            # Implementation notes
├── PRODUCTION_DEPLOYMENT_COMPLETE.md    # Deployment complete
├── PRODUCTION_TRIANGLE_LAYERS_4-7-10.md # Architecture docs
├── SESSION_REPORT_20251221.md           # Session notes
└── plan-for-new-features-extraction.md  # Planning doc
```

### Tests (tests/)

```
tests/
├── unit/                   # Unit tests
│   ├── test_pipeline.py            # Feature extraction tests
│   ├── test_database.py            # Database tests
│   └── test_*.py                   # Other unit tests
│
├── integration/            # Integration tests
│   └── test_database_integration.py
│
├── manual_tests/           # ✨ NEW: Manual verification
│   ├── test_new_extraction.py
│   ├── test_multi_contract.py
│   └── test_real_contracts.py
│
└── fixtures/               # ✨ NEW: Test data
    ├── test_contract_simple.sol
    └── test_results_*.csv
```

### Logs & Stats

```
logs/builds/                # ✨ NEW: All build logs
├── database_build_20251230_*.log
├── build.log
└── test_*.log

backups/                    # ✨ NEW: Old build stats
├── database_build_stats_20251230_211118.json
└── database_build_stats_20251230_213815.json

Root:
└── database_build_stats_20251231_000135.json  # Latest stats
```

---

## 📝 .gitignore Updates

Add the following to `.gitignore` to keep repo clean:

```gitignore
# Logs
logs/
*.log

# Build stats (keep only latest in git)
database_build_stats_*.json
!database_build_stats_20251231_000135.json

# Backups
backups/

# Test outputs
test_results_*.csv

# Database
*.db
*.sqlite

# Python
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/

# Virtual environments
.venv/
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment variables
.env
.env.local

# Temporary files
/tmp/
*.tmp
```

---

## ✅ Organization Rules

### ✓ Keep in Root
- **Main documentation**: README.md, roadmap, structure guide
- **Configuration files**: pyproject.toml, Dockerfile, railway.json
- **Latest build stats**: Only the most recent `database_build_stats_*.json`

### ✓ Move to docs/
- **Current documentation**: All new comprehensive guides
- **Archive**: Old/outdated documentation

### ✓ Move to scripts/
- **Executable scripts**: Database builders, collectors, trainers
- **Organized by category**: Use numbered folders (1_setup, 2_collection, etc.)

### ✓ Move to logs/builds/
- **All log files**: Build logs, test logs, etc.
- **Not tracked in git**: Add to .gitignore

### ✓ Move to backups/
- **Old build statistics**: Previous `database_build_stats_*.json`
- **Not tracked in git**: Add to .gitignore

### ✓ Move to tests/
- **Test scripts**: Unit, integration, manual tests
- **Test data**: Fixtures and expected outputs

---

## 🎯 Benefits of This Organization

### 1. **Clear Separation of Concerns**
- Source code in `src/`
- Scripts in `scripts/`
- Tests in `tests/`
- Documentation in `docs/`

### 2. **Easy Navigation**
- Numbered script folders (1, 2, 3, 4, 9) show execution order
- Archived docs separated from current docs
- Logs isolated in dedicated folder

### 3. **Git-Friendly**
- Clean root directory
- .gitignore properly configured
- Only essential files tracked

### 4. **Scalable**
- Easy to add new scripts in appropriate category
- Documentation stays organized
- Logs don't clutter the repo

### 5. **Professional**
- Industry-standard structure
- Easy for new developers to understand
- Clear documentation

---

## 🚀 Quick Access Commands

### Run Main Database Builder
```bash
poetry run python scripts/build_database.py
```

### Run Tests
```bash
poetry run pytest tests/
```

### Check Database Quality
```bash
poetry run python scripts/data_quality/data_quality_report_v4.py
```

### Train ML Model
```bash
poetry run python scripts/3_training/train_production_v7.py
```

### View Latest Build Stats
```bash
cat database_build_stats_20251231_000135.json | python3 -m json.tool
```

---

## 📊 Organization Checklist

- [x] Source code in `src/chainguardian/`
- [x] Scripts organized in `scripts/` with categories
- [x] Tests organized in `tests/` (unit, integration, manual)
- [x] Current documentation in `docs/`
- [x] Archived documentation in `docs/archive/`
- [x] Logs in `logs/builds/`
- [x] Backups in `backups/`
- [x] Only essential files in root
- [x] .gitignore updated
- [x] README and main docs in root
- [x] Latest build stats in root

---

## 📝 Notes

1. **Scripts are well-organized**: The existing `scripts/` directory already had a good structure with numbered categories. We added `build_database.py` to it.

2. **Documentation is comprehensive**: We created 5 new documentation files explaining all the changes, fixes, and current state.

3. **Tests are properly structured**: Manual tests and fixtures now have dedicated folders.

4. **Logs are isolated**: All build logs are in `logs/builds/`, keeping the root clean.

5. **Archives are preserved**: Old documentation is in `docs/archive/` for historical reference, not deleted.

---

**Last Updated**: 2025-12-31
**Organized By**: Claude Code
**Status**: ✅ Complete and Production-Ready
