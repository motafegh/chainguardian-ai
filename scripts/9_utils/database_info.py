"""
Database Information & Statistics
==================================
Comprehensive database overview without authentication issues.

Author: Ali
Date: December 22, 2024
"""

from sqlalchemy import create_engine, text
import pandas as pd

DATABASE_URL = "postgresql://chainguardian_user:2220128@localhost:5432/chainguardian"
engine = create_engine(DATABASE_URL)

print("\n" + "="*80)
print("📊 CHAINGUARDIAN DATABASE INFORMATION")
print("="*80)

with engine.connect() as conn:
    
    # 1. Contract counts
    print("\n1️⃣  CONTRACT COUNTS BY SOURCE")
    print("-" * 80)
    df = pd.read_sql(text("""
        SELECT 
            data_source,
            COUNT(*) as total,
            COUNT(CASE WHEN f.failure_reason IS NULL THEN 1 END) as successful,
            ROUND(100.0 * COUNT(CASE WHEN f.failure_reason IS NULL THEN 1 END) / COUNT(*), 1) as success_rate
        FROM contracts c
        LEFT JOIN features f ON c.id = f.contract_id
        GROUP BY data_source
        ORDER BY data_source;
    """), conn)
    print(df.to_string(index=False))
    
    # 2. Label distribution
    print("\n\n2️⃣  LABEL DISTRIBUTION")
    print("-" * 80)
    df = pd.read_sql(text("""
        SELECT 
            CASE 
                WHEN data_source IN ('smartbugs_curated', 'production_vulnerable', 'trail_of_bits') 
                THEN 'VULNERABLE'
                ELSE 'SAFE'
            END as label,
            COUNT(*) as count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as percentage
        FROM contracts c
        INNER JOIN features f ON c.id = f.contract_id
        WHERE f.failure_reason IS NULL
        GROUP BY label;
    """), conn)
    print(df.to_string(index=False))
    
    # 3. CEI violations
    print("\n\n3️⃣  CEI VIOLATIONS DETECTED")
    print("-" * 80)
    df = pd.read_sql(text("""
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
        ORDER BY f.cei_violations DESC;
    """), conn)
    print(df.to_string(index=False))
    
    # 4. Feature statistics
    print("\n\n4️⃣  FEATURE STATISTICS")
    print("-" * 80)
    df = pd.read_sql(text("""
        SELECT 
            'lines_of_code' as feature,
            MIN(lines_of_code)::int as min,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY lines_of_code)::int as median,
            MAX(lines_of_code)::int as max
        FROM features WHERE failure_reason IS NULL
        UNION ALL
        SELECT 
            'num_functions',
            MIN(num_functions)::int,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY num_functions)::int,
            MAX(num_functions)::int
        FROM features WHERE failure_reason IS NULL
        UNION ALL
        SELECT 
            'cei_violations',
            MIN(cei_violations)::int,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY cei_violations)::int,
            MAX(cei_violations)::int
        FROM features WHERE failure_reason IS NULL;
    """), conn)
    print(df.to_string(index=False))
    
    # 5. Top risky contracts
    print("\n\n5️⃣  TOP 10 HIGHEST RISK CONTRACTS")
    print("-" * 80)
    df = pd.read_sql(text("""
        SELECT 
            c.name,
            c.data_source,
            ROUND(f.risk_score_weighted::numeric, 3) as risk_score,
            f.cei_violations,
            f.total_detector_hits as detector_hits
        FROM contracts c
        INNER JOIN features f ON c.id = f.contract_id
        WHERE f.failure_reason IS NULL
        ORDER BY f.risk_score_weighted DESC
        LIMIT 10;
    """), conn)
    print(df.to_string(index=False))
    
    # 6. Schema info
    print("\n\n6️⃣  SCHEMA INFORMATION")
    print("-" * 80)
    df = pd.read_sql(text("""
        SELECT 
            table_name,
            (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as columns
        FROM information_schema.tables t
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """), conn)
    print(df.to_string(index=False))
    
    # 7. Feature count
    print("\n\n7️⃣  ML FEATURE COUNT")
    print("-" * 80)
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total_columns,
            COUNT(*) - 4 as ml_features
        FROM information_schema.columns
        WHERE table_name = 'features';
    """))
    row = result.fetchone()
    print(f"   Total columns:  {row[0]}")
    print(f"   ML features:    {row[1]} (excluding id, contract_id, failure_reason, error_message)")

print("\n" + "="*80)
print("✅ DATABASE INFORMATION COMPLETE")
print("="*80 + "\n")