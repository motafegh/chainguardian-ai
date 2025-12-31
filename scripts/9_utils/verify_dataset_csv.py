"""
Verify Production Dataset Quality

Checks dataset meets production requirements:
1. Multiple sources for both vulnerable and safe
2. Balanced distribution
3. No single-source dominance
4. Sufficient samples per source
"""

from pathlib import Path
import logging
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from chainguardian.database.manager import DatabaseManager
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_dataset():
    """Verify production dataset meets quality requirements."""
    
    db = DatabaseManager()
    df = db.get_all_features()
    
    print("\n" + "="*70)
    print("🔍 PRODUCTION DATASET VERIFICATION")
    print("="*70)
    
    # Clean dataset (remove failures)
    df_clean = df[df['failure_reason'].isna()]
    
    print(f"\n📊 DATASET SIZE:")
    print(f"   Total contracts: {len(df)}")
    print(f"   Clean contracts: {len(df_clean)}")
    print(f"   Failed extractions: {len(df) - len(df_clean)}")
    print(f"   Success rate: {len(df_clean)/len(df)*100:.1f}%")
    
    # Source diversity
    print(f"\n📂 DATA SOURCES:")
    sources = df_clean['data_source'].value_counts()
    for source, count in sources.items():
        percentage = count / len(df_clean) * 100
        print(f"   {source:30s}: {count:4d} ({percentage:5.1f}%)")
    
    # Check vulnerable sources
    vulnerable_sources = df_clean[df_clean['data_source'].str.contains('vulnerable|smartbugs', na=False, case=False)]
    vuln_source_counts = vulnerable_sources['data_source'].value_counts()
    
    print(f"\n🔥 VULNERABLE CONTRACTS:")
    print(f"   Total: {len(vulnerable_sources)}")
    if len(vuln_source_counts) > 0:
        print(f"   Sources: {len(vuln_source_counts)}")
        for source, count in vuln_source_counts.items():
            print(f"      {source:25s}: {count:4d}")
    else:
        print(f"   ⚠️  No vulnerable contracts found!")
    
    # Check safe sources
    safe_sources = df_clean[df_clean['data_source'].str.contains('safe|openzeppelin', na=False, case=False)]
    safe_source_counts = safe_sources['data_source'].value_counts()
    
    print(f"\n🔒 SAFE CONTRACTS:")
    print(f"   Total: {len(safe_sources)}")
    if len(safe_source_counts) > 0:
        print(f"   Sources: {len(safe_source_counts)}")
        for source, count in safe_source_counts.items():
            print(f"      {source:25s}: {count:4d}")
    else:
        print(f"   ⚠️  No safe contracts found!")
    
    # Balance check
    print(f"\n⚖️  CLASS BALANCE:")
    if len(vulnerable_sources) > 0 and len(safe_sources) > 0:
        ratio = len(safe_sources) / len(vulnerable_sources)
        vuln_pct = len(vulnerable_sources) / len(df_clean) * 100
        print(f"   Vulnerable: {len(vulnerable_sources)} ({vuln_pct:.1f}%)")
        print(f"   Safe: {len(safe_sources)} ({100-vuln_pct:.1f}%)")
        print(f"   Ratio: 1:{ratio:.2f}")
        
        if vuln_pct >= 30 and vuln_pct <= 50:
            print(f"   ✅ GOOD balance (30-50% vulnerable)")
        elif vuln_pct >= 20:
            print(f"   ⚠️  Acceptable (use SMOTE or class weights)")
        else:
            print(f"   ❌ Poor balance (need more vulnerable contracts)")
    
    # Diversity requirements
    print(f"\n🎯 DIVERSITY REQUIREMENTS:")
    
    # Requirement 1: At least 2 vulnerable sources
    vuln_source_requirement = len(vuln_source_counts) >= 2
    print(f"   Vulnerable sources ≥ 2: {'✅ PASS' if vuln_source_requirement else '❌ FAIL'} ({len(vuln_source_counts)})")
    
    # Requirement 2: At least 2 safe sources
    safe_source_requirement = len(safe_source_counts) >= 2
    print(f"   Safe sources ≥ 2: {'✅ PASS' if safe_source_requirement else '❌ FAIL'} ({len(safe_source_counts)})")
    
    # Requirement 3: No single source > 70%
    max_source_pct = sources.max() / len(df_clean) * 100
    dominance_requirement = max_source_pct < 70
    print(f"   No source > 70%: {'✅ PASS' if dominance_requirement else '❌ FAIL'} (max: {max_source_pct:.1f}%)")
    
    # Requirement 4: At least 30 samples per source
    min_samples = sources.min()
    sample_requirement = min_samples >= 30
    print(f"   All sources ≥ 30 samples: {'✅ PASS' if sample_requirement else '⚠️  WARNING'} (min: {min_samples})")
    
    # Requirement 5: Total dataset ≥ 300
    size_requirement = len(df_clean) >= 300
    print(f"   Total size ≥ 300: {'✅ PASS' if size_requirement else '❌ FAIL'} ({len(df_clean)})")
    
    # Overall verdict
    all_requirements = [
        vuln_source_requirement,
        safe_source_requirement,
        dominance_requirement,
        size_requirement
    ]
    
    print(f"\n{'='*70}")
    if all(all_requirements):
        print("🎉 DATASET MEETS PRODUCTION REQUIREMENTS!")
        print("✅ Ready for ML training")
    else:
        print("⚠️  DATASET NEEDS IMPROVEMENT")
        if not vuln_source_requirement:
            print("   ❌ Need more vulnerable sources (add DeFi hacks)")
        if not safe_source_requirement:
            print("   ❌ Need more safe sources (add audited protocols)")
        if not dominance_requirement:
            print("   ❌ One source dominates (collect from other sources)")
        if not size_requirement:
            print("   ❌ Dataset too small (need at least 300 contracts)")
    
    print("="*70)
    
    # Save verification report
    report = {
        'total_contracts': len(df_clean),
        'vulnerable_contracts': len(vulnerable_sources),
        'safe_contracts': len(safe_sources),
        'vulnerable_sources': len(vuln_source_counts),
        'safe_sources': len(safe_source_counts),
        'max_source_percentage': float(max_source_pct),
        'min_samples_per_source': int(min_samples),
        'passes_requirements': all(all_requirements)
    }
    
    import json
    report_file = Path("data/production_dataset_verification.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Verification report saved: {report_file}")


if __name__ == "__main__":
    verify_dataset()