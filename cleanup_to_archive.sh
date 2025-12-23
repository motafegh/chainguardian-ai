#!/bin/bash
# ChainGuardian Project Cleanup
# Moves old experimental files to archive, keeps production files

echo "======================================================================"
echo "🧹 CHAINGUARDIAN PROJECT CLEANUP"
echo "======================================================================"

# Create archive structure
ARCHIVE_DIR="archive/cleanup_$(date +%Y%m%d)"
mkdir -p "$ARCHIVE_DIR"/{scripts,models,reports,mlruns,notebooks,logs,backups}

echo -e "\n📦 Moving old files to: $ARCHIVE_DIR"

# ============================================================================
# SCRIPTS - Move old training/testing scripts
# ============================================================================
echo -e "\n1️⃣  Cleaning scripts/3_training..."
mv scripts/3_training/predict.py "$ARCHIVE_DIR/scripts/" 2>/dev/null
mv scripts/3_training/predict_unlabeled.py "$ARCHIVE_DIR/scripts/" 2>/dev/null
mv scripts/3_training/test_hybrid_adversarial.py "$ARCHIVE_DIR/scripts/" 2>/dev/null
mv scripts/3_training/test_production_hybrid.py "$ARCHIVE_DIR/scripts/" 2>/dev/null
mv scripts/3_training/test_standard_scaler.py "$ARCHIVE_DIR/scripts/" 2>/dev/null
mv scripts/3_training/train_clean_20251222.py "$ARCHIVE_DIR/scripts/" 2>/dev/null
mv scripts/3_training/train_with_db_20251222.py "$ARCHIVE_DIR/scripts/" 2>/dev/null
mv scripts/3_training/train_with_semantic_production.py "$ARCHIVE_DIR/scripts/" 2>/dev/null

echo "   ✅ Moved 8 old training scripts"

# ============================================================================
# SCRIPTS - Move experimental extraction scripts
# ============================================================================
echo -e "\n2️⃣  Cleaning scripts/extraction..."
if [ -d "scripts/extraction" ]; then
    mv scripts/extraction "$ARCHIVE_DIR/scripts/" 2>/dev/null
    echo "   ✅ Moved extraction scripts (outdated)"
fi

# ============================================================================
# SCRIPTS - Move old export scripts
# ============================================================================
echo -e "\n3️⃣  Cleaning old export scripts..."
if [ -d "scripts/export" ]; then
    mv scripts/export "$ARCHIVE_DIR/scripts/" 2>/dev/null
fi
mv scripts/export_final_dataset.py "$ARCHIVE_DIR/scripts/" 2>/dev/null
mv scripts/export_final_dataset.py.backup "$ARCHIVE_DIR/scripts/" 2>/dev/null
echo "   ✅ Moved old export scripts"

# ============================================================================
# SCRIPTS - Move old analysis scripts
# ============================================================================
echo -e "\n4️⃣  Cleaning scripts/analysis..."
if [ -d "scripts/analysis" ]; then
    mv scripts/analysis "$ARCHIVE_DIR/scripts/" 2>/dev/null
    echo "   ✅ Moved analysis scripts"
fi

# ============================================================================
# SCRIPTS - Move old database rebuild scripts
# ============================================================================
echo -e "\n5️⃣  Cleaning scripts/database..."
if [ -d "scripts/database" ]; then
    mv scripts/database "$ARCHIVE_DIR/scripts/" 2>/dev/null
    echo "   ✅ Moved old database scripts"
fi

# ============================================================================
# ROOT - Move test scripts to archive
# ============================================================================
echo -e "\n6️⃣  Cleaning root test scripts..."
mv test_adversarial_manual.py "$ARCHIVE_DIR/" 2>/dev/null
mv test_predictor.py "$ARCHIVE_DIR/" 2>/dev/null
mv test_unseen_data.py "$ARCHIVE_DIR/" 2>/dev/null
mv test_vulnerable_contracts.py "$ARCHIVE_DIR/" 2>/dev/null
mv verify_ml_dataset.py "$ARCHIVE_DIR/" 2>/dev/null
mv check_all_csvs.py "$ARCHIVE_DIR/" 2>/dev/null
mv fix_adversarial_semantic.py "$ARCHIVE_DIR/scripts/" 2>/dev/null
mv inspect_data.py "$ARCHIVE_DIR/scripts/" 2>/dev/null
mv test_integrated_pipeline.py "$ARCHIVE_DIR/scripts/" 2>/dev/null
mv verify_dataset.py "$ARCHIVE_DIR/scripts/" 2>/dev/null
echo "   ✅ Moved root test scripts"

# ============================================================================
# MODELS - Move old model backups (keep latest backup)
# ============================================================================
echo -e "\n7️⃣  Cleaning models/..."
mv models/archive_20251222_before_retrain "$ARCHIVE_DIR/models/" 2>/dev/null
mv models/backup_20251221 "$ARCHIVE_DIR/models/" 2>/dev/null
mv models/run_20251222_123802 "$ARCHIVE_DIR/models/" 2>/dev/null
mv models/saved_models "$ARCHIVE_DIR/models/" 2>/dev/null
mv models/*.bak "$ARCHIVE_DIR/models/" 2>/dev/null
echo "   ✅ Moved old model backups (kept backup_20251222_1425)"

# ============================================================================
# REPORTS - Move old reports
# ============================================================================
echo -e "\n8️⃣  Cleaning reports/..."
mv reports/adversarial_feature_importance.csv "$ARCHIVE_DIR/reports/" 2>/dev/null
mv reports/adversarial_test_results.csv "$ARCHIVE_DIR/reports/" 2>/dev/null
mv reports/baseline_feature_importance.csv "$ARCHIVE_DIR/reports/" 2>/dev/null
mv reports/clean_model_feature_importance.csv "$ARCHIVE_DIR/reports/" 2>/dev/null
mv reports/pattern_learning_feature_importance.csv "$ARCHIVE_DIR/reports/" 2>/dev/null
mv reports/proxy_vs_honest_comparison.csv "$ARCHIVE_DIR/reports/" 2>/dev/null
mv reports/stage1_only_results.csv "$ARCHIVE_DIR/reports/" 2>/dev/null
mv reports/two_stage_adversarial_results.csv "$ARCHIVE_DIR/reports/" 2>/dev/null
mv reports/unlabeled_predictions.csv "$ARCHIVE_DIR/reports/" 2>/dev/null
mv reports/vulnerability_only_importance.csv "$ARCHIVE_DIR/reports/" 2>/dev/null
echo "   ✅ Moved old experimental reports"

# ============================================================================
# RESULTS - Move to reports
# ============================================================================
echo -e "\n9️⃣  Moving results/ to reports/..."
if [ -d "results" ]; then
    mv results/* reports/ 2>/dev/null
    rmdir results 2>/dev/null
    echo "   ✅ Consolidated results into reports"
fi

# ============================================================================
# LOGS - Archive old logs
# ============================================================================
echo -e "\n🔟 Cleaning logs/..."
mv logs/reanalysis_*.log "$ARCHIVE_DIR/logs/" 2>/dev/null
echo "   ✅ Archived old logs"

# ============================================================================
# BACKUPS - Move SQL backups
# ============================================================================
echo -e "\n1️⃣1️⃣  Cleaning SQL backups..."
mv backup_20251222_corrupt.sql "$ARCHIVE_DIR/backups/" 2>/dev/null
mv backup_chainguardian_20251222_125320.sql "$ARCHIVE_DIR/backups/" 2>/dev/null
echo "   ✅ Moved SQL backups"

# ============================================================================
# NOTEBOOKS - Clean old notebooks
# ============================================================================
echo -e "\n1️⃣2️⃣  Cleaning notebooks/..."
mv notebooks/01_deep_eda_v2.ipynb "$ARCHIVE_DIR/notebooks/" 2>/dev/null
echo "   ✅ Archived old notebooks"

# ============================================================================
# SRC - Clean duplicate/backup files
# ============================================================================
echo -e "\n1️⃣3️⃣  Cleaning src/ backups..."
mv src/chainguardian/database/manager.py.backup "$ARCHIVE_DIR/" 2>/dev/null
mv src/chainguardian/feature_extraction/pipeline.py.backup_20251219_224614 "$ARCHIVE_DIR/" 2>/dev/null
mv src/chainguardian/ml/models/hybrid_predictor.py.backup_20251221 "$ARCHIVE_DIR/" 2>/dev/null
mv src/chainguardian/ml/hybrid_predictor.py "$ARCHIVE_DIR/" 2>/dev/null  # Duplicate
echo "   ✅ Moved backup files"

# ============================================================================
# MLOPS - Clean old mlflow artifacts
# ============================================================================
echo -e "\n1️⃣4️⃣  Cleaning mlops/..."
if [ -d "src/chainguardian/mlops/MLflow" ]; then
    mv src/chainguardian/mlops/MLflow "$ARCHIVE_DIR/" 2>/dev/null
    echo "   ✅ Moved old MLflow directory (using root mlruns/)"
fi

# ============================================================================
# SUMMARY
# ============================================================================
echo -e "\n======================================================================"
echo "✅ CLEANUP COMPLETE!"
echo "======================================================================"

echo -e "\n📊 Archived files in: $ARCHIVE_DIR"
echo "   $(find $ARCHIVE_DIR -type f | wc -l) files moved"

echo -e "\n📁 Production files remain in:"
echo "   ✅ scripts/3_training/train_production_model.py"
echo "   ✅ scripts/9_utils/ (verification scripts)"
echo "   ✅ models/production_model.pkl"
echo "   ✅ models/backup_20251222_1425/ (latest backup)"
echo "   ✅ src/chainguardian/ (clean source code)"
echo "   ✅ mlruns/ (experiment tracking)"

echo -e "\n======================================================================"
