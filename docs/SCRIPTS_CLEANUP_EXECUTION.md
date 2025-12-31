# Scripts Cleanup - Execution Plan

**Generated**: 2025-12-31
**Status**: READY FOR EXECUTION
**Risk Level**: LOW (all changes preserve working code)

---

## Analysis Results

### Files Analyzed
- **Total Scripts**: 89 files across 7 folders
- **Duplicate Files**: 2 pairs (DIFFERENT content, both needed)
- **Versioned Files**: 5 old versions to archive
- **Empty Folders**: 3 folders to remove
- **CEI Fix Scripts**: 5 variants (keep SOURCEFIX as latest)

---

## Critical Findings

### 1. Duplicate Files - KEEP BOTH (Different Content)

#### `audit_all_features.py` - DIFFERENT purposes

**File 1**: [scripts/data_quality/audit_all_features.py](../scripts/data_quality/audit_all_features.py)
- **Purpose**: Fixed version using DatabaseManager with native cursor
- **Key Feature**: Loads 100 samples, identifies excluded features
- **Status**: ✅ KEEP - Main audit script

**File 2**: [scripts/ml_production/audit_all_features.py](../scripts/ml_production/audit_all_features.py)
- **Purpose**: Complete feature categorization and correlation analysis
- **Key Feature**: Loads 5 samples, detailed categorical analysis, correlation with target
- **Status**: ✅ KEEP - Production audit with advanced analysis

**Action**: RENAME to clarify purpose
```bash
# Rename to avoid confusion
mv scripts/ml_production/audit_all_features.py scripts/ml_production/audit_features_with_correlation.py
```

---

#### `verify_dataset.py` - DIFFERENT purposes

**File 1**: [scripts/9_utils/verify_dataset.py](../scripts/9_utils/verify_dataset.py)
- **Purpose**: Quick integrity check of CSV file
- **Key Feature**: Loads from `data/complete_dataset_with_semantic.csv`
- **Focus**: Basic stats, feature groups, missing values
- **Status**: ✅ KEEP - Quick verification utility

**File 2**: [scripts/data_quality/verify_dataset.py](../scripts/data_quality/verify_dataset.py)
- **Purpose**: Production dataset quality verification
- **Key Feature**: Loads from database, checks production requirements
- **Focus**: Source diversity, balance requirements, saves verification report
- **Status**: ✅ KEEP - Production quality checks

**Action**: RENAME to clarify purpose
```bash
# Rename for clarity
mv scripts/9_utils/verify_dataset.py scripts/9_utils/verify_dataset_csv.py
```

---

### 2. CEI Fix Scripts - Archive Old Versions

**Files Found** (by modification date):
1. `fix_cei_zero_SOURCEFIX.py` (Dec 22 21:34) ← **LATEST**
2. `fix_cei_zero_RAW.py` (Dec 22 21:28)
3. `fix_cei_zero_final.py` (Dec 22 21:26)
4. `fix_cei_zero_v2.py` (Dec 22 21:24)
5. `fix_cei_zero.py` (Dec 22 21:21) ← **OLDEST**

**Recommendation**: Keep SOURCEFIX, archive the rest

```bash
# Create archive folder
mkdir -p archive/2_collection/cei_fixes/

# Archive old versions (keep SOURCEFIX)
mv scripts/2_collection/fix_cei_zero.py archive/2_collection/cei_fixes/
mv scripts/2_collection/fix_cei_zero_v2.py archive/2_collection/cei_fixes/
mv scripts/2_collection/fix_cei_zero_final.py archive/2_collection/cei_fixes/
mv scripts/2_collection/fix_cei_zero_RAW.py archive/2_collection/cei_fixes/

# KEEP: fix_cei_zero_SOURCEFIX.py (latest working version)
```

---

### 3. Versioned Training Scripts

**Location**: [scripts/3_training/](../scripts/3_training/)

| File | Date | Status |
|------|------|--------|
| `train_production_v7.py` | Latest | ✅ KEEP |
| `train_production_v6.py` | Older | 🗑️ Archive |
| `train_production_v5_NO_LEAKAGE.py` | Older | 🗑️ Archive |
| `train_production_v4_WITH_BOOLEANS.py` | Older | 🗑️ Archive |

```bash
# Create archive folder
mkdir -p archive/3_training/versions/

# Archive old training versions
mv scripts/3_training/train_production_v4_WITH_BOOLEANS.py archive/3_training/versions/
mv scripts/3_training/train_production_v5_NO_LEAKAGE.py archive/3_training/versions/
mv scripts/3_training/train_production_v6.py archive/3_training/versions/

# KEEP: train_production_v7.py
```

---

### 4. Data Quality Report Versions

**Location**: [scripts/data_quality/](../scripts/data_quality/)

| File | Status |
|------|--------|
| `data_quality_report_v4.py` | ✅ KEEP |
| `data_quality_report_v3.py` | 🗑️ Archive |
| `data_quality_report_v2.py` | 🗑️ Archive |

```bash
# Create archive folder
mkdir -p archive/data_quality/versions/

# Archive old report versions
mv scripts/data_quality/data_quality_report_v2.py archive/data_quality/versions/
mv scripts/data_quality/data_quality_report_v3.py archive/data_quality/versions/

# KEEP: data_quality_report_v4.py
```

---

### 5. Ablation Test Scripts

**Location**: [scripts/3_training/](../scripts/3_training/)

| File | Status |
|------|--------|
| `ablation_cei_test_FINAL.py` | ✅ KEEP |
| `ablation_cei_test.py` | 🗑️ Archive |

```bash
# Archive old ablation test
mv scripts/3_training/ablation_cei_test.py archive/3_training/versions/

# KEEP: ablation_cei_test_FINAL.py
```

---

### 6. Empty Folders

**Folders to Remove**:
- `scripts/db_management/` (empty)
- `scripts/ml_training/` (empty)
- `scripts/utils/` (empty)

```bash
# Remove empty folders
rmdir scripts/db_management/
rmdir scripts/ml_training/
rmdir scripts/utils/
```

---

## Complete Execution Script

Save this as `scripts/cleanup_scripts.sh`:

```bash
#!/bin/bash
# Scripts Cleanup - Automated Execution
# Generated: 2025-12-31

set -e  # Exit on error

echo "🧹 Starting Scripts Cleanup..."
echo ""

# ============================================================================
# PHASE 1: Create Archive Structure
# ============================================================================
echo "📁 Creating archive folders..."
mkdir -p archive/2_collection/cei_fixes/
mkdir -p archive/3_training/versions/
mkdir -p archive/data_quality/versions/

# ============================================================================
# PHASE 2: Rename Duplicate Files for Clarity
# ============================================================================
echo "📝 Renaming duplicate files for clarity..."

# Rename audit_all_features.py in ml_production
if [ -f "scripts/ml_production/audit_all_features.py" ]; then
    mv scripts/ml_production/audit_all_features.py scripts/ml_production/audit_features_with_correlation.py
    echo "   ✅ Renamed ml_production/audit_all_features.py → audit_features_with_correlation.py"
fi

# Rename verify_dataset.py in 9_utils
if [ -f "scripts/9_utils/verify_dataset.py" ]; then
    mv scripts/9_utils/verify_dataset.py scripts/9_utils/verify_dataset_csv.py
    echo "   ✅ Renamed 9_utils/verify_dataset.py → verify_dataset_csv.py"
fi

# ============================================================================
# PHASE 3: Archive CEI Fix Versions
# ============================================================================
echo "🗄️  Archiving old CEI fix scripts..."

if [ -f "scripts/2_collection/fix_cei_zero.py" ]; then
    mv scripts/2_collection/fix_cei_zero.py archive/2_collection/cei_fixes/
    echo "   ✅ Archived fix_cei_zero.py"
fi

if [ -f "scripts/2_collection/fix_cei_zero_v2.py" ]; then
    mv scripts/2_collection/fix_cei_zero_v2.py archive/2_collection/cei_fixes/
    echo "   ✅ Archived fix_cei_zero_v2.py"
fi

if [ -f "scripts/2_collection/fix_cei_zero_final.py" ]; then
    mv scripts/2_collection/fix_cei_zero_final.py archive/2_collection/cei_fixes/
    echo "   ✅ Archived fix_cei_zero_final.py"
fi

if [ -f "scripts/2_collection/fix_cei_zero_RAW.py" ]; then
    mv scripts/2_collection/fix_cei_zero_RAW.py archive/2_collection/cei_fixes/
    echo "   ✅ Archived fix_cei_zero_RAW.py"
fi

echo "   ✅ KEPT: fix_cei_zero_SOURCEFIX.py (latest version)"

# ============================================================================
# PHASE 4: Archive Training Script Versions
# ============================================================================
echo "🗄️  Archiving old training scripts..."

if [ -f "scripts/3_training/train_production_v4_WITH_BOOLEANS.py" ]; then
    mv scripts/3_training/train_production_v4_WITH_BOOLEANS.py archive/3_training/versions/
    echo "   ✅ Archived train_production_v4_WITH_BOOLEANS.py"
fi

if [ -f "scripts/3_training/train_production_v5_NO_LEAKAGE.py" ]; then
    mv scripts/3_training/train_production_v5_NO_LEAKAGE.py archive/3_training/versions/
    echo "   ✅ Archived train_production_v5_NO_LEAKAGE.py"
fi

if [ -f "scripts/3_training/train_production_v6.py" ]; then
    mv scripts/3_training/train_production_v6.py archive/3_training/versions/
    echo "   ✅ Archived train_production_v6.py"
fi

echo "   ✅ KEPT: train_production_v7.py (latest version)"

# ============================================================================
# PHASE 5: Archive Data Quality Report Versions
# ============================================================================
echo "🗄️  Archiving old data quality reports..."

if [ -f "scripts/data_quality/data_quality_report_v2.py" ]; then
    mv scripts/data_quality/data_quality_report_v2.py archive/data_quality/versions/
    echo "   ✅ Archived data_quality_report_v2.py"
fi

if [ -f "scripts/data_quality/data_quality_report_v3.py" ]; then
    mv scripts/data_quality/data_quality_report_v3.py archive/data_quality/versions/
    echo "   ✅ Archived data_quality_report_v3.py"
fi

echo "   ✅ KEPT: data_quality_report_v4.py (latest version)"

# ============================================================================
# PHASE 6: Archive Ablation Test Versions
# ============================================================================
echo "🗄️  Archiving old ablation tests..."

if [ -f "scripts/3_training/ablation_cei_test.py" ]; then
    mv scripts/3_training/ablation_cei_test.py archive/3_training/versions/
    echo "   ✅ Archived ablation_cei_test.py"
fi

echo "   ✅ KEPT: ablation_cei_test_FINAL.py (latest version)"

# ============================================================================
# PHASE 7: Remove Empty Folders
# ============================================================================
echo "🗑️  Removing empty folders..."

if [ -d "scripts/db_management" ] && [ ! "$(ls -A scripts/db_management)" ]; then
    rmdir scripts/db_management/
    echo "   ✅ Removed scripts/db_management/"
fi

if [ -d "scripts/ml_training" ] && [ ! "$(ls -A scripts/ml_training)" ]; then
    rmdir scripts/ml_training/
    echo "   ✅ Removed scripts/ml_training/"
fi

if [ -d "scripts/utils" ] && [ ! "$(ls -A scripts/utils)" ]; then
    rmdir scripts/utils/
    echo "   ✅ Removed scripts/utils/"
fi

# ============================================================================
# PHASE 8: Summary
# ============================================================================
echo ""
echo "✅ CLEANUP COMPLETE!"
echo ""
echo "📊 Summary:"
echo "   • Renamed 2 duplicate files for clarity"
echo "   • Archived 4 CEI fix versions → archive/2_collection/cei_fixes/"
echo "   • Archived 3 training versions → archive/3_training/versions/"
echo "   • Archived 2 data quality versions → archive/data_quality/versions/"
echo "   • Archived 1 ablation test → archive/3_training/versions/"
echo "   • Removed 3 empty folders"
echo ""
echo "📁 Archive structure created in: ./archive/"
echo "🔍 Verify changes: git status"
echo ""
