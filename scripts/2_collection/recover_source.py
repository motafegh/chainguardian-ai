#!/usr/bin/env python3
"""🔥 RECOVER SWC SOURCE CODE"""

from chainguardian.database.manager import DatabaseManager
import requests
import time

db = DatabaseManager()

# SWC Registry contracts (your exact names!)
swc_sources = {
    'open_address_lottery': 'https://raw.githubusercontent.com/smartcontractworkshop/SWC-registry/master/buggy_contracts/OpenAddressLottery.sol',
    'name_registrar': 'https://raw.githubusercontent.com/smartcontractworkshop/SWC-registry/master/buggy_contracts/name_registrar.sol',
    'crypto_roulette': 'https://raw.githubusercontent.com/smartcontractworkshop/SWC-registry/master/buggy_contracts/CryptoRoulette.sol',
    'phishable': 'https://raw.githubusercontent.com/smartcontractworkshop/SWC-registry/master/buggy_contracts/phishable.sol',
    'parity_wallet_bug_1': 'https://raw.githubusercontent.com/smartcontractworkshop/SWC-registry/master/buggy_contracts/parity_wallet_bug1.sol',
    'arbitrary_location_write_simple': 'https://raw.githubusercontent.com/smartcontractworkshop/SWC-registry/master/buggy_contracts/arbitrary_location_write_simple.sol',
    'wallet_03_wrong_constructor': 'https://raw.githubusercontent.com/smartcontractworkshop/SWC-registry/master/buggy_contracts/wallet_03_wrong_constructor.sol',
    'rubixi': 'https://raw.githubusercontent.com/smartcontractworkshop/SWC-registry/master/buggy_contracts/rubixi.sol',
    'incorrect_constructor_name1': 'https://raw.githubusercontent.com/smartcontractworkshop/SWC-registry/master/buggy_contracts/incorrect_constructor_name1.sol',
    'wallet_02_refund_nosub': 'https://raw.githubusercontent.com/smartcontractworkshop/SWC-registry/master/buggy_contracts/wallet_02_refund_nosub.sol'
}

print("🔥 RECOVERING SWC SOURCE CODE...")
recovered = 0

with db._get_cursor() as cursor:
    for name, url in swc_sources.items():
        try:
            print(f"📥 {name}...")
            resp = requests.get(url, timeout=10)
            source_code = resp.text
            
            # Update matching contract
            cursor.execute("""
                UPDATE contracts 
                SET source_code = %s 
                WHERE LOWER(name) LIKE %s 
                AND source_code IS NULL OR LENGTH(source_code) = 0
            """, (source_code, f'%{name}%'))
            
            if cursor.rowcount > 0:
                recovered += cursor.rowcount
                print(f"✅ {name}: {len(source_code)} chars")
            
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ {name}: {e}")

print(f"\n🎉 RECOVERED {recovered} CONTRACTS!")
