#!/usr/bin/env python3
"""🔍 REVEAL 396 VULN CONTRACTS - Why no source_code?"""

from chainguardian.database.manager import DatabaseManager

db = DatabaseManager()

print("🔍 TOP 20 VULNERABLE CONTRACTS (zero-CEI, no source)")
print("="*80)

with db._get_cursor() as cursor:
    cursor.execute("""
        SELECT c.id, c.name, LENGTH(COALESCE(c.source_code, '')) as code_len,
               f.cei_violations, f.failure_reason
        FROM contracts c 
        JOIN features f ON c.id = f.contract_id
        JOIN labels l ON c.id = l.contract_id
        WHERE f.failure_reason IS NULL
          AND f.cei_violations = 0
          AND l.has_vulnerability = TRUE
        ORDER BY c.id
        LIMIT 20
    """)
    
    for row in cursor.fetchall():
        id_, name, code_len, cei, failure = row
        source_status = "✅" if code_len > 0 else "❌"
        print(f"{source_status} ID {id_:4d} | {name[:40]:40s} | CEI:{cei:2d} | Code:{code_len:6d} | Fail:{failure or 'None'}")

print("\n🔍 SUMMARY:")
with db._get_cursor(dict_cursor=True) as cursor:
    cursor.execute("""
        SELECT 
            COUNT(*) FILTER (WHERE LENGTH(COALESCE(c.source_code, '')) > 0) as has_source,
            COUNT(*) FILTER (WHERE LENGTH(COALESCE(c.source_code, '')) = 0) as no_source,
            COUNT(*) as total
        FROM contracts c JOIN features f ON c.id = f.contract_id
        JOIN labels l ON c.id = l.contract_id
        WHERE f.failure_reason IS NULL AND f.cei_violations = 0 AND l.has_vulnerability = TRUE
    """)
    stats = cursor.fetchone()
    print(f"📊 Zero-CEI vuln contracts: {stats['total']}")
    print(f"❌ No source_code:         {stats['no_source']} ({stats['no_source']/stats['total']*100:.1f}%)")
    print(f"✅ Has source_code:        {stats['has_source']}")

print("\n🔍 SAMPLE SOURCE CODE (first valid):")
with db._get_cursor() as cursor:
    cursor.execute("""
        SELECT c.id, LEFT(c.source_code, 200) as sample
        FROM contracts c JOIN features f ON c.id = f.contract_id
        JOIN labels l ON c.id = l.contract_id
        WHERE LENGTH(c.source_code) > 100
        ORDER BY c.id
        LIMIT 1
    """)
    row = cursor.fetchone()
    if row and row[1]:
        print(f"ID {row[0]}: {row[1][:200]}...")
    else:
        print("❌ NO VALID SOURCE CODE FOUND!")
