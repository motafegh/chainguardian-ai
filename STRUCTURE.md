# Project Structure

## Core Directories
```
src/chainguardian/          - Main application code
├── data_collection/        - Contract collection pipelines
├── feature_extraction/     - Feature extraction (Slither, AST)
├── database/               - Database management
└── ml/                     - Machine learning (future)

scripts/                    - Utility scripts
├── database/               - Database setup & queries
├── data/                   - Data import & analysis
├── testing/                - Test scripts
└── old/                    - Archived scripts

data/                       - Data files
├── smartbugs_curated/      - SmartBugs dataset
├── smartbugs_contracts/    - Downloaded contracts
└── *.csv                   - Exported datasets

logs/                       - Application logs
models/                     - Saved ML models
cache/                      - Cache files
blockchain/contracts/       - Collected smart contracts
docs/                       - Documentation
Learning-files/             - Personal notes
notebooks/                  - Jupyter notebooks
tests/                      - Unit & integration tests
```

## Running Scripts

### Database
```bash
poetry run python scripts/database/create_tables.py
poetry run python scripts/database/query_database.py
```

### Data Import
```bash
poetry run python scripts/data/download_smartbugs_curated.py
poetry run python scripts/data/import_smartbugs_to_db.py
poetry run python scripts/data/analyze_dataset.py
```

### Testing
```bash
poetry run python scripts/testing/test_pipeline_with_db.py
```
