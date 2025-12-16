"""
Clean up project structure

🎓 Organizes files into proper folders
Run BEFORE git commit to have clean structure
"""

import shutil
from pathlib import Path
import os

def cleanup_project():
    """Reorganize project structure."""
    
    print("="*70)
    print("🧹 PROJECT CLEANUP")
    print("="*70)
    print()
    
    # Create organized structure
    folders_to_create = [
        "scripts/database",
        "scripts/data",
        "scripts/testing",
        "scripts/old"
    ]
    
    for folder in folders_to_create:
        Path(folder).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {folder}/")
    
    print()
    
    # Move database scripts
    print("📁 Organizing database scripts...")
    db_scripts = [
        "create_tables.py",
        "fix_address_constraint.py", 
        "query_database.py",
        "test_db_connection.py"
    ]
    
    for script in db_scripts:
        if Path(script).exists():
            dest = Path("scripts/database") / script
            shutil.move(script, dest)
            print(f"  ✅ {script} → scripts/database/")
    
    print()
    
    # Move data scripts
    print("📁 Organizing data scripts...")
    data_scripts = [
        "download_smartbugs_curated.py",
        "download_smartbugs_sample.py",
        "import_smartbugs_to_db.py",
        "analyze_dataset.py",
        "examine_smartbugs_labels.py"
    ]
    
    for script in data_scripts:
        if Path(script).exists():
            dest = Path("scripts/data") / script
            shutil.move(script, dest)
            print(f"  ✅ {script} → scripts/data/")
    
    print()
    
    # Move testing scripts
    print("📁 Organizing testing scripts...")
    test_scripts = [
        "test_pipeline_with_db.py"
    ]
    
    for script in test_scripts:
        if Path(script).exists():
            dest = Path("scripts/testing") / script
            shutil.move(script, dest)
            print(f"  ✅ {script} → scripts/testing/")
    
    print()
    
    # Move Archive folder
    print("📁 Organizing archive...")
    if Path("Archive").exists():
        shutil.move("Archive", "scripts/old/Archive")
        print(f"  ✅ Archive/ → scripts/old/Archive/")
    
    # Move old scripts folder
    if Path("scripts/old_day4").exists():
        for item in Path("scripts/old_day4").iterdir():
            dest = Path("scripts/old") / item.name
            shutil.move(str(item), dest)
        Path("scripts/old_day4").rmdir()
        print(f"  ✅ scripts/old_day4/ → scripts/old/")
    
    if Path("scripts/new").exists():
        for item in Path("scripts/new").iterdir():
            dest = Path("scripts/old") / item.name
            shutil.move(str(item), dest)
        Path("scripts/new").rmdir()
        print(f"  ✅ scripts/new/ → scripts/old/")
    
    print()
    
    # Optional: Remove node_modules (if not needed)
    print("🗑️  Optional removals...")
    removals = input("Remove node_modules/, package.json, package-lock.json? (y/n): ")
    
    if removals.lower() == 'y':
        if Path("node_modules").exists():
            shutil.rmtree("node_modules")
            print("  🗑️  Removed: node_modules/")
        
        for file in ["package.json", "package-lock.json"]:
            if Path(file).exists():
                Path(file).unlink()
                print(f"  🗑️  Removed: {file}")
    
    print()
    
    # Handle contracts_registry.py
    if Path("contracts_registry.py").exists():
        choice = input("What to do with contracts_registry.py? (keep/delete/move to old): ")
        if choice == "delete":
            Path("contracts_registry.py").unlink()
            print("  🗑️  Deleted: contracts_registry.py")
        elif choice == "move to old":
            shutil.move("contracts_registry.py", "scripts/old/contracts_registry.py")
            print("  ✅ Moved to scripts/old/")
        else:
            print("  ⏭️  Keeping contracts_registry.py in root")
    
    print()
    
    # Clean up logs archive
    print("📁 Organizing logs...")
    if Path("logs/archive_day4").exists():
        print("  ℹ️  logs/archive_day4/ exists (leaving as is)")
    
    print()
    
    # Create clean README structure reference
    print("📝 Creating STRUCTURE.md...")
    structure_doc = """# Project Structure

## Core Directories
```
src/chainguardian/          - Main application code
├── data_collection/        - Contract collection pipelines
├── feature_extraction/     - Feature extraction (Slither, AST)
├── database/               - Database management
└── ml/                     - Machine learning (future)

scripts/                    - Utility scripts
├── database/               - Database setup & queries
├── data/                   - Data import & analysis
├── testing/                - Test scripts
└── old/                    - Archived scripts

data/                       - Data files
├── smartbugs_curated/      - SmartBugs dataset
├── smartbugs_contracts/    - Downloaded contracts
└── *.csv                   - Exported datasets

logs/                       - Application logs
models/                     - Saved ML models
cache/                      - Cache files
blockchain/contracts/       - Collected smart contracts
docs/                       - Documentation
Learning-files/             - Personal notes
notebooks/                  - Jupyter notebooks
tests/                      - Unit & integration tests
```

## Running Scripts

### Database
```bash
poetry run python scripts/database/create_tables.py
poetry run python scripts/database/query_database.py
```

### Data Import
```bash
poetry run python scripts/data/download_smartbugs_curated.py
poetry run python scripts/data/import_smartbugs_to_db.py
poetry run python scripts/data/analyze_dataset.py
```

### Testing
```bash
poetry run python scripts/testing/test_pipeline_with_db.py
```
"""
    
    with open("STRUCTURE.md", "w") as f:
        f.write(structure_doc)
    
    print("  ✅ Created: STRUCTURE.md")
    print()
    
    # Summary
    print("="*70)
    print("✅ CLEANUP COMPLETE!")
    print("="*70)
    print()
    print("Next steps:")
    print("  1. Review the new structure")
    print("  2. Test that scripts still work:")
    print("     poetry run python scripts/database/query_database.py")
    print("  3. Update any import paths if needed")
    print("  4. Commit with: git add . && git commit -m 'chore: Reorganize project structure'")
    print()

if __name__ == "__main__":
    cleanup_project()