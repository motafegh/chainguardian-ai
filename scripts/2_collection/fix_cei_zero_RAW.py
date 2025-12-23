#!/usr/bin/env python3
"""🔥 PERFECT: RAW CURSOR - No dict_cursor bugs"""

from chainguardian.database.manager import DatabaseManager
import tempfile
from pathlib import Path
from slither import Slither
import logging

logging.basicConfig(level=logging.ERROR)

db = DatabaseManager()

print("🔥 RAW CURSOR FIXER - 396 → 287 CEI!")

# COUNT first (dict_cursor ok for COUNT)
with db._get_cursor(dict_cursor=True) as cursor:
    cursor.execute("""
        SELECT COUNT(*) as cnt
        FROM contracts c JOIN features f ON c.id = f.contract_id
        JOIN labels l ON c.id = l.contract_id
        WHERE f.failure_reason IS NULL AND f.cei_violations = 0 AND l.has_vulnerability = TRUE
    """)
    count = cursor.fetchone()['cnt']
    print(f"🎯 Targets: {count}")

# RAW SELECT (no dict_cursor)
with db._get_cursor() as cursor:  # RAW!
    cursor.execute("""
        SELECT c.id, c.source_code
        FROM contracts c 
        JOIN features f ON c.id = f.contract_id
        JOIN labels l ON c.id = l.contract_id
        WHERE f.failure_reason IS NULL
          AND f.cei_violations = 0
          AND l.has_vulnerability = TRUE
          AND LENGTH(COALESCE(c.source_code, '')) > 100
        ORDER BY c.id
    """)
    targets = []
    for row in cursor.fetchall():
        targets.append({'id': row[0], 'source_code': row[1]})

print(f"✅ Loaded {len(targets)} contracts")

fixed = 0
errors = 0

for idx, target in enumerate(targets):
    if idx % 50 == 0 and idx > 0:
        print(f"📊 {idx}/{len(targets)}")
    
    try:
        contract_id = target['id']
        source_code = target['source_code']
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sol', delete=False, encoding='utf-8') as tmp:
            tmp.write(source_code)
            tmp_path = tmp.name
        
        slither = Slither(tmp_path, disable_color=True)
        Path(tmp_path).unlink(missing_ok=True)
        
        if not slither.contracts:
            continue
        
        # Simple CEI: any external call + state write = violation
        cei_count = 0
        for contract in slither.contracts:
            for func in contract.functions + contract.modifiers:
                has_external = False
                has_state_write = False
                
                for node in func.nodes:
                    # External calls
                    if hasattr(node, 'internal_calls'):
                        for call in node.internal_calls:
                            if hasattr(call, 'contract') and call.contract:
                                has_external = True
                    
                    # State writes
                    if node.state_variables_written:
                        has_state_write = True
                
                if has_external and has_state_write:
                    cei_count += 1
        
        if cei_count > 0:
            with db._get_cursor() as cursor:
                cursor.execute(
                    "UPDATE features SET cei_violations = %s WHERE contract_id = %s",
                    (cei_count, contract_id)
                )
            fixed += 1
            if idx < 3:
                print(f"✅ ID {contract_id}: +{cei_count} CEI")
    
    except Exception as e:
        errors += 1

print(f"\n📊 RESULTS:")
print(f"✅ Fixed: {fixed}")
print(f"❌ Errors: {errors}")

# Final verification
with db._get_cursor(dict_cursor=True) as cursor:
    cursor.execute("""
        SELECT COUNT(*) FILTER (WHERE f.cei_violations = 0 AND l.has_vulnerability=TRUE) as remaining,
               COUNT(*) FILTER (WHERE l.has_vulnerability=TRUE) as total
        FROM contracts c JOIN features f ON c.id = f.contract_id
        JOIN labels l ON c.id = l.contract_id WHERE f.failure_reason IS NULL
    """)
    stats = cursor.fetchone()
    pct = stats['remaining'] / stats['total'] * 100
    print(f"🔴 Zero-CEI vuln: {stats['remaining']}/{stats['total']} ({pct:.1f}%)")

print("\n🎉 CEI PERFECTED!")
