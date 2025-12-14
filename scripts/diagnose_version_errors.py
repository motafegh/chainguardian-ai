"""
Diagnostic tool for VERSION_MISMATCH errors
Helps identify which pragma versions are causing issues
"""

import pandas as pd
import re
import subprocess
from pathlib import Path
from collections import defaultdict


def get_installed_versions():
    """Get list of installed Solidity versions"""
    try:
        result = subprocess.run(
            ["solc-select", "versions"],
            capture_output=True,
            text=True,
            check=True
        )
        versions = []
        for line in result.stdout.split('\n'):
            if line.strip():
                version = line.split()[0]
                if version and version[0].isdigit():
                    versions.append(version)
        return sorted(versions, key=lambda v: tuple(map(int, v.split('.'))))
    except Exception as e:
        print(f"Error getting installed versions: {e}")
        return []


def analyze_pragma_patterns(csv_path):
    """Analyze pragma patterns causing VERSION_MISMATCH errors"""
    df = pd.read_csv(csv_path)
    
    # Filter for VERSION_MISMATCH errors
    version_errors = df[df['failure_reason'] == 'VERSION_MISMATCH']
    
    print(f"\n{'='*70}")
    print("VERSION MISMATCH ANALYSIS")
    print('='*70)
    print(f"Total VERSION_MISMATCH errors: {len(version_errors)}")
    
    # Extract pragma versions
    pragma_pattern = r'pragma solidity ([^\n]+)'
    pragmas = []
    caret_pragmas = []
    range_pragmas = []
    
    for error_msg in version_errors['error_message']:
        match = re.search(pragma_pattern, error_msg)
        if match:
            pragma = match.group(1)
            pragmas.append(pragma)
            
            if '^' in pragma:
                caret_pragmas.append(pragma)
            elif '>=' in pragma or '<' in pragma:
                range_pragmas.append(pragma)
    
    # Analyze patterns
    print(f"\n📊 Pragma Pattern Breakdown:")
    print(f"   Caret (^) pragmas: {len(caret_pragmas)}")
    print(f"   Range (>=<) pragmas: {len(range_pragmas)}")
    print(f"   Other pragmas: {len(pragmas) - len(caret_pragmas) - len(range_pragmas)}")
    
    # Top problematic pragmas
    pragma_counts = pd.Series(pragmas).value_counts()
    print(f"\n🔍 Top 15 Problematic Pragmas:")
    for pragma, count in pragma_counts.head(15).items():
        print(f"   {pragma}: {count} contracts")
    
    # Analyze caret pragmas specifically
    if caret_pragmas:
        print(f"\n🔍 Caret Pragma Analysis:")
        caret_counts = pd.Series(caret_pragmas).value_counts()
        for pragma, count in caret_counts.head(10).items():
            version_match = re.search(r'([\d.]+)', pragma)
            if version_match:
                version = version_match.group(1)
                print(f"   ^{version}: {count} contracts")
    
    # Get installed versions
    installed = get_installed_versions()
    print(f"\n📦 Installed Versions: {len(installed)} total")
    if installed:
        print(f"   Earliest: {installed[0]}")
        print(f"   Latest: {installed[-1]}")
        print(f"   Sample: {installed[::len(installed)//10]}")  # Show every 10th version
    
    # Check for missing versions
    if caret_pragmas:
        required_versions = set()
        for pragma in caret_pragmas:
            match = re.search(r'([\d.]+)', pragma)
            if match:
                required_versions.add(match.group(1))
        
        missing = required_versions - set(installed)
        if missing:
            print(f"\n⚠️ Missing versions for caret pragmas:")
            for v in sorted(missing, key=lambda v: tuple(map(int, v.split('.')))):
                print(f"   {v}")
    
    # Show sample errors
    print(f"\n📝 Sample Error Messages:")
    for i, error_msg in enumerate(version_errors['error_message'].head(3)):
        print(f"\n--- Error {i+1} ---")
        # Extract just the relevant part
        lines = error_msg.split('\n')
        for line in lines[:5]:  # First 5 lines
            if 'pragma' in line.lower() or 'version' in line.lower():
                print(line)
    
    print('='*70 + '\n')
    
    return {
        'total_errors': len(version_errors),
        'caret_pragmas': len(caret_pragmas),
        'range_pragmas': len(range_pragmas),
        'installed_versions': len(installed),
        'missing_versions': missing if 'missing' in locals() else set()
    }


def generate_install_commands(missing_versions):
    """Generate solc-select install commands for missing versions"""
    if not missing_versions:
        return None
    
    # Group versions by major.minor
    version_groups = defaultdict(list)
    for v in sorted(missing_versions, key=lambda v: tuple(map(int, v.split('.')))):
        parts = v.split('.')
        key = f"{parts[0]}.{parts[1]}"
        version_groups[key].append(v)
    
    print(f"\n🔧 Recommended Install Commands:")
    print("="*50)
    
    # Generate commands
    for major_minor, versions in version_groups.items():
        # For each major.minor, install the latest version
        latest = max(versions, key=lambda v: tuple(map(int, v.split('.'))))
        print(f"poetry run solc-select install {latest}")
    
    # Also suggest installing all if many are missing
    if len(missing_versions) > 20:
        print(f"\n# Or install all versions at once:")
        print(f"poetry run solc-select install all")


if __name__ == "__main__":
    csv_path = Path("data/collected_dataset.csv")
    if csv_path.exists():
        analysis = analyze_pragma_patterns(csv_path)
        
        if analysis['missing_versions']:
            generate_install_commands(analysis['missing_versions'])
    else:
        print(f"Dataset not found at {csv_path}")