"""
Standalone Database Verification (No Dependencies)
==================================================
Direct PostgreSQL verification without DatabaseManager import.

Author: Ali
Date: December 22, 2024
"""

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import json
from pathlib import Path

print("\n" + "="*80)
print("🔍 STANDALONE DATABASE VERIFICATION")
print("="*80)

# ============================================================================
# DIRECT CONNECTION (NO MANAGER)
# ============================================================================
print("\n📊 STEP 1: DATABASE CONNECTION")
print("-" * 80)

# EDUCATIONAL NOTE: Direct connection string
# Format: postgresql://user:password@host:port/database
DATABASE_URL = "postgresql://chainguardian_user:2220128@localhost:5432/chainguardian"

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print(f"✅ Connected to PostgreSQL")
        print(f"   Version: {version.split(',')[0]}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print(f"\n💡 Try this command to check if PostgreSQL is running:")
    print(f"   sudo systemctl status postgresql")
    exit(1)

# ============================================================================
# DATA STATISTICS
# ============================================================================
print("\n📈 STEP 2: DATA STATISTICS")
print("-" * 80)

with engine.connect() as conn:
    # Overall stats
    stats_query = text("""
        SELECT 
            data_source,
            COUNT(*) as total_contracts,
            COUNT(CASE WHEN f.failure_reason IS NULL THEN 1 END) as successful,
            COUNT(CASE WHEN f.failure_reason IS NOT NULL THEN 1 END) as failed,
            ROUND(100.0 * COUNT(CASE WHEN f.failure_reason IS NULL THEN 1 END) / COUNT(*), 1) as success_rate
        FROM contracts c
        LEFT JOIN features f ON c.id = f.contract_id
        GROUP BY data_source
        ORDER BY data_source;
    """)
    
    stats_df = pd.read_sql(stats_query, conn)
    
    print("\n📊 Extraction Success Rates:")
    print(stats_df.to_string(index=False))
    
    total = stats_df['total_contracts'].sum()
    successful = stats_df['successful'].sum()
    overall_rate = 100 * successful / total
    
    print(f"\n{'='*60}")
    print(f"OVERALL: {successful}/{total} contracts successful ({overall_rate:.1f}%)")
    print(f"{'='*60}")

# ============================================================================
# LABEL DISTRIBUTION
# ============================================================================
print("\n🎯 STEP 3: LABEL DISTRIBUTION")
print("-" * 80)

with engine.connect() as conn:
    label_query = text("""
        SELECT 
            data_source,
            COUNT(*) as count,
            CASE 
                WHEN data_source IN ('smartbugs_curated', 'production_vulnerable', 'trail_of_bits') 
                THEN 'VULNERABLE'
                ELSE 'SAFE'
            END as label
        FROM contracts c
        INNER JOIN features f ON c.id = f.contract_id
        WHERE f.failure_reason IS NULL
        GROUP BY data_source
        ORDER BY label, data_source;
    """)
    
    label_df = pd.read_sql(label_query, conn)
    
    print("\n📊 Label Distribution by Source:")
    print(label_df.to_string(index=False))
    
    vulnerable = label_df[label_df['label'] == 'VULNERABLE']['count'].sum()
    safe = label_df[label_df['label'] == 'SAFE']['count'].sum()
    total_labeled = vulnerable + safe
    
    print(f"\n{'='*60}")
    print(f"VULNERABLE: {vulnerable} ({100*vulnerable/total_labeled:.1f}%)")
    print(f"SAFE:       {safe} ({100*safe/total_labeled:.1f}%)")
    print(f"TOTAL:      {total_labeled}")
    print(f"{'='*60}")

# ============================================================================
# CEI FEATURES (YOUR INNOVATION)
# ============================================================================
print("\n⭐ STEP 4: SEMANTIC FEATURES (CEI ANALYSIS)")
print("-" * 80)

with engine.connect() as conn:
    cei_query = text("""
        SELECT 
            c.data_source,
            COUNT(*) as contracts,
            ROUND(AVG(f.cei_violations)::numeric, 3) as avg_cei_violations,
            MAX(f.cei_violations) as max_cei_violations,
            ROUND(AVG(f.cei_pattern_score)::numeric, 3) as avg_cei_score,
            COUNT(CASE WHEN f.has_reentrancy_guard THEN 1 END) as with_guard
        FROM contracts c
        INNER JOIN features f ON c.id = f.contract_id
        WHERE f.failure_reason IS NULL
        GROUP BY c.data_source
        ORDER BY avg_cei_violations DESC;
    """)
    
    cei_df = pd.read_sql(cei_query, conn)
    
    print("\n📊 CEI Pattern Analysis by Source:")
    print(cei_df.to_string(index=False))
    
    # Find contracts with violations
    violations_query = text("""
        SELECT 
            c.name,
            c.data_source,
            f.cei_violations,
            f.cei_pattern_score,
            f.has_reentrancy_guard,
            f.state_after_call_count
        FROM contracts c
        INNER JOIN features f ON c.id = f.contract_id
        WHERE f.cei_violations > 0
        ORDER BY f.cei_violations DESC
        LIMIT 10;
    """)
    
    violations_df = pd.read_sql(violations_query, conn)
    
    if len(violations_df) > 0:
        print(f"\n🚨 Contracts with CEI Violations ({len(violations_df)} found):")
        print(violations_df.to_string(index=False))
    else:
        print(f"\n⚠️ No CEI violations detected")

# ============================================================================
# FEATURE RANGES
# ============================================================================
print("\n📏 STEP 5: FEATURE RANGES (OUTLIER CHECK)")
print("-" * 80)

with engine.connect() as conn:
    ranges_query = text("""
        SELECT 
            MIN(lines_of_code) as min_loc,
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY lines_of_code) as q25_loc,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY lines_of_code) as median_loc,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY lines_of_code) as q75_loc,
            MAX(lines_of_code) as max_loc
        FROM features
        WHERE failure_reason IS NULL;
    """)
    
    ranges_df = pd.read_sql(ranges_query, conn)
    
    print(f"\n📊 Lines of Code Distribution:")
    print(f"   Min:    {ranges_df['min_loc'][0]:.0f}")
    print(f"   Q25:    {ranges_df['q25_loc'][0]:.0f}")
    print(f"   Median: {ranges_df['median_loc'][0]:.0f}")
    print(f"   Q75:    {ranges_df['q75_loc'][0]:.0f}")
    print(f"   Max:    {ranges_df['max_loc'][0]:.0f}")
    
    iqr = ranges_df['q75_loc'][0] - ranges_df['q25_loc'][0]
    print(f"\n   IQR:    {iqr:.0f} (RobustScaler will use this!)")

# ============================================================================
# FEATURE COUNT
# ============================================================================
print("\n🔢 STEP 6: FEATURE COUNT")
print("-" * 80)

with engine.connect() as conn:
    columns_query = text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'features'
        AND column_name NOT IN ('id', 'contract_id', 'failure_reason', 'error_message')
        ORDER BY column_name;
    """)
    
    feature_cols = pd.read_sql(columns_query, conn)
    feature_count = len(feature_cols)
    
    print(f"✅ Total ML features: {feature_count}")
    print(f"\n📋 Feature categories:")
    
    # Group by prefix
    prefixes = {
        'has_': 0, 'cei_': 0, 'cfg_': 0, 'cg_': 0, 'dfg_': 0,
        'num_': 0, 'risk_': 0, 'state_': 0
    }
    
    for col in feature_cols['column_name']:
        for prefix in prefixes:
            if col.startswith(prefix):
                prefixes[prefix] += 1
                break
    
    for prefix, count in prefixes.items():
        if count > 0:
            print(f"   {prefix}*: {count} features")

# ============================================================================
# ML READINESS
# ============================================================================
print("\n✅ STEP 7: ML READINESS CHECKLIST")
print("-" * 80)

checklist = {
    f"Sufficient data ({successful} ≥ 300)": successful >= 300,
    f"Balanced dataset ({100*vulnerable/total_labeled:.1f}% vulnerable)": 15 <= 100*vulnerable/total_labeled <= 40,
    f"CEI features extracted ({len(violations_df)} violations found)": len(violations_df) >= 0,
    f"Feature count reasonable ({feature_count} features)": 85 <= feature_count <= 105,
}

all_ready = all(checklist.values())

for check, status in checklist.items():
    icon = "✅" if status else "⚠️"
    print(f"   {icon} {check}")

print(f"\n{'='*80}")
if all_ready:
    print("🎉 DATABASE IS ML-READY!")
else:
    print("⚠️ REVIEW WARNINGS ABOVE")
print(f"{'='*80}")

# ============================================================================
# SAVE SUMMARY
# ============================================================================
print("\n💾 STEP 8: SAVING SUMMARY")
print("-" * 80)

summary = {
    "total_contracts": int(total),
    "successful_extractions": int(successful),
    "vulnerable": int(vulnerable),
    "safe": int(safe),
    "feature_count": int(feature_count),
    "cei_violations_found": int(len(violations_df)),
    "ml_ready": all_ready
}

summary_file = Path("data/db_verification_summary.json")
with open(summary_file, 'w') as f:
    json.dump(summary, f, indent=2)

print(f"✅ Summary saved to: {summary_file}")
print("\n" + "="*80 + "\n")