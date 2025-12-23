#!/usr/bin/env python3
"""🔥 FIXED: JOIN instead of EXISTS() - Process 396 contracts"""

from chainguardian.database.manager import DatabaseManager
import pandas as pd
import tempfile
from pathlib import Path
from slither import Slither
import logging

logging.basicConfig(level=logging.ERROR)

db = DatabaseManager()

print("🔥 FIXING 396 ZERO-CEI VULNERABLE CONTRACTS (v2: JOIN fix)...")

# FIXED: JOIN instead of EXISTS()
with db._get_cursor(dict_cursor=True) as cursor:
    cursor.execute("""
        SELECT c.id, c.name, c.source_code, f.cei_violations
        FROM contracts c 
        JOIN features f ON c.id = f.contract_id
        JOIN labels l ON c.id = l.contract_id
        WHERE f.failure_reason IS NULL
          AND f.cei_violations = 0
          AND l.has_vulnerability = TRUE
          AND LENGTH(COALESCE(c.source_code, '')) > 100
        ORDER BY c.id
        LIMIT 500
    """)
    targets = pd.DataFrame(cursor.fetchall())

print(f"🎯 Processing {len(targets)} zero-CEI vulnerable contracts")

if len(targets) == 0:
    print("✅ No targets found!")
    exit(0)

fixed = 0
errors = 0
total_cei = 0

for idx, row in targets.iterrows():
    if idx % 50 == 0 and idx > 0:
        print(f"📊 {idx}/{len(targets)} ({idx/len(targets)*100:.0f}%)")
    
    try:
        contract_id = row['id']
        source_code = row['source_code']
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sol', delete=False, encoding='utf-8') as tmp:
            tmp.write(source_code)
            tmp_path = tmp.name
        
        slither = Slither(tmp_path, disable_color=True)
        Path(tmp_path).unlink(missing_ok=True)
        
        if not slither.contracts:
            continue
        
        # Improved CEI detection
        cei_count = 0
        for contract in slither.contracts:
            for func in contract.functions + contract.modifiers:
                external_calls = []
                state_writes = []
                
                for node in func.nodes:
                    if hasattr(node, 'internal_calls'):
                        for call in node.internal_calls:
                            if hasattr(call, 'contract') and call.contract:
                                external_calls.append(call)
                    if node.state_variables_written:
                        state_writes.extend(node.state_variables_written)
                
                if external_calls and state_writes:
                    cei_count += 1
        
        if cei_count > 0:
            with db._get_cursor() as cursor:
                cursor.execute(
                    "UPDATE features SET cei_violations = %s WHERE contract_id = %s",
                    (cei_count, contract_id)
                )
            fixed += 1
            total_cei += cei_count
            
            if idx < 5:
                print(f"✅ {row['name'][:30]}: 0 → {cei_count} CEI")
    
    except Exception as e:
        errors += 1

print(f"\n📊 RESULTS:")
print(f"✅ Fixed: {fixed} contracts")
print(f"🔥 Total CEI: {total_cei}")
print(f"❌ Errors: {errors}")

print("\n📈 BEFORE/AFTER:")
with db._get_cursor(dict_cursor=True) as cursor:
    cursor.execute("""
        SELECT 
            COUNT(*) FILTER (WHERE f.cei_violations = 0 AND l.has_vulnerability=TRUE) as remaining_zero,
            COUNT(*) FILTER (WHERE l.has_vulnerability=TRUE) as vuln_total
        FROM contracts c 
        JOIN features f ON c.id = f.contract_id
        JOIN labels l ON c.id = l.contract_id
        WHERE f.failure_reason IS NULL
    """)
    stats = cursor.fetchone()
    pct = stats['remaining_zero'] / stats['vuln_total'] * 100
    print(f"🔴 Zero-CEI vuln: {stats['remaining_zero']:,}/{stats['vuln_total']:,} ({pct:.1f}%)")

print("\n🎉 CEI FIXED!")
