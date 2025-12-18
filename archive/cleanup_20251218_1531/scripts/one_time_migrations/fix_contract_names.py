"""
Fix contract name mismatches in database.

Problem: Database has addresses/wrong names instead of actual contract names.
Solution: Parse .sol files to extract real contract names.
"""

from chainguardian.database.manager import DatabaseManager
from pathlib import Path
import re
import psycopg2

def extract_contract_name_from_file(sol_file: Path) -> str:
    """Extract the primary contract name from a .sol file."""
    try:
        content = sol_file.read_text(encoding='utf-8')
        
        # Find all contract declarations
        # Matches: contract MyContract { or contract MyContract is BaseContract {
        pattern = r'contract\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:is\s+[^{]+)?\s*\{'
        matches = re.findall(pattern, content)
        
        if not matches:
            return None
        
        # Return the last contract (usually the main one)
        return matches[-1]
        
    except Exception as e:
        print(f"Error reading {sol_file}: {e}")
        return None

def fix_database_names():
    """Update database with correct contract names."""
    
    db = DatabaseManager()
    df = db.get_all_features()
    
    print("=" * 70)
    print("FIXING CONTRACT NAMES IN DATABASE")
    print("=" * 70)
    
    # Connect directly to update
    conn = psycopg2.connect(
        host="localhost",
        database="chainguardian",
        user="chainguardian_user",
        password="2220128"
    )
    cursor = conn.cursor()
    
    fixed_count = 0
    error_count = 0
    
    for idx, row in df.iterrows():
        file_path = Path(row['file_path'])
        db_name = row['contract_name']
        contract_id = row['contract_id']
        
        # Skip if file doesn't exist
        if not file_path.exists():
            continue
        
        # Skip if name looks correct (not an address)
        if not db_name.startswith('0x') and '_' not in db_name.lower():
            continue
        
        # Extract real name from file
        real_name = extract_contract_name_from_file(file_path)
        
        if real_name and real_name != db_name:
            print(f"Fixing: '{db_name}' → '{real_name}'")
            
            try:
                cursor.execute("""
                    UPDATE contracts 
                    SET name = %s 
                    WHERE id = %s;
                """, (real_name, contract_id))
                
                fixed_count += 1
                
            except Exception as e:
                print(f"  ✗ Error updating {db_name}: {e}")
                error_count += 1
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 70)
    print("✅ NAME FIX COMPLETE")
    print("=" * 70)
    print(f"  Fixed: {fixed_count} contracts")
    print(f"  Errors: {error_count}")
    print("\n➡️  Now re-run: poetry run python scripts/reanalyze_all_contracts.py")
    print("=" * 70)

if __name__ == "__main__":
    fix_database_names()
