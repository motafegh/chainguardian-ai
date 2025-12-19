# Data Organization

## Directory Structure

### raw/ - Raw source datasets
Curated datasets cloned from external sources:
- `smartbugs_curated/` - Academic vulnerable contracts
- `openzeppelin-contracts/` - Battle-tested safe contracts  
- `trail_of_bits/` - Trail of Bits vulnerable examples
- `swc_registry/` - SWC vulnerability examples

DO NOT edit these - they are source data!

### processed/ - Feature-extracted datasets
Clean, ML-ready datasets:
- `production_dataset.csv` - Final dataset for training
- `training_labeled.csv` - Known labels only
- `prediction_unlabeled.csv` - Unknown labels for prediction

### metadata/ - Collection metadata
Metadata from collection runs:
- `vulnerable_sources/` - Vulnerable contract metadata
- `safe_sources/` - Safe contract metadata
- `production_runs/` - Etherscan scraping outputs
