#!/usr/bin/env python3
"""🔥 CEI EXTRACTION for recovered source"""

from chainguardian.database.manager import DatabaseManager
from slither import Slither
import tempfile
from pathlib import Path
import logging

logging.basicConfig(level=logging.ERROR)
db = DatabaseManager()

print("🔥 CEI EXTRACTION...")

with db._get_cursor() as cursor:
    cursor.execute("""
        SELECT c.id, c.source_code
        FROM contracts c JOIN features f ON c.id = f.contract_id
        JOIN labels l ON c.id = l.contract_id
        WHERE f.failure_reason IS NULL AND f.cei_violations = 0 
          AND l.has_vulnerability = TRUE AND c.source_code IS NOT NULL 
          AND LENGTH(c.source_code) > 100
    """)
    
    targets = [(row[0], row[1]) for row in cursor.fetchall()]
    print(f"🎯 {len(targets)} contracts with source")

fixed = 0
for idx, (contract_id, source_code) in enumerate(targets):
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sol', delete=False) as tmp:
            tmp.write(source_code)
            tmp_path = tmp.name
        
        slither = Slither(tmp_path)
        Path(tmp_path).unlink(missing_ok=True)
        
        if slither.contracts:
            cei_count = sum(1 for c in slither.contracts for f in c.functions 
                          if any(hasattr(call, 'contract') and call.contract 
                                for node in f.nodes for call in getattr(node, 'internal_calls', [])))
            
            if cei_count > 0:
                cursor.execute("UPDATE features SET cei_violations = %s WHERE contract_id = %s", 
                             (cei_count, contract_id))
                fixed += 1
                if idx < 3: print(f"✅ ID {contract_id}: {cei_count} CEI")
    
    except: pass

print(f"\n✅ FIXED {fixed} contracts!")
