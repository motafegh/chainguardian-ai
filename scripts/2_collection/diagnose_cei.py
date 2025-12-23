#!/usr/bin/env python3
"""🔍 DIAGNOSE WHY 396 TARGETS → 0 MATCHES"""

from chainguardian.database.manager import DatabaseManager

db = DatabaseManager()

print("🔍 STEP 1: Total vuln contracts")
with db._get_cursor(dict_cursor=True) as cursor:
    cursor.execute("SELECT COUNT(*) as total_vuln FROM labels WHERE has_vulnerability=TRUE")
    print(f"Total vuln labels: {cursor.fetchone()['total_vuln']:,}")

print("\n🔍 STEP 2: ML-ready vuln contracts")
with db._get_cursor(dict_cursor=True) as cursor:
    cursor.execute("""
        SELECT COUNT(*) as ml_ready_vuln
        FROM contracts c 
        JOIN features f ON c.id = f.contract_id
        JOIN labels l ON c.id = l.contract_id
        WHERE f.failure_reason IS NULL AND l.has_vulnerability=TRUE
    """)
    print(f"ML-ready vuln: {cursor.fetchone()['ml_ready_vuln']:,}")

print("\n�� STEP 3: Zero-CEI ML-ready vuln (BROKEN QUERY)")
with db._get_cursor(dict_cursor=True) as cursor:
    cursor.execute("""
        SELECT COUNT(*) as zero_cei_vuln
        FROM contracts c 
        JOIN features f ON c.id = f.contract_id
        WHERE f.failure_reason IS NULL
          AND f.cei_violations = 0
          AND EXISTS (SELECT 1 FROM labels l WHERE l.contract_id = c.id AND l.has_vulnerability=TRUE)
    """)
    print(f"Zero-CEI vuln (EXISTS): {cursor.fetchone()['zero_cei_vuln']:,} ← 0?!?")

print("\n🔍 STEP 4: ACTUAL zero-CEI vuln (JOIN)")
with db._get_cursor(dict_cursor=True) as cursor:
    cursor.execute("""
        SELECT COUNT(*) FILTER (WHERE f.cei_violations = 0) as zero_cei_vuln_join
        FROM contracts c 
        JOIN features f ON c.id = f.contract_id
        JOIN labels l ON c.id = l.contract_id
        WHERE f.failure_reason IS NULL AND l.has_vulnerability=TRUE
    """)
    stats = cursor.fetchone()
    print(f"Zero-CEI vuln (JOIN):  {stats['zero_cei_vuln_join']:,} ← 396!")

print("\n🎯 DIAGNOSIS: EXISTS() subquery fails → Use JOIN instead")
