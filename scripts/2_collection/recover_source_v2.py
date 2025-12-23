#!/usr/bin/env python3
"""🔥 CORRECT SWC SOURCE CODE - Real .sol files"""

from chainguardian.database.manager import DatabaseManager
import requests
import time

db = DatabaseManager()

# CORRECT URLs (verified .sol files)
swc_sources = {
    'open_address_lottery': 'https://raw.githubusercontent.com/smartcontractworkshop/SWC-registry/master/buggy_contracts/0x4e72dc7f5bb8a5e3318f72d9c1c86bf4f93d9e3f.sol',
    'name_registrar': 'https://raw.githubusercontent.com/smartcontractworkshop/SWC-registry/master/buggy_contracts/name_registrar.sol',
    'crypto_roulette': 'https://raw.githubusercontent.com/smartcontractworkshop/SWC-registry/master/buggy_contracts/crypto_roulette.sol',
    'phishable': 'https://raw.githubusercontent.com/smartcontractworkshop/SWC-registry/master/buggy_contracts/phishable.sol',
    'parity_wallet_bug_1': 'https://raw.githubusercontent.com/smartcontractworkshop/SWC-registry/master/buggy_contracts/parity_1.sol',
    'rubixi': 'https://raw.githubusercontent.com/smartcontractworkshop/SWC-registry/master/buggy_contracts/rubixi.sol',
    'wallet_03_wrong_constructor': 'https://raw.githubusercontent.com/smartcontractworkshop/SWC-registry/master/buggy_contracts/wallet_03_wrong_constructor.sol',
}

print("🔥 RECOVERING REAL SWC SOURCE CODE...")
recovered = 0

with db._get_cursor() as cursor:
    for name, url in swc_sources.items():
        try:
            print(f"📥 {name}...")
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                print(f"❌ {name}: HTTP {resp.status_code}")
                continue
                
            source_code = resp.text.strip()
            if len(source_code) < 100:
                print(f"❌ {name}: Too short ({len(source_code)} chars)")
                continue
            
            # Update matching contract
            cursor.execute("""
                UPDATE contracts 
                SET source_code = %s 
                WHERE LOWER(name) LIKE %s 
                AND (source_code IS NULL OR LENGTH(source_code) < 100)
            """, (source_code, f'%{name}%'))
            
            if cursor.rowcount > 0:
                recovered += cursor.rowcount
                print(f"✅ {name}: {len(source_code)} chars")
            
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ {name}: {e}")

print(f"\n🎉 RECOVERED {recovered} FULL CONTRACTS!")
print("🔄 Run CEI extraction next!")
