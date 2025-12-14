"""
Manual Contract Test - See Full Error
======================================

Tests ONE contract manually to see the complete error message.
"""

import sys
from pathlib import Path
import re
import subprocess
from slither import Slither

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def detect_version(file_path):
    """Detect version from pragma."""
    content = file_path.read_text(encoding='utf-8')
    
    match = re.search(
        r'pragma\s+solidity\s+([\^=~<>]*)\s*([\d.]+)',
        content
    )
    
    if match:
        operator = match.group(1)
        version = match.group(2)
        has_caret = '^' in operator
        return version, has_caret, operator
    
    return None, False, None

def get_installed_versions():
    """Get installed Solidity versions."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "solc_select", "versions"],
            capture_output=True,
            text=True,
            check=True
        )
        
        versions = set()
        for line in result.stdout.split('\n'):
            if line.strip():
                version = line.split()[0]
                if version and version[0].isdigit():
                    versions.add(version)
        
        return sorted(versions)
        
    except Exception as e:
        print(f"Error getting versions: {e}")
        return []

def find_best_version(required, has_caret, installed):
    """Find best version to use."""
    if not has_caret:
        # No caret - use exact if available
        if required in installed:
            return required
        
        # Find close match
        major, minor = required.split('.')[:2]
        compatible = [v for v in installed if v.startswith(f"{major}.{minor}.")]
        
        if compatible:
            best = max(compatible, key=lambda v: tuple(map(int, v.split('.'))))
            return best
        
        return None
    
    else:
        # Has caret - find highest compatible
        try:
            req_major, req_minor, req_patch = map(int, required.split('.'))
        except:
            return None
        
        compatible = []
        for v in installed:
            try:
                v_major, v_minor, v_patch = map(int, v.split('.'))
                
                # Same major
                if v_major != req_major:
                    continue
                
                # Check compatibility
                if req_major == 0 and req_minor == 0:
                    # 0.0.x - exact patch only
                    if v_minor == req_minor and v_patch >= req_patch:
                        compatible.append(v)
                elif req_major == 0:
                    # 0.x.y - higher minor/patch OK
                    if v_minor > req_minor or (v_minor == req_minor and v_patch >= req_patch):
                        compatible.append(v)
                else:
                    # x.y.z - higher minor/patch OK
                    if v_minor > req_minor or (v_minor == req_minor and v_patch >= req_patch):
                        compatible.append(v)
            except:
                continue
        
        if compatible:
            return max(compatible, key=lambda v: tuple(map(int, v.split('.'))))
        
        return required if required in installed else None

def switch_version(version):
    """Switch to Solidity version."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "solc_select", "use", version],
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except Exception as e:
        print(f"Failed to switch: {e.stderr}")
        return False

def test_contract(contract_path):
    """Test a single contract."""
    print(f"\n{'='*70}")
    print(f"TESTING CONTRACT: {contract_path.name}")
    print(f"{'='*70}\n")
    
    # Detect version
    version, has_caret, operator = detect_version(contract_path)
    
    print(f"Detected pragma: solidity {operator}{version}")
    print(f"Has caret: {has_caret}")
    print()
    
    # Get installed versions
    installed = get_installed_versions()
    print(f"Installed Solidity versions: {len(installed)}")
    print(f"Range: {min(installed)} to {max(installed)}")
    print()
    
    # Find best version
    best = find_best_version(version, has_caret, installed)
    print(f"Best version to use: {best}")
    print()
    
    if not best:
        print("❌ No compatible version found!")
        return
    
    # Switch to that version
    print(f"Switching to {best}...")
    if not switch_version(best):
        print("❌ Switch failed!")
        return
    
    print(f"✓ Switched to {best}")
    print()
    
    # Try to compile
    print(f"Attempting compilation...")
    print(f"{'='*70}\n")
    
    try:
        slither = Slither(
            str(contract_path),
            solc="solc",
            solc_disable_warnings=True,
            solc_args="--optimize"
        )
        
        print("✅ COMPILATION SUCCESS!")
        print(f"Contracts found: {len(slither.contracts)}")
        
    except Exception as e:
        print("❌ COMPILATION FAILED!")
        print(f"\nFULL ERROR MESSAGE:")
        print(f"{'='*70}")
        print(str(e))  # FULL ERROR - not truncated!
        print(f"{'='*70}\n")
        
        # Try to extract specific info
        error_str = str(e)
        
        if "requires different compiler version" in error_str.lower():
            print("\n🔍 This is a version mismatch error")
            
            # Try to extract version info
            import re
            version_match = re.search(
                r'current compiler is ([\d.]+).*requires ([\d.^<>=]+)',
                error_str,
                re.IGNORECASE | re.DOTALL
            )
            
            if version_match:
                current = version_match.group(1)
                required = version_match.group(2)
                print(f"Current compiler: {current}")
                print(f"Required: {required}")


if __name__ == "__main__":
    # Test one of the failing contracts
    # You can change this path to any failing contract
    
    test_files = [
        Path("blockchain/contracts/collected/Nsure_0x20945ca1.sol"),
        Path("blockchain/contracts/collected/SDT_0x73968b9a.sol"),
        Path("blockchain/contracts/collected/PENDLE_0x808507121b80c02388fad14726482e061b8da827.sol"),
    ]
    
    for test_file in test_files:
        if test_file.exists():
            test_contract(test_file)
            break
        else:
            print(f"File not found: {test_file}")
            print("Trying next...")
    else:
        print("\n❌ No test files found!")
        print("\nUsage:")
        print("1. Edit this script")
        print("2. Set test_file to path of a failing contract")
        print("3. Run: python test_one_contract.py")