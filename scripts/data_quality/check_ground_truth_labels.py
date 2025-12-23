# scripts/check_ground_truth_labels.py
"""
Check REAL ground truth labels from database (labels table)
NOT derived from features!
"""

from chainguardian.database.manager import DatabaseManager
import pandas as pd

db = DatabaseManager()

print("\n" + "="*70)
print("🏷️  GROUND TRUTH LABELS ANALYSIS")
print("="*70)

# Get ALL labels from labels table
with db._get_cursor(dict_cursor=True) as cursor:
    cursor.execute("""
        SELECT 
            l.contract_id,
            l.vulnerability_type,
            l.has_vulnerability,
            l.confidence,
            l.severity,
            l.source,
            c.name as contract_name,
            c.data_source
        FROM labels l
        JOIN contracts c ON l.contract_id = c.id
        ORDER BY l.contract_id, l.vulnerability_type
    """)
    labels_df = pd.DataFrame(cursor.fetchall())

print(f"📊 TOTAL GROUND TRUTH LABELS: {len(labels_df):,}")
print(f"📊 UNIQUE CONTRACTS LABELED: {labels_df['contract_id'].nunique():,}")

if len(labels_df) == 0:
    print("\n❌ NO GROUND TRUTH LABELS FOUND!")
    print("💡 Labels table is empty - need to populate from sources")
else:
    print("\n🔴 VULNERABILITIES BY TYPE:")
    vuln_summary = labels_df[labels_df['has_vulnerability'] == True]['vulnerability_type'].value_counts()
    print(vuln_summary.head(10))
    
    print("\n🟢 TOTAL VULNERABLE CONTRACTS:")
    vuln_contracts = labels_df[labels_df['has_vulnerability'] == True]['contract_id'].nunique()
    print(f"   {vuln_contracts:,} contracts have ≥1 vulnerability")
    
    print("\n📋 TOP SOURCES:")
    print(labels_df['source'].value_counts().head(10))

print("\n🏷️  SUMMARY BY DATA SOURCE:")
with db._get_cursor(dict_cursor=True) as cursor:
    cursor.execute("""
        SELECT 
            c.data_source,
            COUNT(DISTINCT c.id) as total_contracts,
            COUNT(DISTINCT CASE WHEN l.has_vulnerability THEN c.id END) as vuln_contracts,
            COUNT(l.id) as total_labels
        FROM contracts c
        LEFT JOIN labels l ON c.id = l.contract_id
        GROUP BY c.data_source
        ORDER BY total_contracts DESC
    """)
    source_summary = pd.DataFrame(cursor.fetchall())
    print(source_summary.head(10))
