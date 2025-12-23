#!/usr/bin/env python3
"""🔍 What columns in ml_ready_v4.csv?"""

import pandas as pd

df = pd.read_csv('data/ml_ready_v4.csv')
print("📊 CSV SHAPE:", df.shape)
print("\n📋 ALL COLUMNS:")
print(df.columns.tolist())

print("\n🔍 VULNERABILITY COLUMNS (likely names):")
vuln_cols = [col for col in df.columns if any(x in col.lower() for x in ['vuln', 'label', 'target'])]
print("Found:", vuln_cols)

print("\n📊 FIRST 5 ROWS:")
print(df.head())

print("\n🎯 Target column name?")
