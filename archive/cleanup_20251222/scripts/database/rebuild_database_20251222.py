#!/usr/bin/env python3
"""
Rebuild ChainGuardian Database from Scratch - December 22, 2025

CAUTION: This DROPS all existing data and recreates tables.
"""

import psycopg2
from pathlib import Path
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Database config
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'chainguardian',
    'user': 'chainguardian_user',
    'password': '2220128'
}

def backup_existing_data():
    """Backup existing database to SQL file."""
    import subprocess
    from datetime import datetime
    
    backup_file = f"backup_chainguardian_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    
    logger.info("📦 Creating backup...")
    try:
        subprocess.run([
            'pg_dump',
            '-h', DB_CONFIG['host'],
            '-U', DB_CONFIG['user'],
            '-d', DB_CONFIG['database'],
            '-f', backup_file
        ], check=True, env={'PGPASSWORD': DB_CONFIG['password']})
        logger.info(f"   ✅ Backup saved: {backup_file}")
        return backup_file
    except Exception as e:
        logger.warning(f"   ⚠️  Backup failed (database may not exist yet): {e}")
        return None

def rebuild_database():
    """Drop and recreate database from schema.sql"""
    
    schema_file = Path(__file__).parent / "schema.sql"
    
    if not schema_file.exists():
        logger.error(f"❌ Schema file not found: {schema_file}")
        sys.exit(1)
    
    logger.info("="*80)
    logger.info("🗄️  REBUILDING CHAINGUARDIAN DATABASE")
    logger.info("="*80)
    
    # Backup existing data
    backup_existing_data()
    
    # Connect and execute schema
    logger.info("\n🔧 Applying schema...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Read and execute schema
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        cursor.execute(schema_sql)
        conn.commit()
        
        logger.info("   ✅ Schema applied successfully")
        
        # Verify tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        logger.info(f"\n📊 Created tables: {len(tables)}")
        for table in tables:
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = '{table[0]}';
            """)
            col_count = cursor.fetchone()[0]
            logger.info(f"   - {table[0]}: {col_count} columns")
        
        cursor.close()
        conn.close()
        
        logger.info("\n" + "="*80)
        logger.info("✅ DATABASE REBUILD COMPLETE")
        logger.info("="*80)
        logger.info("Ready for data extraction!")
        logger.info("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"❌ Database rebuild failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    
    # Safety check
    print("⚠️  WARNING: This will DELETE all existing data!")
    print("Continue? (type 'yes' to proceed): ", end='')
    
    if '--force' in sys.argv:
        response = 'yes'
    else:
        response = input().strip().lower()
    
    if response == 'yes':
        rebuild_database()
    else:
        print("❌ Aborted")
