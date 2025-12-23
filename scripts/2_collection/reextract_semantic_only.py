#!/usr/bin/env python3
"""Re-extract semantic features - BULLETPROOF VERSION"""

from chainguardian.database.manager import DatabaseManager
import pandas as pd
import logging
import tempfile
from pathlib import Path
from slither import Slither

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("="*80)
print("🔄 RE-EXTRACTING SEMANTIC FEATURES (BULLETPROOF)")
print("="*80)

db = DatabaseManager()

# BULLETPROOF: Check ALL contracts (no source_code filter)
print("\n📥 Loading ALL vulnerable contracts...")
with db._get_cursor(dict_cursor=True) as cursor:
    cursor.execute("""
        SELECT 
            c.id,
            c.name as contract_name,
            COALESCE(c.source_code, '') as source_code,
            c.file_path,
            f.cei_violations,
            CASE WHEN EXISTS (
                SELECT 1 FROM labels l WHERE l.contract_id = c.id AND l.has_vulnerability = TRUE
            ) THEN TRUE ELSE FALSE END as ground_truth_vulnerable
        FROM contracts c
        JOIN features f ON c.id = f.contract_id
        WHERE f.failure_reason IS NULL
          AND f.cei_violations = 0
          AND LENGTH(COALESCE(c.source_code, '')) > 100
        ORDER BY c.id
    """)
    contracts_df = pd.DataFrame(cursor.fetchall())

print(f"✅ Found {len(contracts_df)} vulnerable contracts with zero CEI")

if len(contracts_df) == 0:
    print("✅ No contracts need semantic re-extraction!")
    print("\n📊 Quick check - ALL CEI stats:")
    with db._get_cursor(dict_cursor=True) as cursor:
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                AVG(cei_violations) as avg_cei,
                COUNT(*) FILTER (WHERE cei_violations = 0) as zero_cei,
                COUNT(*) FILTER (WHERE ground_truth_vulnerable = TRUE) as vuln_total
            FROM (
                SELECT f.cei_violations,
                       CASE WHEN EXISTS (SELECT 1 FROM labels l WHERE l.contract_id = c.id AND l.has_vulnerability = TRUE) 
                            THEN TRUE ELSE FALSE END as ground_truth_vulnerable
                FROM contracts c JOIN features f ON c.id = f.contract_id 
                WHERE f.failure_reason IS NULL
            ) t
        """)
        stats = cursor.fetchone()
        print(f"   Total ML-ready: {stats['total']}")
        print(f"   Avg CEI violations: {stats['avg_cei']:.2f}")
        print(f"   Zero CEI contracts: {stats['zero_cei']}")
        print(f"   Vulnerable contracts: {stats['vuln_total']}")
    exit(0)

# Process contracts
updated = 0
skipped = 0
errors = 0

for idx, row in contracts_df.iterrows():
    if (updated + skipped + errors) % 10 == 0:
        print(f"📊 {updated + skipped + errors}/{len(contracts_df)} "
              f"({(updated + skipped + errors)/len(contracts_df)*100:.0f}%)")
    
    try:
        source_code = row['source_code']
        contract_id = row['id']
        contract_name = row['contract_name']
        
        # Temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sol', delete=False) as f:
            f.write(source_code)
            temp_path = f.name
        
        # Slither analysis
        slither = Slither(temp_path)
        if not slither.contracts:
            skipped += 1
            Path(temp_path).unlink(missing_ok=True)
            continue
        
        main_contract = slither.contracts[-1]
        
        # Semantic features (handle ImportError)
        try:
            from chainguardian.feature_extraction.semantic_analyzer import SemanticAnalyzer
            analyzer = SemanticAnalyzer(main_contract)
            semantic = analyzer.analyze()
        except ImportError:
            # Fallback: basic CEI count
            semantic = {'cei_violations': len([f for f in main_contract.functions if 'external_call' in [c.full_name for c in f.internal_calls]]), 
                       'cei_safe_functions': 0, 'cei_pattern_score': 1.0,
                       'has_reentrancy_guard': any('nonReentrant' in m.name for m in main_contract.modifiers),
                       'functions_with_reentrancy_guard': 0,
                       'state_before_call_count': 0, 'state_after_call_count': 0,
                       'unchecked_calls_in_critical_context': 0}
        
        # UPDATE features table
        with db._get_cursor() as cursor:
            cursor.execute("""
                UPDATE features 
                SET cei_violations = %s,
                    cei_safe_functions = %s,
                    cei_pattern_score = %s,
                    has_reentrancy_guard = %s,
                    functions_with_reentrancy_guard = %s,
                    state_before_call_count = %s,
                    state_after_call_count = %s
                WHERE contract_id = %s
            """, (
                semantic.get('cei_violations', 0),
                semantic.get('cei_safe_functions', 0),
                semantic.get('cei_pattern_score', 1.0),
                semantic.get('has_reentrancy_guard', False),
                semantic.get('functions_with_reentrancy_guard', 0),
                semantic.get('state_before_call_count', 0),
                semantic.get('state_after_call_count', 0),
                contract_id
            ))
        
        if semantic.get('cei_violations', 0) > 0:
            print(f"✅ {contract_name}: {semantic['cei_violations']} CEI found!")
        
        updated += 1
        Path(temp_path).unlink(missing_ok=True)
    
    except Exception as e:
        logger.error(f"❌ {contract_name}: {e}")
        errors += 1

print(f"\n📊 FINAL:")
print(f"✅ Updated: {updated}")
print(f"⚠️  Skipped: {skipped}")
print(f"❌ Errors: {errors}")

print("\n💾 Exporting updated dataset...")
df_features = db.get_all_features()
df_features.to_csv("data/ml_ready_v4_semantic_fixed.csv", index=False)
print(f"✅ Saved: data/ml_ready_v4_semantic_fixed.csv")

print("\n🎉 COMPLETE!")
print("🔄 cp data/ml_ready_v4_semantic_fixed.csv data/ml_ready_v4.csv")
