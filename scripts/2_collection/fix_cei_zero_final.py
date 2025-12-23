#!/usr/bin/env python3
"""🔥 FINAL FIX: Schema-perfect JOIN query"""

from chainguardian.database.manager import DatabaseManager
import pandas as pd
import tempfile
from pathlib import Path
from slither import Slither
import logging
import time

logging.basicConfig(level=logging.ERROR)

db = DatabaseManager()

print("🔍 LIVE QUERY TEST (exact same as cei_status.py)...")
with db._get_cursor(dict_cursor=True) as cursor:
    cursor.execute("""
        SELECT COUNT(*) FILTER (WHERE f.cei_violations = 0) as zero_cei_vuln
        FROM contracts c 
        JOIN features f ON c.id = f.contract_id
        JOIN labels l ON c.id = l.contract_id
        WHERE f.failure_reason IS NULL AND l.has_vulnerability=TRUE
    """)
    stats = cursor.fetchone()
    print(f"🔴 LIVE: {stats['zero_cei_vuln']:,}/469 zero-CEI vuln ← SHOULD BE 396!")

# Target query (SAME LOGIC as above but SELECT data)
print("\n🔥 FETCHING TARGETS...")
with db._get_cursor(dict_cursor=True) as cursor:
    cursor.execute("""
        SELECT c.id, c.name, c.source_code
        FROM contracts c 
        JOIN features f ON c.id = f.contract_id
        JOIN labels l ON c.id = l.contract_id
        WHERE f.failure_reason IS NULL
          AND f.cei_violations = 0
          AND l.has_vulnerability = TRUE
          AND LENGTH(COALESCE(c.source_code, '')) > 100
        ORDER BY c.id
        LIMIT 10  -- First 10 only for debug
    """)
    targets = pd.DataFrame(cursor.fetchall())

print(f"🎯 Found {len(targets)} targets ← DEBUG LIMIT 10")

if len(targets) == 0:
    print("❌ ZERO TARGETS → Check transaction isolation!")
    exit(1)

print("\n✅ PROCESSING SAMPLE...")
fixed = 0
for idx, row in targets.iterrows():
    print(f"  ID {row['id']}: {row['name'][:40]}")
    fixed += 1

print(f"\n🎯 QUERY WORKS! Found {fixed} targets")
print("💡 Remove LIMIT 10 → Process ALL 396!")
