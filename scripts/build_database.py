#!/usr/bin/env python3
"""
ChainGuardian AI - Comprehensive Database Builder
Extracts features from all contracts in blockchain folder and builds the database
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'database_build_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))


def discover_contracts(base_dir: Path) -> Dict[str, List[Tuple[Path, str]]]:
    """
    Discover all Solidity contracts organized by dataset.

    Returns:
        Dict mapping dataset name to list of (file_path, contract_name) tuples
    """
    logger.info(f"Discovering contracts in {base_dir}")

    # Use data/ folder datasets (97% success rate vs 0% in blockchain/)
    datasets = {
        'smartbugs_curated': base_dir / 'smartbugs_curated',
        'production': base_dir / 'production',
        'vulnerable_complex': base_dir / 'vulnerable_complex',
        'safe_contracts': base_dir / 'safe_contracts',
    }

    discovered = {}

    for dataset_name, dataset_path in datasets.items():
        if not dataset_path.exists():
            logger.warning(f"Dataset not found: {dataset_name}")
            continue

        contracts = []
        for sol_file in dataset_path.rglob('*.sol'):
            # Extract contract name from file
            # Handle various naming patterns:
            # - simple.sol -> Simple
            # - MyContract.sol -> MyContract
            # - my_contract.sol -> my_contract
            contract_name = sol_file.stem

            # Capitalize if all lowercase (e.g., simple -> Simple)
            if contract_name.islower():
                contract_name = contract_name.capitalize()

            contracts.append((sol_file, contract_name))

        if contracts:
            discovered[dataset_name] = contracts
            logger.info(f"  {dataset_name}: {len(contracts)} contracts")

    total = sum(len(c) for c in discovered.values())
    logger.info(f"Total discovered: {total} contracts across {len(discovered)} datasets")

    return discovered


def check_duplicate(db_manager, file_path: str) -> bool:
    """
    Check if contract already exists in database.

    Returns:
        True if duplicate, False if new
    """
    try:
        with db_manager._get_cursor() as cursor:
            cursor.execute("""
                SELECT id FROM contracts
                WHERE file_path = %s
                LIMIT 1
            """, (file_path,))
            return cursor.fetchone() is not None
    except Exception as e:
        logger.debug(f"Duplicate check failed: {e}")
        return False


def build_database(
    mode: str = 'comprehensive',
    skip_existing: bool = True,
    max_contracts: int = None
):
    """
    Build the database by extracting features from all contracts.

    Args:
        mode: Extraction mode ('comprehensive' or 'maximum')
        skip_existing: Skip contracts already in database
        max_contracts: Limit extraction (for testing)
    """
    from chainguardian.feature_extraction.pipeline import FeaturePipeline
    from chainguardian.database.manager import DatabaseManager

    logger.info("=" * 80)
    logger.info("CHAINGUARDIAN AI - DATABASE BUILDER")
    logger.info("=" * 80)
    logger.info(f"Mode: {mode}")
    logger.info(f"Skip existing: {skip_existing}")
    logger.info(f"Max contracts: {max_contracts or 'unlimited'}")
    logger.info("")

    # Initialize
    pipeline = FeaturePipeline(mode=mode)
    db = DatabaseManager()

    # Discover contracts (using data/ folder - 97% success rate)
    base_dir = Path('data')
    datasets = discover_contracts(base_dir)

    # Statistics
    stats = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'skipped_duplicate': 0,
        'skipped_limit': 0,
        'by_dataset': {},
        'by_failure_reason': {},
        'start_time': datetime.now(),
    }

    # Process each dataset
    for dataset_name, contracts in datasets.items():
        logger.info(f"\n{'=' * 80}")
        logger.info(f"PROCESSING DATASET: {dataset_name}")
        logger.info(f"{'=' * 80}")

        stats['by_dataset'][dataset_name] = {
            'total': len(contracts),
            'success': 0,
            'failed': 0,
            'skipped': 0
        }

        for i, (contract_path, contract_name) in enumerate(contracts, 1):
            stats['total'] += 1

            # Check limit
            if max_contracts and stats['success'] >= max_contracts:
                stats['skipped_limit'] += 1
                logger.info(f"Reached max contracts limit ({max_contracts})")
                break

            # Check duplicate
            if skip_existing and check_duplicate(db, str(contract_path)):
                stats['skipped_duplicate'] += 1
                stats['by_dataset'][dataset_name]['skipped'] += 1
                logger.debug(f"[{i}/{len(contracts)}] SKIP (duplicate): {contract_name}")
                continue

            # Extract features
            logger.info(f"[{i}/{len(contracts)}] Processing: {contract_name}")
            logger.info(f"  Path: {contract_path}")

            try:
                features = pipeline.analyze_contract(
                    contract_path,
                    contract_name,
                    metadata={
                        'dataset': dataset_name,
                        'data_source': dataset_name,
                    }
                )

                if features.get('extraction_status') == 'success':
                    stats['success'] += 1
                    stats['by_dataset'][dataset_name]['success'] += 1
                    logger.info(f"  ✓ SUCCESS - {len(features)} features extracted")
                else:
                    stats['failed'] += 1
                    stats['by_dataset'][dataset_name]['failed'] += 1
                    failure_reason = features.get('failure_reason', 'UNKNOWN')
                    stats['by_failure_reason'][failure_reason] = stats['by_failure_reason'].get(failure_reason, 0) + 1
                    logger.warning(f"  ✗ FAILED - {failure_reason}")

            except Exception as e:
                stats['failed'] += 1
                stats['by_dataset'][dataset_name]['failed'] += 1
                stats['by_failure_reason']['EXCEPTION'] = stats['by_failure_reason'].get('EXCEPTION', 0) + 1
                logger.error(f"  ✗ EXCEPTION - {e}")

            # Progress update every 50 contracts
            if stats['total'] % 50 == 0:
                elapsed = (datetime.now() - stats['start_time']).total_seconds()
                rate = stats['total'] / elapsed if elapsed > 0 else 0
                logger.info(f"\n--- PROGRESS UPDATE ---")
                logger.info(f"Processed: {stats['total']} contracts")
                logger.info(f"Success: {stats['success']} ({stats['success']/stats['total']*100:.1f}%)")
                logger.info(f"Failed: {stats['failed']}")
                logger.info(f"Rate: {rate:.1f} contracts/sec")
                logger.info(f"---\n")

    # Final statistics
    stats['end_time'] = datetime.now()
    stats['duration_seconds'] = (stats['end_time'] - stats['start_time']).total_seconds()

    print_final_statistics(stats)
    save_statistics(stats)

    return stats


def print_final_statistics(stats: Dict):
    """Print comprehensive final statistics."""
    logger.info("\n" + "=" * 80)
    logger.info("DATABASE BUILD COMPLETE")
    logger.info("=" * 80)

    logger.info(f"\nOVERALL STATISTICS:")
    logger.info(f"  Total contracts processed: {stats['total']}")
    logger.info(f"  Successful extractions: {stats['success']} ({stats['success']/stats['total']*100:.1f}%)")
    logger.info(f"  Failed extractions: {stats['failed']} ({stats['failed']/stats['total']*100:.1f}%)")
    logger.info(f"  Skipped (duplicates): {stats['skipped_duplicate']}")
    logger.info(f"  Duration: {stats['duration_seconds']:.1f} seconds ({stats['duration_seconds']/60:.1f} minutes)")
    logger.info(f"  Processing rate: {stats['total']/stats['duration_seconds']:.2f} contracts/sec")

    logger.info(f"\nBY DATASET:")
    for dataset, data in stats['by_dataset'].items():
        success_rate = data['success'] / data['total'] * 100 if data['total'] > 0 else 0
        logger.info(f"  {dataset}:")
        logger.info(f"    Total: {data['total']}")
        logger.info(f"    Success: {data['success']} ({success_rate:.1f}%)")
        logger.info(f"    Failed: {data['failed']}")
        logger.info(f"    Skipped: {data['skipped']}")

    if stats['by_failure_reason']:
        logger.info(f"\nFAILURE REASONS:")
        for reason, count in sorted(stats['by_failure_reason'].items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {reason}: {count}")

    logger.info("\n" + "=" * 80)


def save_statistics(stats: Dict):
    """Save statistics to JSON file."""
    # Convert datetime objects to strings
    stats_json = stats.copy()
    stats_json['start_time'] = stats['start_time'].isoformat()
    stats_json['end_time'] = stats['end_time'].isoformat()

    filename = f"database_build_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(stats_json, f, indent=2)

    logger.info(f"Statistics saved to: {filename}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Build ChainGuardian AI database')
    parser.add_argument('--mode', choices=['comprehensive', 'maximum'], default='comprehensive',
                        help='Feature extraction mode (default: comprehensive)')
    parser.add_argument('--no-skip-existing', action='store_true',
                        help='Re-process contracts already in database')
    parser.add_argument('--max', type=int, default=None,
                        help='Maximum number of contracts to process (for testing)')
    parser.add_argument('--test', action='store_true',
                        help='Test mode: process only 10 contracts')

    args = parser.parse_args()

    if args.test:
        logger.info("TEST MODE: Processing only 10 contracts")
        args.max = 10

    try:
        stats = build_database(
            mode=args.mode,
            skip_existing=not args.no_skip_existing,
            max_contracts=args.max
        )

        success_rate = stats['success'] / stats['total'] * 100 if stats['total'] > 0 else 0

        if success_rate >= 90:
            logger.info("✅ Database build SUCCESSFUL!")
            sys.exit(0)
        elif success_rate >= 70:
            logger.warning("⚠️  Database build completed with warnings")
            sys.exit(0)
        else:
            logger.error("❌ Database build had significant failures")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.warning("\n\nDatabase build interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
