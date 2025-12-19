# Scripts Organization

## Directory Structure

### 1_setup/ - One-time setup
Run these ONCE when setting up the project:
- `create_tables.py` - Create PostgreSQL database tables
- `test_db_connection.py` - Verify database connection

### 2_collection/ - Data collection & import
Run these to build your dataset:
1. `rekt_news_collector.py` - Generate vulnerable contracts metadata
2. `audited_defi_collector.py` - Generate safe contracts metadata
3. `trail_of_bits_collector.py` - Copy Trail of Bits contracts
4. `swc_registry_collector.py` - Copy SWC registry contracts
5. `master_collector.py` - Fetch source code from Etherscan
6. `import_smartbugs_to_db.py` - Import SmartBugs dataset
7. `import_openzeppelin_with_mocks.py` - Import OpenZeppelin contracts
8. `import_production_dataset.py` - Import production vulnerable/safe

### 3_training/ - ML training & evaluation
Run these for model training:
- `train_baseline.py` - Train baseline ML models
- `predict.py` - Make predictions on unlabeled data

### 9_utils/ - Utility scripts
Helper scripts:
- `verify_dataset.py` - Check dataset quality
- `check_duplicates.py` - Find duplicate contracts
- `verify_data_integrity.py` - Validate data integrity
