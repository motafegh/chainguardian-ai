# ═══════════════════════════════════════════════════
# VERIFICATION SCRIPT - Run this with me watching
# ═══════════════════════════════════════════════════

import sys
print(f"Python version: {sys.version}")
assert sys.version_info >= (3, 11), "❌ Need Python 3.11+"
print("✅ Python version OK")

# ────────────────────────────────────────────────────
# TEST 1: Core Libraries
# ────────────────────────────────────────────────────
try:
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns
    from sklearn.ensemble import RandomForestClassifier
    print("✅ Core libraries import successfully")
except ImportError as e:
    print(f"❌ Missing library: {e}")
    print("Run: poetry add pandas numpy matplotlib seaborn scikit-learn")

# ────────────────────────────────────────────────────
# TEST 2: Load Your Dataset
# ────────────────────────────────────────────────────
try:
    df = pd.read_csv('data/chainguardian_features_clean.csv')
    print(f"✅ Loaded dataset: {len(df)} contracts, {len(df.columns)} columns")
    print(f"   Columns: {list(df.columns[:5])}...")
    print(f"   Vulnerability columns: {[c for c in df.columns if c.startswith('has_')]}")
except FileNotFoundError:
    print("❌ Dataset not found at 'data/chainguardian_features_clean.csv'")
    print("   Current directory:", os.getcwd())
    print("   Expected path:", os.path.abspath('data/chainguardian_features_clean.csv'))
except Exception as e:
    print(f"❌ Error loading dataset: {e}")

# ────────────────────────────────────────────────────
# TEST 3: Matplotlib Works
# ────────────────────────────────────────────────────
try:
    plt.figure(figsize=(8, 4))
    plt.plot([1, 2, 3], [1, 4, 9])
    plt.title("Test Plot")
    plt.savefig('test_plot.png', dpi=100, bbox_inches='tight')
    plt.close()
    print("✅ Matplotlib works - saved test_plot.png")
except Exception as e:
    print(f"❌ Matplotlib error: {e}")

# ────────────────────────────────────────────────────
# TEST 4: Jupyter Notebook
# ────────────────────────────────────────────────────
try:
    import notebook
    print("✅ Jupyter installed")
except ImportError:
    print("⚠️ Jupyter not installed")
    print("Run: poetry add jupyter ipykernel")

# ────────────────────────────────────────────────────
# TEST 5: Access to .sol Files
# ────────────────────────────────────────────────────
import os
from pathlib import Path

# Check where your .sol files are
possible_paths = [
    'blockchain/contracts/collected',
    'data/smartbugs/',
    'contracts/',
]

sol_files_found = []
for path in possible_paths:
    if os.path.exists(path):
        sol_count = len(list(Path(path).rglob('*.sol')))
        if sol_count > 0:
            sol_files_found.append((path, sol_count))
            print(f"✅ Found {sol_count} .sol files in {path}")

if not sol_files_found:
    print("⚠️ No .sol files found - needed for graph feature extraction")
    print("   We'll need to query database or fetch from Etherscan")
else:
    print(f"✅ Total .sol files accessible: {sum(count for _, count in sol_files_found)}")

# ────────────────────────────────────────────────────
# TEST 6: Database Connection (if applicable)
# ────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
    
    # Try importing your database manager
    # Adjust path to your actual module
    # from src.chainguardian.database.manager import DatabaseManager
    # db = DatabaseManager()
    # db.connect()
    # print("✅ Database connection works")
    
    print("⚠️ Skipping database test - uncomment if you use it")
except Exception as e:
    print(f"⚠️ Database test skipped: {e}")

# ────────────────────────────────────────────────────
# TEST 7: Git Status
# ────────────────────────────────────────────────────
import subprocess
try:
    result = subprocess.run(['git', 'status', '--short'], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        if result.stdout.strip():
            print("⚠️ Uncommitted changes:")
            print(result.stdout)
            print("   Consider committing before starting")
        else:
            print("✅ Git repo clean")
except:
    print("⚠️ Git check failed")

# ────────────────────────────────────────────────────
# TEST 8: Create Notebooks Directory
# ────────────────────────────────────────────────────
os.makedirs('notebooks', exist_ok=True)
print("✅ notebooks/ directory ready")

# ────────────────────────────────────────────────────
# TEST 9: Install Additional Libraries for Week 1
# ────────────────────────────────────────────────────
print("\n📦 Libraries needed for next 2 weeks:")
print("Run this command:")
print("""
poetry add \\
    jupyter \\
    ipykernel \\
    matplotlib \\
    seaborn \\
    plotly \\
    scipy \\
    networkx \\
    imbalanced-learn \\
    xgboost \\
    lightgbm \\
    shap \\
    optuna \\
    tqdm
""")

print("\n" + "="*60)
print("✅ SETUP VERIFICATION COMPLETE")
print("="*60)
print("\nIf all tests passed, you're ready for Day 1!")
print("If any failed, let's fix them now before starting.")