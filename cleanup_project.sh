#!/bin/bash

echo "�� CHAINGUARDIAN AI - PROJECT CLEANUP"
echo "======================================"
echo ""

# Check current size
echo "📊 BEFORE CLEANUP:"
du -sh . --exclude=.git --exclude=.venv --exclude=data 2>/dev/null | head -1
echo ""

# ===== STEP 1: DELETE ENTIRE ARCHIVE DIRECTORY =====
echo "🗑️  STEP 1: Removing archive/ directory..."
if [ -d "archive" ]; then
    SIZE=$(du -sh archive/ 2>/dev/null | cut -f1)
    echo "   Size: $SIZE"
    rm -rf archive/
    echo "   ✅ Deleted archive/"
else
    echo "   ⚠️  archive/ not found"
fi
echo ""

# ===== STEP 2: DELETE REDUNDANT ROOT FILES =====
echo "🗑️  STEP 2: Removing redundant root files..."
FILES_TO_DELETE=(
    "CURRENT_STATUS.md"
    "Full_RoadMap.md"
    "PROGRESS.md"
    "STRUCTURE.md"
    "WORKFLOW.md"
    "adversarial_test_output.txt"
    "test_plot.png"
    "package.json"
    "package-lock.json"
)

for file in "${FILES_TO_DELETE[@]}"; do
    if [ -f "$file" ]; then
        rm -f "$file"
        echo "   ✅ Deleted $file"
    fi
done
echo ""

# ===== STEP 3: DELETE EMPTY/UNUSED DIRECTORIES =====
echo "🗑️  STEP 3: Removing empty/test directories..."
DIRS_TO_DELETE=(
    "blockchain/contracts/collected"
    "blockchain/contracts"
    "blockchain"
    "test_collection"
    "cache"
)

for dir in "${DIRS_TO_DELETE[@]}"; do
    if [ -d "$dir" ]; then
        rm -rf "$dir"
        echo "   ✅ Deleted $dir/"
    fi
done
echo ""

# ===== STEP 4: CLEAN UP LOGS DIRECTORY =====
echo "🗑️  STEP 4: Cleaning logs/ directory..."
if [ -d "logs" ]; then
    LOG_COUNT=$(find logs/ -type f -name "*.log" 2>/dev/null | wc -l)
    echo "   Found $LOG_COUNT log files"
    
    # Keep only latest 5 logs, delete rest
    find logs/ -type f -name "*.log" -printf '%T@ %p\n' | \
        sort -n | head -n -5 | cut -d' ' -f2- | xargs -r rm
    
    REMAINING=$(find logs/ -type f -name "*.log" 2>/dev/null | wc -l)
    echo "   ✅ Kept $REMAINING most recent logs, deleted $((LOG_COUNT - REMAINING))"
else
    echo "   ⚠️  logs/ not found"
fi
echo ""

# ===== STEP 5: CLEAN UP MODELS DIRECTORY =====
echo "🗑️  STEP 5: Cleaning models/ directory..."
cd models/ 2>/dev/null || exit

# Keep only latest semantic/hybrid metadata
if ls semantic_metadata_*.json 1> /dev/null 2>&1; then
    LATEST_SEMANTIC=$(ls -t semantic_metadata_*.json | head -1)
    ls semantic_metadata_*.json | grep -v "$LATEST_SEMANTIC" | xargs -r rm
    echo "   ✅ Kept $LATEST_SEMANTIC, deleted others"
fi

if ls hybrid_metadata_*.json 1> /dev/null 2>&1; then
    LATEST_HYBRID=$(ls -t hybrid_metadata_*.json | head -1)
    ls hybrid_metadata_*.json | grep -v "$LATEST_HYBRID" | xargs -r rm
    echo "   ✅ Kept $LATEST_HYBRID, deleted others"
fi

# Delete redundant files
rm -f model_metadata.json vulnerability_labels.json pattern_learning_features.txt
rm -f stage1_feature_importance.csv stage2_feature_importance.csv
echo "   ✅ Removed redundant metadata files"

# Clean up empty subdirectories
rm -rf mlflow_tracking/ vulnerability_specific/
echo "   ✅ Removed empty subdirectories"

cd ..
echo ""

# ===== STEP 6: CLEAN UP NOTEBOOKS =====
echo "🗑️  STEP 6: Cleaning notebooks/ directory..."
if [ -d "notebooks/h2o_logs" ]; then
    rm -rf notebooks/h2o_logs/
    echo "   ✅ Deleted h2o_logs/"
fi
if [ -d "notebooks/reports/figures" ]; then
    [ -z "$(ls -A notebooks/reports/figures)" ] && rm -rf notebooks/reports/figures/
fi
echo ""

# ===== STEP 7: CLEAN UP REPORTS =====
echo "🗑️  STEP 7: Cleaning reports/ directory..."
cd reports/ 2>/dev/null || exit

# Delete old summary text files
rm -f adversarial_validation_summary.txt baseline_training_results.txt
rm -f day2_summary.txt final_inverted_signals_discovery.txt
rm -f honest_model_summary.txt pattern_learning_results.txt
rm -f vulnerability_only_model_results.txt database_audit_summary.txt

# Keep only essential CSVs
KEEP_CSVS=(
    "adversarial_test_results.csv"
    "model_comparison.csv"
)

for csv in *.csv; do
    if [[ ! " ${KEEP_CSVS[@]} " =~ " ${csv} " ]]; then
        rm -f "$csv"
    fi
done

echo "   ✅ Cleaned old reports, kept essentials"
cd ..
echo ""

# ===== STEP 8: CLEAN UP SCRIPTS =====
echo "🗑️  STEP 8: Cleaning scripts/ directory..."

# Remove experimental/old training scripts
cd scripts/3_training/ 2>/dev/null || exit
rm -f train_baseline.py train_llm_feeder.py train_pattern_learning.py
rm -f train_two_stage_ensemble.py test_stage1_only.py
rm -f test_two_stage_adversarial.py test_two_stage_adversarial.py.old
echo "   ✅ Removed experimental training scripts"
cd ../..

# Remove backup files
find scripts/ -name "*.backup" -delete
find scripts/ -name "*.old" -delete
echo "   ✅ Removed backup files"
echo ""

# ===== STEP 9: CONSOLIDATE DOCS =====
echo "📝 STEP 9: Consolidating documentation..."
mkdir -p docs/archive 2>/dev/null

# Move old docs to archive
OLD_DOCS=(
    "docs/DAY4_COMPLETE_FINAL.md"
    "docs/DAY4_SEMANTIC_ANALYSIS.md"
    "docs/feature_extraction_results.md"
)

for doc in "${OLD_DOCS[@]}"; do
    if [ -f "$doc" ]; then
        mv "$doc" docs/archive/ 2>/dev/null
    fi
done
echo "   ✅ Archived old documentation"
echo ""

# ===== STEP 10: CLEAN RESULTS =====
echo "🗑️  STEP 10: Cleaning results/ directory..."
cd results/ 2>/dev/null || exit

# Keep only the most important results
KEEP_RESULTS=(
    "best_hybrid_config.json"
    "hybrid_performance_summary.json"
    "hyperparameter_search.csv"
    "hyperparameter_tradeoff.png"
)

for file in *; do
    if [[ ! " ${KEEP_RESULTS[@]} " =~ " ${file} " ]]; then
        rm -f "$file"
    fi
done

echo "   ✅ Kept essential results only"
cd ..
echo ""

# ===== VERIFICATION =====
echo "======================================"
echo "✅ CLEANUP COMPLETE!"
echo "======================================"
echo ""

echo "📊 AFTER CLEANUP:"
du -sh . --exclude=.git --exclude=.venv --exclude=data 2>/dev/null | head -1
echo ""

echo "📁 REMAINING STRUCTURE:"
tree -L 2 -d -I '__pycache__|.venv|data|.git|.pytest_cache|*.egg-info' --dirsfirst
echo ""

echo "💾 DISK SPACE SAVED:"
echo "   Check with: du -sh . before/after"
echo ""

echo "✅ Project is now clean and organized!"
