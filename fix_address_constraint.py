"""
Fix database schema - make address optional (NULL allowed)

🎓 Why: SmartBugs contracts don't have addresses in filenames
We need to allow NULL addresses in the database
"""

import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'chainguardian',
    'user': 'chainguardian_user',
    'password': '2220128'
}

def fix_address_constraint():
    """
    Make address column nullable in contracts table.
    
    🎓 SQL ALTER TABLE changes table structure without losing data
    """
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("="*70)
    print("🔧 FIXING DATABASE SCHEMA")
    print("="*70)
    print()
    
    try:
        # Step 1: Check current constraint
        cursor.execute("""
            SELECT column_name, is_nullable, data_type
            FROM information_schema.columns
            WHERE table_name = 'contracts' AND column_name = 'address';
        """)
        
        result = cursor.fetchone()
        if result:
            col_name, is_nullable, data_type = result
            print(f"📊 Current 'address' column:")
            print(f"   Data type: {data_type}")
            print(f"   Nullable: {is_nullable}")
            print()
        
        # Step 2: Drop NOT NULL constraint
        print("🔧 Removing NOT NULL constraint from 'address' column...")
        cursor.execute("""
            ALTER TABLE contracts 
            ALTER COLUMN address DROP NOT NULL;
        """)
        print("✅ Made 'address' column optional (can be NULL)")
        print()
        
        # Step 3: Drop UNIQUE constraint (if exists)
        print("🔧 Checking for UNIQUE constraint...")
        cursor.execute("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'contracts' 
            AND constraint_type = 'UNIQUE' 
            AND constraint_name LIKE '%address%';
        """)
        
        constraints = cursor.fetchall()
        if constraints:
            for (constraint_name,) in constraints:
                print(f"   Dropping constraint: {constraint_name}")
                cursor.execute(f"""
                    ALTER TABLE contracts 
                    DROP CONSTRAINT IF EXISTS {constraint_name};
                """)
            print("✅ Removed old UNIQUE constraint")
        else:
            print("   No UNIQUE constraint found")
        print()
        
        # Step 4: Create partial UNIQUE index (NULL values allowed)
        print("🔧 Creating new UNIQUE index (allows NULL)...")
        cursor.execute("""
            DROP INDEX IF EXISTS contracts_address_unique;
        """)
        cursor.execute("""
            CREATE UNIQUE INDEX contracts_address_unique 
            ON contracts(address) 
            WHERE address IS NOT NULL;
        """)
        print("✅ Created UNIQUE constraint (NULL values allowed)")
        print()
        
        # Commit changes
        conn.commit()
        
        # Step 5: Verify changes
        cursor.execute("""
            SELECT column_name, is_nullable, data_type
            FROM information_schema.columns
            WHERE table_name = 'contracts' AND column_name = 'address';
        """)
        
        result = cursor.fetchone()
        if result:
            col_name, is_nullable, data_type = result
            print("="*70)
            print("✅ VERIFICATION - Current 'address' column:")
            print("="*70)
            print(f"   Data type: {data_type}")
            print(f"   Nullable: {is_nullable} ← Should be 'YES'")
            print()
        
        print("="*70)
        print("🎉 DATABASE SCHEMA UPDATED SUCCESSFULLY!")
        print("="*70)
        print()
        print("Changes:")
        print("  1. ✅ 'address' column is now optional (NULL allowed)")
        print("  2. ✅ UNIQUE constraint only applies to non-NULL addresses")
        print("  3. ✅ Multiple contracts can have NULL address")
        print()
        print("🎯 Ready to import SmartBugs contracts!")
        print()
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        print()
        print("💡 Troubleshooting:")
        print("  1. Check PostgreSQL is running: sudo service postgresql status")
        print("  2. Check credentials are correct")
        print("  3. Check you have ALTER TABLE permissions")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    fix_address_constraint()