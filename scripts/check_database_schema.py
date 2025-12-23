#!/usr/bin/env python3
"""🔍 FINAL SCHEMA CHECK - c.name (not contract_name)"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from chainguardian.database.manager import DatabaseManager

db = DatabaseManager()

print("="*80)
print("📊 FINAL SCHEMA CHECK - CORRECT COLUMNS")
print("="*80)

print("\n✅ SCHEMA CONFIRMED:")
print("   • contracts.name (NOT contract_name)")
print("   • features.cei_violations ✅")
print("   • labels.has_vulnerability")

# CORRECT sample data
print("\n📊 Sample vuln contracts (FINAL FIX):")
with db._get_cursor() as cur:
    cur.execute("""
        SELECT c.id, c.name, f.cei_violations, l.has_vulnerability
        FROM contracts c 
        JOIN features f ON c.id = f.contract_id 
        JOIN labels l ON c.id = l.contract_id
        WHERE f.failure_reason IS NULL AND l.has_vulnerability = TRUE
        LIMIT 5
    """)
    samples = cur.fetchall()
    for s in samples:
        print(f"   {s[0]:4d} | {s[1]:30s} | CEI: {s[2]:2d} | Vuln: {s[3]}")

# CEI distribution
print("\n📊 CEI Distribution (POST-IMPUTATION):")
with db._get_cursor() as cur:
    cur.execute("""
        SELECT 
            f.cei_violations,
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE l.has_vulnerability = TRUE) as vuln_count,
            ROUND(100.0 * COUNT(*) FILTER (WHERE l.has_vulnerability = TRUE) / COUNT(*), 1) as vuln_pct
        FROM contracts c 
        JOIN features f ON c.id = f.contract_id
        JOIN labels l ON c.id = l.contract_id
        WHERE f.failure_reason IS NULL
        GROUP BY f.cei_violations
        ORDER BY f.cei_violations
    """)
    dist = cur.fetchall()
    print(f"   {'CEI':>3s} | {'Total':>6s} | {'Vuln':>6s} | {'%Vuln':>6s}")
    print(f"   {'-'*3} | {'-'*6} | {'-'*6} | {'-'*6}")
    for d in dist:
        print(f"   {d[0]:3d} | {d[1]:6d} | {d[2]:6d} | {d[3]:6.1f}%")

print("\n🎉 SCHEMA PERFECT!")
print("✅ ALWAYS: c.name + f.cei_violations + l.has_vulnerability")