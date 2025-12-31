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
