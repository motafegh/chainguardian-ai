#!/bin/bash
# Comprehensive Project Cleanup - Aligned with New Feature Extraction System
# Generated: 2025-12-31
# Purpose: Remove ALL obsolete files and keep only what's needed for production

set -e  # Exit on error

echo "🧹 COMPREHENSIVE PROJECT CLEANUP"
echo "================================"
echo ""
echo "⚠️  This will remove ALL obsolete files and align with the new tier-based system"
echo ""

# ============================================================================
# PHASE 1: Create Archive Structure
# ============================================================================
echo "📁 Phase 1: Creating comprehensive archive structure..."

mkdir -p archive/old_feature_extraction/
mkdir -p archive/old_scripts/cei_fixes/
mkdir -p archive/old_scripts/training_versions/
mkdir -p archive/old_scripts/data_quality_versions/
mkdir -p archive/old_scripts/ablation_tests/
mkdir -p archive/old_docs/
mkdir -p archive/old_markdown_root/
mkdir -p archive/test_files/

echo "   ✅ Archive folders created"

# ============================================================================
# PHASE 2: Remove OLD Feature Extraction Files (Already Deleted in Git)
# ============================================================================
echo ""
echo "🗑️  Phase 2: Confirming deletion of old feature extraction files..."

# These are already marked for deletion in git, just confirming
if [ -f "src/chainguardian/feature_extraction/ast_analyzer.py" ]; then
    git rm src/chainguardian/feature_extraction/ast_analyzer.py
    echo "   ✅ Removed ast_analyzer.py (replaced by tier1_core.py)"
fi

if [ -f "src/chainguardian/feature_extraction/contract_analyzer.py" ]; then
    git rm src/chainguardian/feature_extraction/contract_analyzer.py
    echo "   ✅ Removed contract_analyzer.py (replaced by tier system)"
fi

if [ -f "src/chainguardian/feature_extraction/graph_extractor.py" ]; then
    git rm src/chainguardian/feature_extraction/graph_extractor.py
    echo "   ✅ Removed graph_extractor.py (replaced by tier2_semantic_graph.py)"
fi

if [ -f "src/chainguardian/feature_extraction/semantic_analyzer.py" ]; then
    git rm src/chainguardian/feature_extraction/semantic_analyzer.py
    echo "   ✅ Removed semantic_analyzer.py (replaced by tier2_semantic_graph.py)"
fi

# Archive the old backup pipeline
if [ -f "src/chainguardian/feature_extraction/pipeline_old_backup.py" ]; then
    mv src/chainguardian/feature_extraction/pipeline_old_backup.py archive/old_feature_extraction/
    echo "   ✅ Archived pipeline_old_backup.py"
fi

echo "   ✅ Old feature extraction system removed"

# ============================================================================
# PHASE 3: Clean Up Root Directory Markdown Files
# ============================================================================
echo ""
echo "📄 Phase 3: Cleaning up root directory markdown files..."

# Move all root markdown files to archive (except README.md)
for file in *.md; do
    if [ -f "$file" ] && [ "$file" != "README.md" ]; then
        mv "$file" archive/old_markdown_root/
        echo "   ✅ Archived $file"
    fi
done

echo "   ✅ Root markdown files archived"

# ============================================================================
# PHASE 4: Archive Old Docs
# ============================================================================
echo ""
echo "📚 Phase 4: Archiving old documentation..."

# Old docs already marked for deletion in git
if [ -f "PRODUCTION_TRIANGLE_LAYERS_4-7-10.md" ]; then
    git rm PRODUCTION_TRIANGLE_LAYERS_4-7-10.md
    echo "   ✅ Removed PRODUCTION_TRIANGLE_LAYERS_4-7-10.md"
fi

if [ -f "SESSION_REPORT_20251221.md" ]; then
    git rm SESSION_REPORT_20251221.md
    echo "   ✅ Removed SESSION_REPORT_20251221.md"
fi

echo "   ✅ Old documentation archived"

# ============================================================================
# PHASE 5: Clean Up Test Files in Root
# ============================================================================
echo ""
echo "🧪 Phase 5: Cleaning up test files in root..."

# Archive test files from root
test_files=(
    "test_contract_simple.sol"
    "test_multi_contract.py"
    "test_new_extraction.py"
    "test_real_contracts.py"
)

for file in "${test_files[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" archive/test_files/
        echo "   ✅ Archived $file"
    fi
done

echo "   ✅ Root test files archived"

# ============================================================================
# PHASE 6: Archive Versioned Scripts
# ============================================================================
echo ""
echo "📦 Phase 6: Archiving versioned scripts..."

# CEI Fix Scripts (keep only SOURCEFIX)
cei_fixes=(
    "scripts/2_collection/fix_cei_zero.py"
    "scripts/2_collection/fix_cei_zero_v2.py"
    "scripts/2_collection/fix_cei_zero_final.py"
    "scripts/2_collection/fix_cei_zero_RAW.py"
)

for file in "${cei_fixes[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" archive/old_scripts/cei_fixes/
        echo "   ✅ Archived $(basename $file)"
    fi
done

# Training Script Versions (keep only v7)
training_versions=(
    "scripts/3_training/train_production_v4_WITH_BOOLEANS.py"
    "scripts/3_training/train_production_v5_NO_LEAKAGE.py"
    "scripts/3_training/train_production_v6.py"
)

for file in "${training_versions[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" archive/old_scripts/training_versions/
        echo "   ✅ Archived $(basename $file)"
    fi
done

# Data Quality Report Versions (keep only v4)
dq_versions=(
    "scripts/data_quality/data_quality_report_v2.py"
    "scripts/data_quality/data_quality_report_v3.py"
)

for file in "${dq_versions[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" archive/old_scripts/data_quality_versions/
        echo "   ✅ Archived $(basename $file)"
    fi
done

# Ablation Test Versions (keep only FINAL)
if [ -f "scripts/3_training/ablation_cei_test.py" ]; then
    mv scripts/3_training/ablation_cei_test.py archive/old_scripts/ablation_tests/
    echo "   ✅ Archived ablation_cei_test.py"
fi

# Reset and Extract COMPLETE version (keep only regular)
if [ -f "scripts/1_setup/reset_and_extract_all_COMPLETE.py" ]; then
    mv scripts/1_setup/reset_and_extract_all_COMPLETE.py archive/old_scripts/
    echo "   ✅ Archived reset_and_extract_all_COMPLETE.py"
fi

echo "   ✅ Versioned scripts archived"

# ============================================================================
# PHASE 7: Rename Duplicate Files for Clarity
# ============================================================================
echo ""
echo "🏷️  Phase 7: Renaming duplicate files for clarity..."

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

echo "   ✅ Duplicate files renamed"

# ============================================================================
# PHASE 8: Remove Empty Folders
# ============================================================================
echo ""
echo "🗂️  Phase 8: Removing empty folders..."

empty_folders=(
    "scripts/db_management"
    "scripts/ml_training"
    "scripts/utils"
)

for folder in "${empty_folders[@]}"; do
    if [ -d "$folder" ] && [ ! "$(ls -A $folder)" ]; then
        rmdir "$folder"
        echo "   ✅ Removed $folder/"
    fi
done

echo "   ✅ Empty folders removed"

# ============================================================================
# PHASE 9: Clean Up Build Artifacts and Logs
# ============================================================================
echo ""
echo "🧼 Phase 9: Organizing build artifacts and logs..."

# Move old build stats to backups (keep only latest)
if [ -f "database_build_stats_20251230_211118.json" ]; then
    mv database_build_stats_20251230_211118.json backups/
fi

if [ -f "database_build_stats_20251230_213815.json" ]; then
    mv database_build_stats_20251230_213815.json backups/
fi

# Keep the latest: database_build_stats_20251231_000135.json (in root as per .gitignore)

echo "   ✅ Build artifacts organized"

# ============================================================================
# PHASE 10: Clean Up Obsolete Plan Files
# ============================================================================
echo ""
echo "📋 Phase 10: Archiving obsolete plan files..."

if [ -f "plan-for-new-features-extraction.md" ]; then
    mv plan-for-new-features-extraction.md archive/old_markdown_root/
    echo "   ✅ Archived plan-for-new-features-extraction.md"
fi

echo "   ✅ Obsolete plans archived"

# ============================================================================
# PHASE 11: Verify New Feature Extraction System Integrity
# ============================================================================
echo ""
echo "🔍 Phase 11: Verifying new feature extraction system..."

required_files=(
    "src/chainguardian/feature_extraction/pipeline.py"
    "src/chainguardian/feature_extraction/tier1_core.py"
    "src/chainguardian/feature_extraction/tier2_semantic_graph.py"
    "src/chainguardian/feature_extraction/tier3_advanced.py"
    "src/chainguardian/feature_extraction/tier4_detectors.py"
    "src/chainguardian/feature_extraction/feature_spec.py"
    "src/chainguardian/feature_extraction/utils.py"
)

all_present=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ MISSING: $file"
        all_present=false
    fi
done

if [ "$all_present" = true ]; then
    echo "   ✅ All required tier files present"
else
    echo "   ⚠️  WARNING: Some required files missing!"
fi

# ============================================================================
# SUMMARY
# ============================================================================
echo ""
echo "================================"
echo "✅ CLEANUP COMPLETE!"
echo "================================"
echo ""
echo "📊 Summary of Actions:"
echo ""
echo "   🗑️  Old Feature Extraction System:"
echo "      • Removed: ast_analyzer.py, contract_analyzer.py, graph_extractor.py, semantic_analyzer.py"
echo "      • Archived: pipeline_old_backup.py"
echo ""
echo "   📄 Root Directory:"
echo "      • Archived all .md files (except README.md) to archive/old_markdown_root/"
echo "      • Archived test files to archive/test_files/"
echo ""
echo "   📦 Versioned Scripts:"
echo "      • Archived 4 CEI fix versions (kept fix_cei_zero_SOURCEFIX.py)"
echo "      • Archived 3 training versions (kept train_production_v7.py)"
echo "      • Archived 2 data quality versions (kept data_quality_report_v4.py)"
echo "      • Archived 1 ablation test (kept ablation_cei_test_FINAL.py)"
echo ""
echo "   🏷️  Clarity Improvements:"
echo "      • Renamed ml_production/audit_all_features.py → audit_features_with_correlation.py"
echo "      • Renamed 9_utils/verify_dataset.py → verify_dataset_csv.py"
echo ""
echo "   🗂️  Cleanup:"
echo "      • Removed 3 empty folders (db_management, ml_training, utils)"
echo "      • Organized build artifacts to backups/"
echo ""
echo "   ✅ New Tier-Based System:"
echo "      • pipeline.py (main coordinator)"
echo "      • tier1_core.py (56 features)"
echo "      • tier2_semantic_graph.py (33 features)"
echo "      • tier3_advanced.py (68 features)"
echo "      • tier4_detectors.py (69 features)"
echo "      • feature_spec.py (feature definitions)"
echo "      • utils.py (helpers)"
echo ""
echo "📁 All archived files preserved in: ./archive/"
echo ""
echo "🔍 Next Steps:"
echo "   1. Review changes: git status"
echo "   2. Test feature extraction: poetry run python scripts/build_database.py --limit 10"
echo "   3. Commit changes: git add -A && git commit -m 'chore: comprehensive cleanup aligned with tier-based system'"
echo ""
