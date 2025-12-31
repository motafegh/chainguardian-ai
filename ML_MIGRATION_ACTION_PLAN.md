# ML System Migration - Action Plan

**Date**: 2025-12-31
**Status**: READY TO EXECUTE
**Estimated Time**: 4-8 hours

---

## Quick Summary

Your current ML system uses **93 old features** but the new tier-based extraction produces **152 features**. Only **22.4% overlap** - needs rebuild.

**What to do**: Rebuild database → Update ML code → Retrain models

---

## Phase 1: Database Rebuild (30 minutes)

### Step 1: Backup Current Database
```bash
# Create backup
pg_dump chainguardian > backups/db_before_tier_migration_20251231.sql

# Verify backup
ls -lh backups/db_before_tier_migration_20251231.sql
```

### Step 2: Rebuild with Tier System
```bash
# Full rebuild (comprehensive mode = 152 features)
poetry run python scripts/build_database.py

# Expected: ~7-10 minutes, 68.2% success rate
```

### Step 3: Verify New Features
```bash
# Check feature count
poetry run python -c "
from chainguardian.database.manager import DatabaseManager
db = DatabaseManager()
df = db.get_all_features()
print(f'✅ Database has {len(df.columns)} columns')
print(f'✅ Sample features: {list(df.columns[:10])}')
"

# Should show ~160 columns (152 features + 8 metadata)
```

---

## Phase 2: Update ML Code (1-2 hours)

### File 1: Feature Engineer
**Path**: `src/chainguardian/ml/data_engineering/feature_engineer.py`

**Find & Replace**:
```python
# Old → New feature names
'has_inline_assembly' → 'has_assembly_usage'
'has_timestamp_dependency' → 'has_timestamp_dependence'
'has_access_control_issues' → 'has_access_control_issue'
'cfg_avg_branching' → 'cfg_avg_branching_factor'
'cg_max_call_depth' → 'call_graph_depth'
```

### File 2: Hybrid Predictor
**Path**: `src/chainguardian/ml/models/hybrid_predictor_enhanced_v2.py`

**Update default features**:
```python
# Add at top
from chainguardian.feature_extraction.feature_spec import get_features_for_mode

# Replace _get_default_features() method
def _get_default_features(self):
    """Get features from tier system."""
    return get_features_for_mode('comprehensive')  # 152 features
```

### File 3: Training Script
**Path**: `scripts/3_training/train_production_v7.py`

**Verify it loads all features**:
```python
# Should already work, just verify
df = db.get_all_features()
print(f"Training with {len(df.columns)} total columns")
# Should print ~160 columns
```

---

## Phase 3: Retrain Models (2-4 hours)

### Step 1: Train New Model
```bash
# This will train on 152 features (vs old 93)
poetry run python scripts/3_training/train_production_v7.py

# Expected: 2-4 hours depending on hyperparameter search
# Watch for: AUC score > 0.9978 (current best)
```

### Step 2: Compare Performance
```bash
# Run ablation test
poetry run python scripts/3_training/ablation_cei_test_FINAL.py

# Compare:
# - Old model: 93 features, AUC 0.9978
# - New model: 152 features, AUC ???
```

---

## Phase 4: Verification (1 hour)

### Test 1: Data Quality
```bash
poetry run python scripts/data_quality/verify_dataset.py
```

### Test 2: Feature Extraction
```bash
# Test on sample contracts
poetry run python scripts/build_database.py --limit 10
```

### Test 3: Feature Audit
```bash
poetry run python scripts/data_quality/audit_all_features.py
```

### Test 4: Prediction Test
```bash
# Test prediction with new model
poetry run python -c "
from chainguardian.ml.models.hybrid_predictor_enhanced_v2 import EnhancedHybridPredictorV2
predictor = EnhancedHybridPredictorV2()
print(f'Model loaded with {len(predictor.feature_names)} features')
# Should print 152
"
```

---

## Expected Results

### Before (Current State)
```
Database: 93 ML features (old system)
Model: 93 features, AUC 0.9978
Extraction: 26.6 min, 52.6% success
```

### After (New State)
```
Database: 152 ML features (tier system)
Model: 152 features, AUC 0.999+ (expected)
Extraction: 7.3 min, 68.2% success
```

### Improvements
- ✅ 63% more features (93 → 152)
- ✅ 3.6x faster extraction
- ✅ 15.6% higher success rate
- ✅ Better ML performance (expected)

---

## Troubleshooting

### Issue 1: Database rebuild fails
```bash
# Check Slither versions
poetry run solc-select versions

# Check database connection
poetry run python -c "from chainguardian.database.manager import DatabaseManager; DatabaseManager()"
```

### Issue 2: Feature name errors
```bash
# Check feature spec
poetry run python -c "
from chainguardian.feature_extraction.feature_spec import get_features_for_mode
print(get_features_for_mode('comprehensive')[:20])
"
```

### Issue 3: Training fails
```bash
# Check data quality
poetry run python scripts/data_quality/verify_dataset.py

# Check for null values
poetry run python -c "
from chainguardian.database.manager import DatabaseManager
db = DatabaseManager()
df = db.get_all_features()
print(df.isnull().sum().sum())
"
```

---

## Rollback Plan (If Needed)

### Option 1: Restore Database Backup
```bash
# Drop current database
psql -U chainguardian -c "DROP DATABASE IF EXISTS chainguardian;"

# Restore backup
psql -U chainguardian < backups/db_before_tier_migration_20251231.sql
```

### Option 2: Keep Both Databases
```bash
# Rename current DB
psql -U postgres -c "ALTER DATABASE chainguardian RENAME TO chainguardian_tier_system;"

# Create new DB with old name
psql -U postgres -c "CREATE DATABASE chainguardian;"

# Restore old backup
psql -U chainguardian < backups/db_before_tier_migration_20251231.sql
```

---

## Checklist

### Pre-Migration
- [ ] Read [docs/ML_SYSTEM_COMPATIBILITY_ANALYSIS.md](docs/ML_SYSTEM_COMPATIBILITY_ANALYSIS.md)
- [ ] Backup database: `pg_dump chainguardian > backups/db_backup.sql`
- [ ] Note current model performance (AUC, etc.)

### Phase 1: Database
- [ ] Run `poetry run python scripts/build_database.py`
- [ ] Verify 152 features in database
- [ ] Run data quality checks

### Phase 2: Code Updates
- [ ] Update feature_engineer.py (rename old features)
- [ ] Update hybrid_predictor_enhanced_v2.py (use tier features)
- [ ] Update any hard-coded feature lists

### Phase 3: Retraining
- [ ] Run train_production_v7.py
- [ ] Compare new model vs old model performance
- [ ] Save new model metadata

### Phase 4: Verification
- [ ] Test feature extraction (10 contracts)
- [ ] Test prediction with new model
- [ ] Run full test suite
- [ ] Document performance improvements

### Post-Migration
- [ ] Update documentation
- [ ] Commit changes to git
- [ ] Deploy new model (if applicable)
- [ ] Monitor production performance

---

## Next Steps

1. **Start Now**: Run Phase 1 (Database Rebuild)
2. **Monitor**: Watch build progress and success rate
3. **Verify**: Check that 152 features are extracted
4. **Continue**: Proceed to Phase 2 (ML Code Updates)

**Ready to begin!** Start with Phase 1, Step 1 (Backup Database) ⬆️

---

**See Also**:
- [docs/ML_SYSTEM_COMPATIBILITY_ANALYSIS.md](docs/ML_SYSTEM_COMPATIBILITY_ANALYSIS.md) - Full analysis
- [docs/FEATURE_EXTRACTION_FIXES.md](docs/FEATURE_EXTRACTION_FIXES.md) - Tier system details
- [docs/BUILD_COMPARISON.md](docs/BUILD_COMPARISON.md) - Performance metrics
