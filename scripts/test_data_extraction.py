#!/usr/bin/env python3
"""
Quick test to see how many contracts from data/ folder can be successfully extracted.
This helps us decide if we have enough working contracts to skip the problematic blockchain/ datasets.
"""

import sys
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from chainguardian.feature_extraction.pipeline import FeaturePipeline


def discover_data_contracts(data_dir: Path):
    """Discover all .sol files in data/ folder."""
    contracts = []

    # Key datasets in data/ folder
    datasets = {
        'smartbugs_curated': data_dir / 'smartbugs_curated',
        'production': data_dir / 'production',
        'vulnerable_complex': data_dir / 'vulnerable_complex',
        'safe_contracts': data_dir / 'safe_contracts',
    }

    for dataset_name, dataset_path in datasets.items():
        if not dataset_path.exists():
            logger.warning(f"Dataset not found: {dataset_name}")
            continue

        for sol_file in dataset_path.rglob('*.sol'):
            # Extract contract name from file
            contract_name = sol_file.stem

            # Capitalize if all lowercase
            if contract_name.islower():
                contract_name = contract_name.capitalize()

            contracts.append((sol_file, contract_name, dataset_name))

    logger.info(f"Discovered {len(contracts)} contracts in data/ folder")
    return contracts


def test_extraction(max_test: int = 100):
    """Test extraction on a sample of contracts from data/ folder."""
    logger.info("=" * 80)
    logger.info("TESTING DATA/ FOLDER EXTRACTION SUCCESS RATE")
    logger.info("=" * 80)

    # Discover contracts
    data_dir = Path('data')
    contracts = discover_data_contracts(data_dir)

    if not contracts:
        logger.error("No contracts found in data/ folder!")
        return

    # Initialize pipeline
    pipeline = FeaturePipeline(mode='comprehensive')

    # Test on sample
    test_size = min(max_test, len(contracts))
    logger.info(f"\nTesting {test_size} contracts (out of {len(contracts)} total)...")

    stats = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'by_reason': {},
        'by_dataset': {}
    }

    for i, (contract_path, contract_name, dataset) in enumerate(contracts[:test_size], 1):
        stats['total'] += 1

        if dataset not in stats['by_dataset']:
            stats['by_dataset'][dataset] = {'total': 0, 'success': 0, 'failed': 0}
        stats['by_dataset'][dataset]['total'] += 1

        logger.info(f"[{i}/{test_size}] Testing: {contract_name} ({dataset})")

        try:
            result = pipeline.analyze_contract(
                contract_path,
                contract_name,
                {'dataset': dataset, 'data_source': dataset}
            )

            if result.get('extraction_status') == 'success':
                stats['success'] += 1
                stats['by_dataset'][dataset]['success'] += 1
                logger.info(f"  ✓ SUCCESS")
            else:
                stats['failed'] += 1
                stats['by_dataset'][dataset]['failed'] += 1
                reason = result.get('failure_reason', 'UNKNOWN')
                stats['by_reason'][reason] = stats['by_reason'].get(reason, 0) + 1
                logger.info(f"  ✗ FAILED - {reason}")

        except Exception as e:
            stats['failed'] += 1
            stats['by_dataset'][dataset]['failed'] += 1
            stats['by_reason']['EXCEPTION'] = stats['by_reason'].get('EXCEPTION', 0) + 1
            logger.error(f"  ✗ EXCEPTION - {e}")

        # Progress update every 25
        if stats['total'] % 25 == 0:
            success_rate = stats['success'] / stats['total'] * 100
            logger.info(f"\n--- PROGRESS: {stats['success']}/{stats['total']} ({success_rate:.1f}%) ---\n")

    # Final report
    logger.info("\n" + "=" * 80)
    logger.info("EXTRACTION TEST RESULTS")
    logger.info("=" * 80)

    success_rate = stats['success'] / stats['total'] * 100 if stats['total'] > 0 else 0

    logger.info(f"\nOVERALL:")
    logger.info(f"  Tested: {stats['total']} contracts")
    logger.info(f"  Success: {stats['success']} ({success_rate:.1f}%)")
    logger.info(f"  Failed: {stats['failed']} ({100-success_rate:.1f}%)")

    logger.info(f"\nBY DATASET:")
    for dataset, data in stats['by_dataset'].items():
        ds_rate = data['success'] / data['total'] * 100 if data['total'] > 0 else 0
        logger.info(f"  {dataset}:")
        logger.info(f"    Total: {data['total']}")
        logger.info(f"    Success: {data['success']} ({ds_rate:.1f}%)")
        logger.info(f"    Failed: {data['failed']}")

    if stats['by_reason']:
        logger.info(f"\nFAILURE REASONS:")
        for reason, count in sorted(stats['by_reason'].items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {reason}: {count}")

    # Projection
    logger.info(f"\nPROJECTION FOR FULL DATA/ FOLDER:")
    total_contracts = len(contracts)
    projected_success = int(total_contracts * success_rate / 100)
    logger.info(f"  Total contracts available: {total_contracts}")
    logger.info(f"  Projected successful extractions: ~{projected_success} ({success_rate:.1f}%)")

    # Recommendation
    logger.info(f"\n" + "=" * 80)
    logger.info("RECOMMENDATION:")
    logger.info("=" * 80)

    if projected_success >= 500:
        logger.info(f"✅ EXCELLENT! ~{projected_success} successful extractions expected.")
        logger.info(f"   This is MORE than enough for ML training (you had 5,321 before).")
        logger.info(f"   Recommendation: Proceed with data/ folder extraction.")
    elif projected_success >= 200:
        logger.info(f"✅ GOOD! ~{projected_success} successful extractions expected.")
        logger.info(f"   This should be sufficient for ML training.")
        logger.info(f"   Recommendation: Proceed with data/ folder extraction.")
    else:
        logger.info(f"⚠️  LOW: Only ~{projected_success} successful extractions expected.")
        logger.info(f"   You may need to fix dependency issues in blockchain/ datasets.")
        logger.info(f"   Recommendation: Consider fixing import/compilation errors.")

    return stats


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Test extraction success rate on data/ folder')
    parser.add_argument('--max', type=int, default=100, help='Max contracts to test (default: 100)')
    args = parser.parse_args()

    test_extraction(max_test=args.max)
