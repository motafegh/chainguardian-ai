# ChainGuardian AI - Complete Workflow

## 🎯 Goal
Build production-grade ML model for smart contract vulnerability detection using semi-supervised learning.

---

## 📋 PHASE 1: Setup (Run Once)

### 1. Database Setup
```bash
# Create PostgreSQL tables
poetry run python scripts/1_setup/create_tables.py

# Verify connection
poetry run python scripts/1_setup/test_db_connection.py
```

---

## 📋 PHASE 2: Data Collection

### 2.1 Clone External Datasets (One-time)
```bash
cd data

# SmartBugs (already done)
# Located: data/smartbugs_curated/

# OpenZeppelin (already done)
# Located: data/safe_contracts/openzeppelin-contracts/

# Trail of Bits (already done)
cd vulnerable_complex
git clone https://github.com/crytic/not-so-smart-contracts.git trail_of_bits

# SWC Registry (already done)
git clone https://github.com/SmartContractSecurity/SWC-registry.git swc_registry

cd ~/projects/chainguardian-ai
```

### 2.2 Import Known Labels to Database
```bash
# Import SmartBugs (vulnerable contracts)
poetry run python scripts/2_collection/import_smartbugs_to_db.py
# Expected: ~140 vulnerable contracts

# Import OpenZeppelin (safe contracts)
poetry run python scripts/2_collection/import_openzeppelin_with_mocks.py
# Expected: ~247 safe contracts
```

### 2.3 Collect Production Contracts
```bash
# Step 1: Generate metadata for vulnerable contracts
poetry run python scripts/2_collection/rekt_news_collector.py
# Output: data/metadata/vulnerable_sources/rekt_news_exploits.json

# Step 2: Generate metadata for safe contracts
poetry run python scripts/2_collection/audited_defi_collector.py
# Output: data/metadata/safe_sources/audited_defi_protocols.json

# Step 3: Collect verified vulnerable examples
poetry run python scripts/2_collection/trail_of_bits_collector.py
poetry run python scripts/2_collection/swc_registry_collector.py

# Step 4: Fetch source code from Etherscan
poetry run python scripts/2_collection/master_collector.py
# Fetches: Real DeFi hacks + Audited protocols

# Step 5: Import all to database
poetry run python scripts/2_collection/import_production_dataset.py
# Extracts features and saves to database
```

### 2.4 Verify Dataset
```bash
# Check dataset quality
poetry run python scripts/9_utils/verify_dataset.py

# Expected output:
# - Vulnerable: ~164 (SmartBugs + production)
# - Safe: ~252 (OpenZeppelin + production)
# - Total: ~416 labeled contracts
```

---

## 📋 PHASE 3: Semi-Supervised Learning

### 3.1 Export Training & Prediction Sets
```bash
poetry run python << 'EOF'
from chainguardian.database.manager import DatabaseManager
import pandas as pd
import numpy as np

db = DatabaseManager()
df = db.get_all_features()
df_clean = df[df['failure_reason'].isna()].copy()

# Create labels (ONLY for known ground truth)
df_clean['label'] = df_clean['data_source'].map({
    'smartbugs_curated': 1,
    'production_vulnerable': 1,
    'openzeppelin': 0,
    'production_safe': 0,
}).astype('float')

# Split labeled vs unlabeled
df_labeled = df_clean[df_clean['label'].notna()].copy()
df_unlabeled = df_clean[df_clean['label'].isna()].copy()

# Convert booleans
for df_temp in [df_labeled, df_unlabeled]:
    bool_cols = df_temp.select_dtypes(include=['bool']).columns
    for col in bool_cols:
        df_temp[col] = df_temp[col].astype(int)
    if 'contract_complexity_category' in df_temp.columns:
        df_temp['contract_complexity_category'] = df_temp['contract_complexity_category'].map(
            {'simple': 1, 'moderate': 2, 'complex': 3, 'critical': 4}
        ).fillna(2)

# Save
df_labeled.to_csv('data/training_labeled.csv', index=False)
df_unlabeled.to_csv('data/prediction_unlabeled.csv', index=False)

print(f"✅ Labeled: {len(df_labeled)} contracts")
print(f"✅ Unlabeled: {len(df_unlabeled)} contracts")
