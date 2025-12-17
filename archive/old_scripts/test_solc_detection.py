"""
Test Solc Version Detection
============================

Run this with: poetry run python scripts/test_solc_detection.py
"""

import subprocess
import sys

print("\n" + "="*70)
print("TESTING SOLC VERSION DETECTION")
print("="*70 + "\n")

# Test different methods to call solc-select
methods = [
    ("Direct call", ["solc-select", "versions"]),
    ("Python -m solc_select", [sys.executable, "-m", "solc_select", "versions"]),
    ("Python -m solc-select (hyphen)", [sys.executable, "-m", "solc-select", "versions"]),
]

working_method = None

for name, cmd in methods:
    print(f"Testing: {name}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout:
            print(f"✅ SUCCESS!")
            print(f"Output preview: {result.stdout[:100]}...")
            
            # Count versions
            versions = [
                line.split()[0] 
                for line in result.stdout.split('\n') 
                if line.strip() and line[0].isdigit()
            ]
            print(f"Found {len(versions)} versions")
            
            if len(versions) > 0:
                working_method = cmd
                print(f"Sample versions: {versions[:5]}")
            
            break
        else:
            print(f"❌ Failed: returncode={result.returncode}")
            if result.stderr:
                print(f"Error: {result.stderr[:100]}")
    
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print()

if working_method:
    print("="*70)
    print("✅ FOUND WORKING METHOD")
    print("="*70)
    print(f"Command: {working_method}")
    print("\nYour pipeline should use this command to get versions.")
    print("\nNow let's test version switching...")
    print()
    
    # Test switching
    print("="*70)
    print("TESTING VERSION SWITCHING")
    print("="*70)
    print()
    
    test_version = "0.8.20"
    switch_cmd = working_method[:-1] + ["use", test_version]
    
    print(f"Trying to switch to {test_version}...")
    print(f"Command: {' '.join(switch_cmd)}")
    
    try:
        result = subprocess.run(
            switch_cmd,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print(f"✅ Successfully switched to {test_version}")
        else:
            print(f"❌ Failed to switch")
            print(f"Error: {result.stderr}")
    
    except Exception as e:
        print(f"❌ Exception: {e}")
    
else:
    print("="*70)
    print("❌ NO WORKING METHOD FOUND")
    print("="*70)
    print("\nThis means solc-select is not accessible from Python subprocess.")
    print("\nPossible issues:")
    print("1. solc-select not installed: poetry add solc-select")
    print("2. Running outside Poetry environment")
    print("3. solc-select installed differently")
    print("\nTry running manually:")
    print("  poetry run solc-select versions")

print("\n" + "="*70)
print("DIAGNOSIS COMPLETE")
print("="*70 + "\n")