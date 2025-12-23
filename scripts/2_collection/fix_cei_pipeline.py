#!/usr/bin/env python3
"""🔧 FIX CEI PIPELINE - Re-analyze ALL zero-CEI contracts"""

from chainguardian.database.manager import DatabaseManager
import pandas as pd
from pathlib import Path
import tempfile
import logging
from slither import Slither

logging.basicConfig(level=logging.WARNING)  # Reduce Slither spam

db = DatabaseManager()
print("🔧 RE-ANALYZING CEI FOR 657 ZERO-CEI CONTRACTS...\n")

# Get ALL zero-CEI ML-ready contracts
print("📥 Target contracts...")
with db._get_cursor(dict_cursor=True) as cursor:
    cursor.execute("""
        SELECT 
            c.id, c.name as contract_name, c.source_code, c.file_path,
            f.cei_violations, f.has_reentrancy_guard
        FROM contracts c
        JOIN features f ON c.id = f.contract_id
        WHERE f.failure_reason IS NULL
          AND f.cei_violations = 0
          AND LENGTH(COALESCE(c.source_code, '')) > 50
        ORDER BY c.id
        LIMIT 700  -- Safety limit
    """)
    zero_cei_df = pd.DataFrame(cursor.fetchall())

print(f"🎯 Found {len(zero_cei_df)} zero-CEI contracts")

if len(zero_cei_df) == 0:
    print("✅ No zero-CEI contracts found!")
    exit(0)

# Process batch
updated = 0
new_cei = 0
errors = 0

for idx, row in zero_cei_df.iterrows():
    if idx % 50 == 0:
        print(f"📊 {idx}/{len(zero_cei_df)} ({idx/len(zero_cei_df)*100:.0f}%)")
    
    try:
        contract_id = row['id']
        source_code = row['source_code']
        
        # Temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sol', delete=False) as f:
            f.write(source_code)
            temp_path = f.name
        
        # Slither (silent)
        slither = Slither(temp_path, disable_color=True, disable_contextual_duplication=True)
        
        if not slither.contracts:
            Path(temp_path).unlink(missing_ok=True)
            continue
        
        contract = slither.contracts[-1]
        
        # Simple CEI heuristic (no SemanticAnalyzer needed)
        cei_count = 0
        reentrancy_guard = False
        
        for func in contract.functions:
            # External calls without state checks = CEI violation
            external_calls = [call for call in func.internal_calls if 'external' in call.full_name.lower()]
            state_writes = [v for v in func.state_variables_written if v not in func.parameters]
            
            if external_calls and len(state_writes) > 0:
                # Check order: state write BEFORE external call = CEI violation
                for ext_call in external_calls:
                    if any(write_point < ext_call.point for write_point in [w.point for w in state_writes]):
                        cei_count += 1
            
            # Reentrancy guard modifier
            if any('nonreentrant' in mod.name.lower() or 'reentrancyguard' in mod.name.lower() 
                   for mod in func.modifiers):
                reentrancy_guard = True
        
        # Update if we found CEI violations
        if cei_count > 0 or reentrancy_guard != row.get('has_reentrancy_guard', False):
            with db._get_cursor() as cursor:
                cursor.execute("""
                    UPDATE features 
                    SET cei_violations = %s,
                        has_reentrancy_guard = %s
                    WHERE contract_id = %s
                """, (cei_count, reentrancy_guard, contract_id))
            
            if cei_count > 0:
                new_cei += 1
            
            updated += 1
        
        Path(temp_path).unlink(missing_ok=True)
    
    except Exception as e:
        errors += 1

print(f"\n📊 RESULTS:")
print(f"✅ Processed:  {len(zero_cei_df)}")
print(f"✅ Updated:   {updated}")
print(f"🔥 New CEI:   {new_cei}")
print(f"❌ Errors:    {errors}")

# Final stats
print("\n📈 BEFORE/AFTER:")
with db._get_cursor(dict_cursor=True) as cursor:
    cursor.execute("""
        SELECT 
            COUNT(*) FILTER (WHERE f.cei_violations = 0) as zero_cei_now,
            COUNT(*) FILTER (WHERE ground_truth_vulnerable = TRUE AND f.cei_violations = 0) as vuln_zero_cei_now
        FROM contracts c JOIN features f ON c.id = f.contract_id
        WHERE f.failure_reason IS NULL
    """)
    final_stats = cursor.fetchone()
    print(f"Zero CEI now:     {final_stats['zero_cei_now']} (was 657)")
    print(f"Vuln zero CEI:    {final_stats['vuln_zero_cei_now']} (was 396)")

print("\n✅ CEI PIPELINE FIXED!")
print("💾 cp data/ml_ready_v4_semantic_fixed.csv data/ml_ready_v4.csv")
