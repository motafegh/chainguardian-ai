#!/usr/bin/env python3
"""CEI Status - FIXED SQL"""

from chainguardian.database.manager import DatabaseManager

db = DatabaseManager()

print("📊 CURRENT CEI STATUS:")
with db._get_cursor(dict_cursor=True) as cursor:
    # FIXED: Direct JOIN (no subquery)
    cursor.execute("""
        SELECT 
            COUNT(*) as total_ml_ready,
            AVG(f.cei_violations) as avg_cei,
            COUNT(*) FILTER (WHERE f.cei_violations = 0) as zero_cei_all,
            COUNT(*) FILTER (WHERE vuln=True AND f.cei_violations = 0) as zero_cei_vuln,
            COUNT(*) FILTER (WHERE vuln=True) as vuln_total
        FROM contracts c 
        JOIN features f ON c.id = f.contract_id 
        LEFT JOIN LATERAL (
            SELECT EXISTS(SELECT 1 FROM labels l WHERE l.contract_id = c.id AND l.has_vulnerability=TRUE) as vuln
        ) v ON true
        WHERE f.failure_reason IS NULL
    """)
    stats = cursor.fetchone()
    
    print(f"✅ ML-ready contracts:           {stats['total_ml_ready']:,}")
    print(f"📊 Avg CEI violations:           {stats['avg_cei']:.2f}")
    print(f"🔢 Zero CEI (all):               {stats['zero_cei_all']:,} ({stats['zero_cei_all']/stats['total_ml_ready']*100:.1f}%)")
    print(f"🔴 Zero CEI (vulnerable only):   {stats['zero_cei_vuln']:,} / {stats['vuln_total']:,} ({stats['zero_cei_vuln']/stats['vuln_total']*100:.1f}%)")

# HEALTH CHECK
zero_cei_pct = stats['zero_cei_vuln'] / stats['vuln_total']
status = "✅ HEALTHY" if zero_cei_pct < 0.5 else "⚠️  POOR SIGNAL"
print(f"\n🎯 CEI HEALTH: {status} ({zero_cei_pct:.1%} vuln with zero CEI)")
