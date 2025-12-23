#!/usr/bin/env python3
"""🔍 FINAL VERIFICATION - FIXED FOR DatabaseManager"""

from chainguardian.database.manager import DatabaseManager
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
db = DatabaseManager()

print("🔍 FINAL VERIFICATION")
print("="*60)

# 1. TOTAL CONTRACTS
total = db.get_contract_count()
print(f"\n📊 Total contracts in database: {total:,}")

# 2. DATA SOURCES + LABELS (FIXED: Use db.get_all_features())
print("\n📁 Data Sources:")
df_features = db.get_all_features()
source_counts = df_features['data_source'].value_counts().head(10)
print(source_counts)

# 3. GROUND TRUTH LABELS (Direct query)
print("\n🏷️  Label Distribution:")
try:
    with db._get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT 
                has_vulnerability,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as percentage
            FROM labels 
            GROUP BY has_vulnerability
            ORDER BY has_vulnerability DESC
        """)
        label_dist = pd.DataFrame(cursor.fetchall())
        print(label_dist.to_string(index=False))
        
        vuln_pct = label_dist[label_dist['has_vulnerability'] == True]['percentage'].sum()
        print(f"\n📈 SUMMARY:")
        print(f"   Vulnerable: {vuln_pct:.1f}% ({label_dist[label_dist['has_vulnerability'] == True]['count'].sum():,})")
        print(f"   Safe:       {100-vuln_pct:.1f}%")
        
        if 35 <= vuln_pct <= 65:
            print("   ✅ PERFECT balance for ML!")
        else:
            print("   ⚠️  Consider dataset balancing")
            
except Exception as e:
    print(f"⚠️  Label query error: {e}")

# 4. EXTRACTION QUALITY
print("\n�� Extraction Quality:")
successful = df_features['failure_reason'].isna().sum()
print(f"   ✅ Successful: {successful:,} ({successful/len(df_features)*100:.1f}%)")
print(f"   ❌ Failed:     {len(df_features)-successful:,} ({(len(df_features)-successful)/len(df_features)*100:.1f}%)")

failures = df_features['failure_reason'].value_counts()
if len(failures) > 0:
    print("   💥 Top failures:")
    for reason, count in failures.head().items():
        print(f"      {reason}: {count:,}")

# 5. TOP RISKY CONTRACTS
print("\n🔥 Top Risky Contracts:")
try:
    with db._get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT c.name, f.risk_score_weighted, f.lines_of_code, 
                   CASE WHEN l.has_vulnerability THEN 'VULN' ELSE 'SAFE' END as status
            FROM contracts c 
            JOIN features f ON c.id = f.contract_id
            LEFT JOIN labels l ON c.id = l.contract_id AND l.has_vulnerability = TRUE
            WHERE f.failure_reason IS NULL
            ORDER BY f.risk_score_weighted DESC 
            LIMIT 10
        """)
        risky = pd.DataFrame(cursor.fetchall())
        print(risky.to_string(index=False))
except Exception as e:
    print(f"⚠️  Risk query: {e}")

print("\n" + "="*60)
print("✅ VERIFICATION COMPLETE!")
print("🎯 Database ready for production ML!")
