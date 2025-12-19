# ChainGuardian AI - Data

## Active Datasets

### Main Dataset
- `chainguardian_features_clean.csv` - **312 contracts with 65 columns**
  - 25 vulnerability labels
  - ~40 features (will expand to 45+ in Week 1)
  - Ready for ML training

### SmartBugs Curated
- `smartbugs_curated/dataset/` - Ground truth vulnerable contracts
  - reentrancy/
  - access_control/
  - arithmetic/
  - unchecked_low_level_calls/
  - etc.

### Contract Storage
- `smartbugs_contracts/` - Cached .sol files (2,384 contracts)

## Archived Data
- Old datasets: `../archive/old_data/`
- Backups: `../archive/backups/`