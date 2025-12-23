"""
Query database to see what's stored
"""
from chainguardian.database.manager import DatabaseManager
import pandas as pd

def show_database_contents():
    """Display all data in database."""
    
    db = DatabaseManager()
    
    print("="*70)
    print("DATABASE CONTENTS")
    print("="*70)
    print()
    
    # Get stats
    stats = db.get_stats()
    print("📊 STATISTICS:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()
    
    # Get all data
    df = db.get_all_features()
    
    if df.empty:
        print("⚠️ No data in database yet")
        return
    
    print("📋 CONTRACTS & FEATURES:")
    print("-"*70)
    
    # Show key columns
    columns_to_show = [
        'contract_id', 'contract_name', 'has_reentrancy', 
        'num_functions', 'high_severity_count', 'max_cyclomatic_complexity'
    ]
    
    print(df[columns_to_show].to_string(index=False))
    print()
    
    print("="*70)
    print(f"Total rows: {len(df)}")
    print(f"Total columns: {len(df.columns)}")
    print("="*70)

if __name__ == "__main__":
    show_database_contents()