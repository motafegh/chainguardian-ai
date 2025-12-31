#!/usr/bin/env python3
"""
Export Training Dataset from New 152-Feature Database
=====================================================

Exports 483 contracts with 152 features from the newly rebuilt database.
This dataset will be used to retrain ML models with the enhanced feature set.

Usage:
    poetry run python scripts/export_training_data.py
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

from chainguardian.database.manager import DatabaseManager
import pandas as pd


def export_training_data(output_path: str = 'data/ml_training_v5_152features.csv'):
    """
    Export all successfully extracted contracts from database.

    Args:
        output_path: Where to save the CSV file

    Returns:
        DataFrame with exported data
    """
    logger.info("=" * 80)
    logger.info("EXPORTING TRAINING DATASET FROM 152-FEATURE DATABASE")
    logger.info("=" * 80)

    # Initialize database connection
    db = DatabaseManager()

    # Count total contracts
    total_contracts = db.get_contract_count()
    logger.info(f"Total contracts in database: {total_contracts}")

    # Export to CSV
    logger.info(f"Exporting to: {output_path}")
    df = db.get_all_features()

    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"✓ Saved {len(df)} rows to {output_path}")

    # Analyze exported data
    logger.info("\n" + "=" * 80)
    logger.info("EXPORT SUMMARY")
    logger.info("=" * 80)

    logger.info(f"\nContracts exported: {len(df)}")

    # Count feature columns (exclude metadata)
    metadata_cols = ['id', 'contract_id', 'contract_name', 'file_path', 'dataset',
                    'data_source', 'extraction_status', 'extraction_mode',
                    'has_reentrancy', 'has_access_control_issues',
                    'has_timestamp_dependency', 'has_unchecked_call']  # Labels

    feature_cols = [c for c in df.columns if c not in metadata_cols and not c.startswith('has_')]

    logger.info(f"Total columns: {len(df.columns)}")
    logger.info(f"Feature columns: {len(feature_cols)}")
    logger.info(f"Label columns: ~{len([c for c in df.columns if c.startswith('has_')])}")

    # Dataset breakdown
    if 'dataset' in df.columns:
        logger.info(f"\nBreakdown by dataset:")
        dataset_counts = df['dataset'].value_counts()
        for dataset, count in dataset_counts.items():
            logger.info(f"  {dataset}: {count} contracts")

    # Show sample features
    logger.info(f"\nSample features (first 30):")
    for i, feat in enumerate(feature_cols[:30], 1):
        logger.info(f"  {i}. {feat}")

    if len(feature_cols) > 30:
        logger.info(f"  ... and {len(feature_cols) - 30} more features")

    # Data quality checks
    logger.info(f"\nData Quality:")
    logger.info(f"  Missing values: {df.isnull().sum().sum()} total")
    logger.info(f"  Duplicate rows: {df.duplicated().sum()}")

    # Feature statistics
    if len(feature_cols) > 0:
        sample_feature = feature_cols[0]
        logger.info(f"\nSample feature stats ({sample_feature}):")
        logger.info(f"  Mean: {df[sample_feature].mean():.2f}")
        logger.info(f"  Std: {df[sample_feature].std():.2f}")
        logger.info(f"  Min: {df[sample_feature].min():.2f}")
        logger.info(f"  Max: {df[sample_feature].max():.2f}")

    logger.info("\n" + "=" * 80)
    logger.info(f"✓ Export complete: {output_path}")
    logger.info("=" * 80)

    # Save metadata
    metadata_path = output_path.replace('.csv', '_metadata.txt')
    with open(metadata_path, 'w') as f:
        f.write(f"Export Date: {datetime.now()}\n")
        f.write(f"Total Contracts: {len(df)}\n")
        f.write(f"Total Features: {len(feature_cols)}\n")
        f.write(f"Database: 152-feature tier-based system\n")
        f.write(f"Mode: comprehensive (Tier 1+2+3)\n")
        f.write(f"\nFeature List:\n")
        for feat in feature_cols:
            f.write(f"  - {feat}\n")

    logger.info(f"✓ Metadata saved: {metadata_path}")

    return df


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Export training data from 152-feature database')
    parser.add_argument(
        '--output',
        default='data/ml_training_v5_152features.csv',
        help='Output CSV file path'
    )

    args = parser.parse_args()

    try:
        df = export_training_data(output_path=args.output)
        logger.info(f"\n✅ SUCCESS! Exported {len(df)} contracts to {args.output}")
        return 0

    except Exception as e:
        logger.error(f"\n❌ EXPORT FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
