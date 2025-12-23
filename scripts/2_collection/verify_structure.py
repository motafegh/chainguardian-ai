# save as: verify_structure.py
from pathlib import Path

def analyze_structure():
    base = Path("blockchain/contracts")
    
    print("📊 STRUCTURE ANALYSIS")
    print("=" * 60)
    
    # Count vulnerable contracts by category
    vuln_path = base / "new_vulnerable"
    if vuln_path.exists():
        print("\n🔴 VULNERABLE CONTRACTS:")
        for category in sorted(vuln_path.iterdir()):
            if category.is_dir():
                sol_files = list(category.rglob("*.sol"))
                if sol_files:
                    print(f"  {category.name}: {len(sol_files)} contracts")
    
    # Count safe contracts
    safe_path = base / "new_safe"
    if safe_path.exists():
        print("\n🟢 SAFE CONTRACTS:")
        for source in sorted(safe_path.iterdir()):
            if source.is_dir():
                sol_files = list(source.rglob("*.sol"))
                if sol_files:
                    print(f"  {source.name}: {len(sol_files)} contracts")
    
    # Misc (optional)
    misc_path = base / "misc"
    if misc_path.exists():
        print("\n⚪ MISC CONTRACTS:")
        for source in sorted(misc_path.iterdir()):
            if source.is_dir():
                sol_files = list(source.rglob("*.sol"))
                if sol_files:
                    print(f"  {source.name}: {len(sol_files)} contracts")
    
    print("=" * 60)
    
    # Totals
    total_vuln = sum(1 for f in vuln_path.rglob("*.sol") if f.is_file())
    total_safe = sum(1 for f in safe_path.rglob("*.sol") if f.is_file())
    
    print(f"\n📈 TOTALS:")
    print(f"  Vulnerable: {total_vuln} contracts")
    print(f"  Safe: {total_safe} contracts")
    print(f"  Grand Total: {total_vuln + total_safe} NEW contracts")
    
    # Check OpenZeppelin
    print(f"\n💡 OpenZeppelin in database: ~300 contracts (DO NOT REPROCESS)")
    
    return total_vuln, total_safe

if __name__ == "__main__":
    vuln, safe = analyze_structure()
    
    if vuln > 800 and safe > 50:
        print("\n✅ READY FOR INTEGRATION!")
        print(f"   Vulnerable/Safe ratio: {vuln/(vuln+safe)*100:.1f}%/{safe/(vuln+safe)*100:.1f}%")
    else:
        print("\n⚠️  Check downloads - some folders may be empty")