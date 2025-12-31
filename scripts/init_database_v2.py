#!/usr/bin/env python3
"""
ChainGuardian AI - Database V2 Initialization (Python Version)
Creates new schema in existing database with 152-feature tier-based system
"""

import sys
import os
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

import psycopg2
from psycopg2 import sql
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Database configuration (uses same credentials as existing system)
DB_HOST = os.getenv('CHAINGUARDIAN_DB_HOST', 'localhost')
DB_PORT = os.getenv('CHAINGUARDIAN_DB_PORT', '5432')
DB_NAME = os.getenv('CHAINGUARDIAN_DB_NAME', 'chainguardian')  # Use existing database
DB_USER = os.getenv('CHAINGUARDIAN_DB_USER', 'chainguardian_user')
DB_PASSWORD = os.getenv('CHAINGUARDIAN_DB_PASSWORD', '2220128')


def init_database_v2():
    """Initialize database with new V2 schema."""
    logger.info("=" * 80)
    logger.info("ChainGuardian AI - Database V2 Schema Initialization")
    logger.info("=" * 80)
    logger.info("")

    # Read schema file
    schema_file = project_root / "database" / "schema_v2_tiered.sql"
    if not schema_file.exists():
        logger.error(f"❌ Schema file not found: {schema_file}")
        return False

    logger.info(f"📄 Reading schema from: {schema_file}")
    schema_sql = schema_file.read_text()

    # Connect to database
    logger.info(f"🔌 Connecting to database: {DB_NAME}@{DB_HOST}")

    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()

        logger.info("✓ Connected successfully")
        logger.info("")

        # Execute schema
        logger.info("📊 Applying V2 schema...")
        logger.info("   This will:")
        logger.info("   - Drop old tables (contracts, features, labels)")
        logger.info("   - Create new tables with 152-feature schema")
        logger.info("   - Set up indexes and views")
        logger.info("")

        # Confirm
        response = input("Continue? (y/N): ").strip().lower()
        if response != 'y':
            logger.info("Cancelled.")
            return False

        logger.info("")
        logger.info("⚙️  Executing SQL...")

        # Execute the schema
        cursor.execute(schema_sql)

        logger.info("✓ Schema applied successfully")
        logger.info("")

        # Verify tables
        logger.info("🔍 Verifying installation...")
        cursor.execute("""
            SELECT
                table_name,
                (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)

        tables = cursor.fetchall()
        logger.info("\nTables created:")
        for table_name, col_count in tables:
            logger.info(f"  ✓ {table_name}: {col_count} columns")

        # Check contract_features specifically
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_name = 'contract_features'
        """)
        feature_cols = cursor.fetchone()[0]
        logger.info(f"\n✓ contract_features table has {feature_cols} columns")
        logger.info(f"  (2 metadata + 152 feature columns = 154 total)")

        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ Database V2 schema initialization COMPLETE!")
        logger.info("=" * 80)
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Run extraction: poetry run python scripts/build_database.py")
        logger.info("  2. Export data: poetry run python scripts/export_training_data.py")
        logger.info("  3. Train models: poetry run python scripts/3_training/train_production_v7.py")
        logger.info("")

        cursor.close()
        conn.close()

        return True

    except psycopg2.Error as e:
        logger.error(f"❌ Database error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = init_database_v2()
    sys.exit(0 if success else 1)
