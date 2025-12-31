#!/usr/bin/env python3
"""
Real Contract Extraction Test
Tests tier-based feature extraction on real vulnerable contracts from Damn Vulnerable DeFi
"""

import sys
from pathlib import Path
import logging
import pandas as pd
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def test_real_contract_extraction():
    """Test extraction on real vulnerable contracts."""

    print("=" * 80)
    print("REAL CONTRACT EXTRACTION TEST - Damn Vulnerable DeFi")
    print("=" * 80)

    # Import pipeline
    try:
        from chainguardian.feature_extraction.pipeline import FeaturePipeline
        print("✓ Pipeline imported successfully\n")
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

    # Real contracts from Damn Vulnerable DeFi (intentionally vulnerable!)
    test_contracts = [
        {
            'path': Path("blockchain/damn-vulnerable-defi/contracts/naive-receiver/NaiveReceiverLenderPool.sol"),
            'name': "NaiveReceiverLenderPool",
            'expected_vuln': "Flash loan vulnerability",
            'description': "Flash loan pool with naive receiver"
        },
        {
            'path': Path("blockchain/damn-vulnerable-defi/contracts/unstoppable/UnstoppableLender.sol"),
            'name': "UnstoppableLender",
            'expected_vuln': "Denial of Service",
            'description': "Lender pool with DOS vulnerability"
        },
        {
            'path': Path("blockchain/damn-vulnerable-defi/contracts/truster/TrusterLenderPool.sol"),
            'name': "TrusterLenderPool",
            'expected_vuln': "Arbitrary execution",
            'description': "Trusted flash loan pool"
        },
        {
            'path': Path("blockchain/damn-vulnerable-defi/contracts/side-entrance/SideEntranceLenderPool.sol"),
            'name': "SideEntranceLenderPool",
            'expected_vuln': "Reentrancy",
            'description': "Side entrance flash loan"
        },
        {
            'path': Path("blockchain/damn-vulnerable-defi/contracts/selfie/SimpleGovernance.sol"),
            'name': "SimpleGovernance",
            'expected_vuln': "Governance attack",
            'description': "Simple governance contract"
        },
    ]

    # Test both modes
    modes = ['comprehensive', 'maximum']
    results_all = []

    for mode in modes:
        print("\n" + "=" * 80)
        print(f"TESTING MODE: {mode.upper()}")
        print("=" * 80 + "\n")

        # Initialize pipeline
        pipeline = FeaturePipeline(mode=mode)

        successful = 0
        failed = 0

        for i, contract_info in enumerate(test_contracts, 1):
            contract_path = contract_info['path']
            contract_name = contract_info['name']

            print(f"[{i}/{len(test_contracts)}] Testing: {contract_name}")
            print(f"  Description: {contract_info['description']}")
            print(f"  Expected vulnerability: {contract_info['expected_vuln']}")
            print(f"  Path: {contract_path}")

            # Check if file exists
            if not contract_path.exists():
                print(f"  ✗ File not found: {contract_path}")
                failed += 1
                continue

            # Extract features
            try:
                features = pipeline.analyze_contract(
                    contract_path,
                    contract_name,
                    metadata={
                        'dataset': 'damn-vulnerable-defi',
                        'expected_vuln_type': contract_info['expected_vuln']
                    }
                )

                if features.get('extraction_status') == 'success':
                    print(f"  ✓ Extraction successful")
                    print(f"    Features extracted: {len(features)}")
                    print(f"    Security risk score: {features.get('security_risk_score', 0)}")
                    print(f"    CEI violations: {features.get('cei_violations', 0)}")
                    print(f"    High severity count: {features.get('high_severity_count', 0)}")

                    # Check for specific vulnerabilities
                    print(f"    Vulnerability flags:")
                    print(f"      has_reentrancy: {features.get('has_reentrancy', False)}")
                    print(f"      has_access_control_issue: {features.get('has_access_control_issue', False)}")
                    print(f"      has_unchecked_call: {features.get('has_unchecked_call', False)}")

                    results_all.append({
                        'mode': mode,
                        'contract': contract_name,
                        'status': 'success',
                        'features_count': len(features),
                        'risk_score': features.get('security_risk_score', 0),
                        'cei_violations': features.get('cei_violations', 0),
                        'high_severity': features.get('high_severity_count', 0),
                        'expected_vuln': contract_info['expected_vuln']
                    })
                    successful += 1
                else:
                    print(f"  ✗ Extraction failed: {features.get('failure_reason', 'Unknown')}")
                    results_all.append({
                        'mode': mode,
                        'contract': contract_name,
                        'status': 'failed',
                        'features_count': 0,
                        'failure_reason': features.get('failure_reason', 'Unknown')
                    })
                    failed += 1

            except Exception as e:
                print(f"  ✗ Exception: {e}")
                results_all.append({
                    'mode': mode,
                    'contract': contract_name,
                    'status': 'error',
                    'error': str(e)
                })
                failed += 1

            print()

        print("\n" + "=" * 80)
        print(f"MODE {mode.upper()} SUMMARY")
        print("=" * 80)
        print(f"Total contracts: {len(test_contracts)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Success rate: {(successful/len(test_contracts)*100):.1f}%")

    # Overall summary
    print("\n" + "=" * 80)
    print("OVERALL TEST SUMMARY")
    print("=" * 80)

    df = pd.DataFrame(results_all)
    print(df.to_string(index=False))

    success_count = len(df[df['status'] == 'success'])
    total_tests = len(df)

    print(f"\nTotal tests: {total_tests} ({len(modes)} modes × {len(test_contracts)} contracts)")
    print(f"Successful extractions: {success_count}")
    print(f"Failed extractions: {total_tests - success_count}")
    print(f"Overall success rate: {(success_count/total_tests*100):.1f}%")

    # Save results
    output_file = f"test_results_real_contracts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(output_file, index=False)
    print(f"\n✓ Results saved to: {output_file}")

    print("\n" + "=" * 80)
    if success_count == total_tests:
        print("✅ ALL TESTS PASSED - Real contract extraction is production-ready!")
    else:
        print(f"⚠️  PARTIAL SUCCESS - {success_count}/{total_tests} extractions succeeded")
    print("=" * 80)

    return success_count == total_tests


if __name__ == "__main__":
    success = test_real_contract_extraction()
    sys.exit(0 if success else 1)
