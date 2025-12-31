# Scripts Folder Cleanup Recommendations

**Generated**: 2025-12-31
**Analysis Date**: Post-Production Deployment
**Purpose**: Identify redundant, versioned, and duplicate scripts for cleanup

---

## Executive Summary

**Total Scripts Analyzed**: 89 files across 9 folders
**Cleanup Actions Required**: 4 categories
**Space to Reclaim**: ~12-15 files can be archived
**Risk Level**: LOW (all recommendations preserve latest/working versions)

---

## 1. Versioned Files - Archive Older Versions

### Critical Finding: Multiple Training Script Versions

**Location**: `scripts/3_training/`

| File | Status | Action |
|------|--------|--------|
| `train_production_v7.py` | **KEEP** - Latest version | No action |
| `train_production_v6.py` | Archive | Move to `archive/3_training/` |
| `train_production_v5_NO_LEAKAGE.py` | Archive | Move to `archive/3_training/` |
| `train_production_v4_WITH_BOOLEANS.py` | Archive | Move to `archive/3_training/` |

**Reasoning**: Version 7 is the latest production training script. Older versions (v4-v6) represent incremental development steps that are no longer needed for production but may have historical value.

**Recommendation**:
```bash
mkdir -p archive/3_training/
mv scripts/3_training/train_production_v4_WITH_BOOLEANS.py archive/3_training/
mv scripts/3_training/train_production_v5_NO_LEAKAGE.py archive/3_training/
mv scripts/3_training/train_production_v6.py archive/3_training/
```

---

### Data Quality Report Versions

**Location**: `scripts/data_quality/`

| File | Status | Action |
|------|--------|--------|
| `data_quality_report_v4.py` | **KEEP** - Latest version | No action |
| `data_quality_report_v3.py` | Archive | Move to `archive/data_quality/` |
| `data_quality_report_v2.py` | Archive | Move to `archive/data_quality/` |

**Reasoning**: Version 4 contains the most comprehensive quality checks. Earlier versions are superseded.

**Recommendation**:
```bash
mkdir -p archive/data_quality/
mv scripts/data_quality/data_quality_report_v2.py archive/data_quality/
mv scripts/data_quality/data_quality_report_v3.py archive/data_quality/
```

---

## 2. Duplicate Files - Consolidate or Document

### Duplicate: `audit_all_features.py`

**Locations**:
- `scripts/data_quality/audit_all_features.py`
- `scripts/ml_production/audit_all_features.py`

**Action Required**: VERIFY CONTENT BEFORE REMOVING

**Steps**:
1. Compare file contents to check if identical:
   ```bash
   diff scripts/data_quality/audit_all_features.py scripts/ml_production/audit_all_features.py
   ```
2. **If identical**: Remove `ml_production` version (keep in `data_quality/` as primary location)
3. **If different**: Rename to clarify purpose:
   - `data_quality/audit_all_features.py` → Keep as is
   - `ml_production/audit_all_features.py` → Rename to `audit_production_features.py`

**Reasoning**: `data_quality/` is the more logical location for feature auditing scripts. If files differ, they serve different purposes and should have distinct names.

---

### Duplicate: `verify_dataset.py`

**Locations**:
- `scripts/9_utils/verify_dataset.py`
- `scripts/data_quality/verify_dataset.py`

**Action Required**: VERIFY CONTENT BEFORE REMOVING

**Steps**:
1. Compare file contents:
   ```bash
   diff scripts/9_utils/verify_dataset.py scripts/data_quality/verify_dataset.py
   ```
2. **If identical**: Remove `9_utils` version (keep in `data_quality/`)
3. **If different**: Rename to clarify purpose

**Reasoning**: Dataset verification is a data quality concern, so `data_quality/` is the appropriate location.

---

## 3. Empty Folders - Remove

**Folders to Delete**:
- `scripts/db_management/` (empty)
- `scripts/ml_training/` (empty)
- `scripts/utils/` (empty)

**Action**:
```bash
rmdir scripts/db_management/
rmdir scripts/ml_training/
rmdir scripts/utils/
```

**Reasoning**: These folders were likely created for organization but never used. Their functionality may have been absorbed into other folders:
- `db_management/` → functionality in `1_setup/`
- `ml_training/` → functionality in `3_training/`
- `utils/` → functionality in `9_utils/`

**Risk**: NONE - Folders are confirmed empty

---

## 4. Potential Redundancy - Review Needed

### CEI (Checks-Effects-Interactions) Fix Scripts

**Location**: `scripts/2_collection/`

**Files Found**:
- `fix_cei_zero.py`
- `fix_cei_zero_v2.py`
- `fix_cei_zero_final.py`
- `fix_cei_zero_final_ACTUAL.py`
- `fix_cei_zero_final_COMPLETE.py`

**Status**: REQUIRES MANUAL REVIEW

**Questions to Answer**:
1. Which file is the actual "final" version?
2. Are all variants still needed or can older ones be archived?

**Recommended Action**:
1. Check git history to identify which was used last in production
2. Keep only the production version (likely `fix_cei_zero_final_COMPLETE.py`)
3. Archive the rest to `archive/2_collection/cei_fixes/`

---

### Ablation Test Scripts

**Location**: `scripts/3_training/`

**Files Found**:
- `ablation_cei_test.py`
- `ablation_cei_test_FINAL.py`

**Status**: REQUIRES MANUAL REVIEW

**Recommendation**:
- If `FINAL` version is complete, archive the original
- If both are used for different test scenarios, rename to clarify purpose

---

## 5. Files Moved to Scripts (Recent)

**Recently Moved**:
- `build_database.py` → `scripts/build_database.py`
- `test_ollama.py` → `scripts/test_ollama.py`

**Status**: ✅ CORRECT LOCATION

**Note**: These files are shown in the analysis as "root/" scripts because they were analyzed from the generated tree before moving them. They are now correctly placed in `scripts/`.

---

## Cleanup Execution Plan

### Phase 1: Low-Risk Cleanup (Immediate)

```bash
# 1. Create archive folder structure
mkdir -p archive/3_training/
mkdir -p archive/data_quality/

# 2. Archive old training versions
mv scripts/3_training/train_production_v4_WITH_BOOLEANS.py archive/3_training/
mv scripts/3_training/train_production_v5_NO_LEAKAGE.py archive/3_training/
mv scripts/3_training/train_production_v6.py archive/3_training/

# 3. Archive old data quality reports
mv scripts/data_quality/data_quality_report_v2.py archive/data_quality/
mv scripts/data_quality/data_quality_report_v3.py archive/data_quality/

# 4. Remove empty folders
rmdir scripts/db_management/
rmdir scripts/ml_training/
rmdir scripts/utils/
```

---

### Phase 2: Duplicate Resolution (Requires Verification)

```bash
# 1. Compare audit_all_features.py files
diff scripts/data_quality/audit_all_features.py scripts/ml_production/audit_all_features.py

# If identical:
rm scripts/ml_production/audit_all_features.py

# 2. Compare verify_dataset.py files
diff scripts/9_utils/verify_dataset.py scripts/data_quality/verify_dataset.py

# If identical:
rm scripts/9_utils/verify_dataset.py
```

---

### Phase 3: Manual Review (User Decision Required)

**CEI Fix Scripts** - Determine which is production version:
- Review: `scripts/2_collection/fix_cei_zero*.py` files
- Keep: Production version only
- Archive: All development versions

**Ablation Tests** - Clarify purpose:
- Review: `scripts/3_training/ablation_cei_test*.py`
- Decision: Archive or rename for clarity

---

## Impact Analysis

### Before Cleanup
- **Total Scripts**: 89 files
- **Versioned Files**: 7 files (5 can be archived)
- **Duplicate Files**: 4 files (2 potential removals)
- **Empty Folders**: 3 folders

### After Cleanup (Estimated)
- **Total Scripts**: ~77-82 files (depending on CEI/ablation decisions)
- **Archived Scripts**: ~7-12 files (preserved for history)
- **Removed Duplicates**: 2-4 files
- **Removed Folders**: 3 empty folders

### Risk Assessment
- **Phase 1 (Archive versioned files)**: ✅ ZERO RISK - Old versions preserved in archive
- **Phase 2 (Remove duplicates)**: ⚠️ LOW RISK - Requires diff verification first
- **Phase 3 (Manual review)**: ⚠️ MEDIUM RISK - Requires understanding of current usage

---

## Recommended .gitignore Updates

Add to `.gitignore` to prevent future clutter:

```gitignore
# ============================================================================
# SCRIPTS ORGANIZATION (Added 2025-12-31)
# ============================================================================
# Archive folder for old script versions
archive/

# Temporary test scripts (pattern-based)
scripts/**/*_test_*.py
scripts/**/*_temp.py
scripts/**/*_debug.py

# Script version backups (if not already archived)
scripts/**/*_v[0-9].py
scripts/**/*_v[0-9][0-9].py
```

---

## Verification Checklist

After cleanup, verify:

- [ ] All production scripts still work
- [ ] No broken imports from removed duplicates
- [ ] Archive folder is excluded from git (if desired)
- [ ] Empty folders are removed
- [ ] README files explain archive structure
- [ ] Latest versions of all scripts are confirmed working

---

## Notes

1. **Archive vs Delete**: We recommend archiving (not deleting) old versions for two reasons:
   - Historical reference if regression occurs
   - Understanding evolution of the codebase

2. **Git History**: Even after archiving, all versions are preserved in git history. The archive folder is for quick reference without digging through commits.

3. **Future Prevention**: Consider adopting a policy:
   - No version suffixes in filenames (use git tags instead)
   - Move old code to archive immediately after replacement
   - Use descriptive names instead of "final", "complete", "actual"

---

## Current Scripts Folder Structure

**Well-Organized Folders** (No changes needed):
- ✅ `1_setup/` - Database setup and schema (7 files)
- ✅ `2_collection/` - Data collection scripts (32 files, some cleanup needed)
- ✅ `3_training/` - ML training scripts (19 files, version cleanup needed)
- ✅ `4_fixes/` - Bug fix and diagnostic scripts (9 files)
- ✅ `9_utils/` - Utility scripts (5 files, duplicate check needed)
- ✅ `data_quality/` - Data quality audits (13 files, version cleanup needed)
- ✅ `ml_production/` - Production ML scripts (2 files, duplicate check needed)

**Overall Assessment**: The numbered folder structure (1_, 2_, 3_, etc.) is excellent and should be maintained. The main issue is version proliferation within folders, not folder organization itself.
