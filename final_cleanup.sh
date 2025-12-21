#!/bin/bash

echo "🧹 FINAL AGGRESSIVE CLEANUP"
echo "============================"
echo ""

# Delete ENTIRE archive directory
echo "🗑️  Deleting archive/..."
rm -rf archive/
echo "   ✅ Done"

# Delete ENTIRE backups directory (you have git!)
echo "🗑️  Deleting backups/..."
rm -rf backups/
echo "   ✅ Done"

# Delete blockchain directory (empty)
echo "🗑️  Deleting blockchain/..."
rm -rf blockchain/
echo "   ✅ Done"

# Delete cache directory
echo "🗑️  Deleting cache/..."
rm -rf cache/
echo "   ✅ Done"

# Delete test_collection directory
echo "🗑️  Deleting test_collection/..."
rm -rf test_collection/
echo "   ✅ Done"

# Delete notebooks/h2o_logs
echo "🗑️  Deleting notebooks/h2o_logs/..."
rm -rf notebooks/h2o_logs/
echo "   ✅ Done"

# Clean up empty subdirectories in models
echo "🗑️  Cleaning models/..."
rm -rf models/mlflow_tracking/
rm -rf models/vulnerability_specific/
echo "   ✅ Done"

# Delete most logs (keep last 3)
echo "🗑️  Cleaning logs/..."
cd logs/ 2>/dev/null
if [ -n "$(ls -A)" ]; then
    ls -t *.log 2>/dev/null | tail -n +4 | xargs -r rm
    echo "   ✅ Kept 3 most recent logs"
fi
cd ..

echo ""
echo "✅ CLEANUP COMPLETE!"
echo ""
echo "📊 New structure:"
tree -L 2 -d -I '__pycache__|.venv|data|.git' --dirsfirst
