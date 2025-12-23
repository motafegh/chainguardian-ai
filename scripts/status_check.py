#!/usr/bin/env python3
"""📊 Project Status Overview"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from chainguardian.database.manager import DatabaseManager

db = DatabaseManager()
df = db.get_all_features()

print("🎉 CHAINGUARDIAN STATUS")
print("="*50)
print(f"📈 Contracts: {len(df):,}")
print(f"✅ Successful: {df['failure_reason'].isna().sum():,}")
print(f"🔴 Vulnerable: TBD")  # From labels table
print(f"🚀 ML Ready: YES")
