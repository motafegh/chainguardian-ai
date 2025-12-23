#!/usr/bin/env python3
"""🔍 Are 396 zero-CEI vuln contracts VALUABLE? Check other features!"""

from chainguardian.database.manager import DatabaseManager
import numpy as np

db = DatabaseManager()

print("🔍 zero-CEI VULN vs SAFE FEATURE COMPARISON")
print("="*80)

with db._get_cursor(dict_cursor=True) as cursor:
    # Compare key features: zero-CEI vuln vs ALL vuln vs safe
    cursor.execute("""
        SELECT 
            'zero_cei_vuln' as group_type, 
            AVG(f.has_reentrancy::int) as avg_reentrancy,
            AVG(f.has_unchecked_call::int) as avg_unchecked,
            AVG(f.num_external_calls) as avg_ext_calls,
            AVG(f.risk_score_weighted) as avg_risk,
            COUNT(*) as count
        FROM contracts c JOIN features f ON c.id = f.contract_id
        JOIN labels l ON c.id = l.contract_id
        WHERE f.failure_reason IS NULL AND f.cei_violations = 0 AND l.has_vulnerability = TRUE
        
        UNION ALL
        
        SELECT 
            'all_vuln', 
            AVG(f.has_reentrancy::int),
            AVG(f.has_unchecked_call::int),
            AVG(f.num_external_calls),
            AVG(f.risk_score_weighted),
            COUNT(*)
        FROM contracts c JOIN features f ON c.id = f.contract_id
        JOIN labels l ON c.id = l.contract_id
        WHERE f.failure_reason IS NULL AND l.has_vulnerability = TRUE
        
        UNION ALL
        
        SELECT 
            'safe', 
            AVG(f.has_reentrancy::int),
            AVG(f.has_unchecked_call::int),
            AVG(f.num_external_calls),
            AVG(f.risk_score_weighted),
            COUNT(*)
        FROM contracts c JOIN features f ON c.id = f.contract_id
        JOIN labels l ON c.id = l.contract_id
        WHERE f.failure_reason IS NULL AND l.has_vulnerability = FALSE
    """)
    
    results = cursor.fetchall()
    
    print(f"{'Group':<15} {'Reentrancy':<12} {'Unchecked':<10} {'ExtCalls':<10} {'RiskScore':<12} {'N':<5}")
    print("-"*80)
    for row in results:
        print(f"{row['group_type']:<15} {row['avg_reentrancy']:.3f}{'':<4} {row['avg_unchecked']:.3f}{'':<5} "
              f"{row['avg_ext_calls']:.1f}{'':<6} {row['avg_risk']:.0f}{'':<6} {row['count']:>3}")

print("\n🎯 DECISION MATRIX:")
print("✅ HIGH other signals → KEEP (impute CEI)")
print("❌ LOW other signals → DROP") 
print("🔄 MIXED → SPLIT TEST") [web:28][web:29]
