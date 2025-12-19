"""
Apply semantic feature columns to existing database schema
Uses Python/psycopg2 to avoid psql authentication issues
"""

import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection config (same as manager.py)
config = {
    'host': 'localhost',
    'port': 5432,
    'database': 'chainguardian',
    'user': 'chainguardian_user',
    'password': '2220128'
}

print("\n" + "="*70)
print("🔧 APPLYING SEMANTIC FEATURE SCHEMA UPDATE")
print("="*70)

try:
    # Connect to database
    conn = psycopg2.connect(**config)
    cursor = conn.cursor()
    print("✅ Connected to database")
    
    # Add semantic feature columns
    semantic_columns = [
        "ALTER TABLE features ADD COLUMN IF NOT EXISTS cei_violations INTEGER DEFAULT 0;",
        "ALTER TABLE features ADD COLUMN IF NOT EXISTS cei_safe_functions INTEGER DEFAULT 0;",
        "ALTER TABLE features ADD COLUMN IF NOT EXISTS cei_pattern_score REAL DEFAULT 1.0;",
        "ALTER TABLE features ADD COLUMN IF NOT EXISTS has_reentrancy_guard BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE features ADD COLUMN IF NOT EXISTS functions_with_reentrancy_guard INTEGER DEFAULT 0;",
        "ALTER TABLE features ADD COLUMN IF NOT EXISTS state_before_call_count INTEGER DEFAULT 0;",
        "ALTER TABLE features ADD COLUMN IF NOT EXISTS state_after_call_count INTEGER DEFAULT 0;",
        "ALTER TABLE features ADD COLUMN IF NOT EXISTS unchecked_calls_in_critical_context INTEGER DEFAULT 0;",
    ]
    
    print("\n📊 Adding semantic feature columns...")
    for sql in semantic_columns:
        try:
            cursor.execute(sql)
            col_name = sql.split("ADD COLUMN IF NOT EXISTS")[1].split()[0]
            print(f"   ✅ Added: {col_name}")
        except Exception as e:
            print(f"   ⚠️  {e}")
    
    conn.commit()
    print("\n✅ Schema update complete!")
    
    # Verify columns exist
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'features' 
        AND column_name LIKE 'cei%' OR column_name LIKE '%guard%' OR column_name LIKE 'state_%'
        ORDER BY column_name;
    """)
    
    columns = cursor.fetchall()
    print(f"\n📋 VERIFIED SEMANTIC COLUMNS ({len(columns)}):")
    for col_name, col_type in columns:
        print(f"   • {col_name:45s} ({col_type})")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*70)
    print("🎉 READY FOR EXTRACTION WITH SEMANTIC FEATURES")
    print("="*70 + "\n")

except Exception as e:
    print(f"\n❌ ERROR: {e}\n")
    raise
