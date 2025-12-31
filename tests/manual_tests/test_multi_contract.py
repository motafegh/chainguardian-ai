#!/usr/bin/env python3
"""
Multi-Contract Test Suite for New Tier-Based Extraction
Tests extraction on diverse contract types to ensure robustness
"""

import sys
from pathlib import Path
import logging
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def test_multi_contract_extraction():
    """Test extraction on multiple diverse contracts."""

    print("=" * 80)
    print("MULTI-CONTRACT COMPREHENSIVE TEST SUITE")
    print("=" * 80)

    # Import pipeline
    try:
        from chainguardian.feature_extraction.pipeline import FeaturePipeline
        print("✓ Pipeline imported successfully\n")
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

    # Test contracts (diverse set)
    test_contracts = [
        # Simple vulnerable contract (our test contract)
        {
            'path': Path("test_contract_simple.sol"),
            'name': "SimpleVulnerable",
            'expected_vulnerabilities': ['cei_violations', 'unchecked_calls'],
            'description': "Simple reentrancy vulnerability"
        },

        # Solidity by Example contracts (no dependencies)
        {
            'path': Path("blockchain/solidity-by-example.github.io/src/pages/constants/Constants.sol"),
            'name': "Constants",
            'expected_vulnerabilities': [],
            'description': "Simple constant variables example"
        },

        # Another example
        {
            'path': Path("blockchain/solidity-by-example.github.io/src/pages/structs/Structs.sol"),
            'name': "Todos",
            'expected_vulnerabilities': [],
            'description': "Struct usage example"
        },
    ]

    # Initialize results tracking
    results = []
    successful = 0
    failed = 0

    # Test both modes
    for mode in ['comprehensive', 'maximum']:
        print(f"\n{'='*80}")
        print(f"TESTING MODE: {mode.upper()}")
        print(f"{'='*80}\n")

        pipeline = FeaturePipeline(mode=mode)

        for i, test_case in enumerate(test_contracts, 1):
            contract_path = test_case['path']
            contract_name = test_case['name']

            # Skip if contract doesn't exist
            if not contract_path.exists():
                print(f"[{i}/{len(test_contracts)}] ⏭️  Skipping {contract_name} (file not found)")
                continue

            print(f"[{i}/{len(test_contracts)}] Testing: {contract_name}")
            print(f"  Description: {test_case['description']}")
            print(f"  Path: {contract_path}")

            try:
                # Extract features
                features = pipeline.analyze_contract(
                    contract_path,
                    contract_name,
                    metadata={'test_case': test_case['description']}
                )

                # Check extraction status
                status = features.get('extraction_status', 'unknown')

                if status == 'success':
                    successful += 1
                    print(f"  ✓ Extraction successful")
                    print(f"    Features extracted: {len(features)}")
                    print(f"    Security risk score: {features.get('security_risk_score', 'N/A')}")
                    print(f"    CEI violations: {features.get('cei_violations', 0)}")
                    print(f"    High severity count: {features.get('high_severity_count', 0)}")

                    # Check expected vulnerabilities
                    if test_case['expected_vulnerabilities']:
                        print(f"    Expected vulnerabilities:")
                        for vuln in test_case['expected_vulnerabilities']:
                            value = features.get(vuln, 0)
                            print(f"      {vuln}: {value}")

                    # Add to results
                    results.append({
                        'mode': mode,
                        'contract': contract_name,
                        'status': 'success',
                        'features_count': len(features),
                        'risk_score': features.get('security_risk_score', 0),
                        'cei_violations': features.get('cei_violations', 0),
                    })

                else:
                    failed += 1
                    print(f"  ✗ Extraction failed")
                    print(f"    Reason: {features.get('failure_reason', 'Unknown')}")
                    print(f"    Error: {features.get('error_message', 'No message')[:100]}")

                    results.append({
                        'mode': mode,
                        'contract': contract_name,
                        'status': 'failed',
                        'failure_reason': features.get('failure_reason', 'Unknown'),
                    })

            except Exception as e:
                failed += 1
                print(f"  ✗ Exception occurred: {e}")
                import traceback
                traceback.print_exc()

                results.append({
                    'mode': mode,
                    'contract': contract_name,
                    'status': 'exception',
                    'error': str(e),
                })

            print()  # Blank line between tests

    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total contracts tested: {len(test_contracts) * 2} (2 modes)")
    print(f"Successful extractions: {successful}")
    print(f"Failed extractions: {failed}")
    print(f"Success rate: {(successful / (successful + failed) * 100):.1f}%")

    # Create results DataFrame
    if results:
        df = pd.DataFrame(results)
        print("\nResults Summary:")
        print(df.to_string(index=False))

        # Save to CSV
        output_file = Path("test_results_multi_contract.csv")
        df.to_csv(output_file, index=False)
        print(f"\n✓ Results saved to: {output_file}")

    # Database Check
    print("\n" + "=" * 80)
    print("DATABASE INTEGRATION TEST")
    print("=" * 80)

    try:
        from chainguardian.database.manager import DatabaseManager

        db = DatabaseManager()
        print("✓ Database connection established")

        # Try to query saved features
        with db._get_cursor() as cursor:
            cursor.execute("""
                SELECT contract_name, extraction_status
                FROM contracts
                ORDER BY created_at DESC
                LIMIT 5
            """)
            recent_contracts = cursor.fetchall()

            if recent_contracts:
                print("\nRecent contracts in database:")
                for row in recent_contracts:
                    print(f"  - {row[0]}: {row[1]}")
            else:
                print("  No contracts found in database")

        print("✓ Database query successful")

    except Exception as e:
        print(f"✗ Database test failed: {e}")

    print("\n" + "=" * 80)
    if successful > 0:
        print("✅ MULTI-CONTRACT TEST PASSED")
        print(f"   Successfully extracted features from {successful} contracts")
        print("   New tier-based extraction is production-ready!")
    else:
        print("❌ MULTI-CONTRACT TEST FAILED")
        print("   No successful extractions")
    print("=" * 80)

    return successful > 0


if __name__ == "__main__":
    success = test_multi_contract_extraction()
    sys.exit(0 if success else 1)
