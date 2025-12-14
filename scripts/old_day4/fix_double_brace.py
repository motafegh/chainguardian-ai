from pathlib import Path
import shutil

contracts_dir = Path('blockchain/contracts/collected')
backup_dir = Path('blockchain/contracts/backup')
backup_dir.mkdir(exist_ok=True)

# List of contracts with {{ issue
double_brace_contracts = [
    'MetaSwap_0x881D4023.sol',
    # Add others from analysis
]

for filename in double_brace_contracts:
    filepath = contracts_dir / filename
    if filepath.exists():
        # Backup
        shutil.copy(filepath, backup_dir / filename)
        
        # Read and fix
        content = filepath.read_text()
        if content.startswith('{{') and content.endswith('}}'):
            fixed = content[1:-1]  # Remove outer braces
            filepath.write_text(fixed)
            print(f"✓ Fixed: {filename}")

