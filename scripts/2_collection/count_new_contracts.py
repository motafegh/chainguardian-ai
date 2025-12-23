# Save as: scripts/count_new_contracts.py
from pathlib import Path

def count_all_contracts():
    base = Path("blockchain/contracts")
    
    print("📊 DETAILED CONTRACT COUNT")
    print("="*70)
    
    # Vulnerable contracts with nested structure
    print("\n🔴 VULNERABLE CONTRACTS (new_vulnerable):")
    vulnerable_path = base / "new_vulnerable"
    total_vuln = 0
    
    for vuln_dir in sorted(vulnerable_path.iterdir()):
        if vuln_dir.is_dir():
            # Count .sol files in this directory and subdirectories
            sol_files = list(vuln_dir.rglob("*.sol"))
            count = len(sol_files)
            total_vuln += count
            
            # Show some examples
            examples = [f.name for f in sol_files[:3]]
            print(f"  {vuln_dir.name}: {count} contracts")
            if examples:
                print(f"     Examples: {', '.join(examples)}{'...' if count > 3 else ''}")
    
    # Safe contracts with nested structure
    print("\n🟢 SAFE CONTRACTS (new_safe):")
    safe_path = base / "new_safe"
    total_safe = 0
    
    # Walk through all safe contracts
    for sol_file in sorted(safe_path.rglob("*.sol")):
        if sol_file.is_file():
            rel_path = sol_file.relative_to(safe_path)
            print(f"  {rel_path}")
            total_safe += 1
    
    # Misc contracts (optional)
    print("\n⚪ MISC CONTRACTS (misc):")
    misc_path = base / "misc"
    total_misc = 0
    
    for sol_file in sorted(misc_path.rglob("*.sol")):
        if sol_file.is_file():
            rel_path = sol_file.relative_to(misc_path)
            print(f"  {rel_path}")
            total_misc += 1
    
    print("\n" + "="*70)
    print(f"📈 TOTALS:")
    print(f"  Vulnerable: {total_vuln}")
    print(f"  Safe:       {total_safe}")
    print(f"  Misc:       {total_misc}")
    print(f"  New Total:  {total_vuln + total_safe + total_misc}")
    
    # Check if we missed any .sol files
    print(f"\n🔍 Checking for missed files...")
    all_sol = list(base.rglob("*.sol"))
    print(f"  Total .sol files found: {len(all_sol)}")
    
    return total_vuln, total_safe, total_misc

if __name__ == "__main__":
    vuln, safe, misc = count_all_contracts()
    
    print(f"\n💡 Next steps:")
    print(f"  1. Process {vuln} vulnerable contracts")
    print(f"  2. Process {safe} safe contracts")
    print(f"  3. Optionally process {misc} misc contracts")
    print(f"\n⏰ Estimated time: {(vuln + safe) * 5 / 60:.1f} minutes")