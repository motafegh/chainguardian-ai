"""
Manually fix ast_analyzer.py with fuzzy matching
"""

from pathlib import Path

print("🔧 Manually patching ast_analyzer.py...")

ast_file = Path('src/chainguardian/feature_extraction/ast_analyzer.py')

if not ast_file.exists():
    print("❌ File not found!")
    exit(1)

content = ast_file.read_text()
lines = content.split('\n')

# Find the extract_features method
patched = False

for i, line in enumerate(lines):
    if 'def extract_features(self, contract_name: str)' in line:
        print(f"  Found extract_features at line {i+1}")
        
        # Look for the contract lookup section
        for j in range(i, min(i+100, len(lines))):
            if 'target_contract = None' in lines[j] and not patched:
                print(f"  Found target_contract initialization at line {j+1}")
                
                # Find the end of the old contract lookup block
                end_idx = j
                for k in range(j, min(j+20, len(lines))):
                    if 'return self._default_features()' in lines[k]:
                        end_idx = k
                        print(f"  Found end of block at line {k+1}")
                        break
                
                # Get indentation
                indent = ' ' * (len(lines[j]) - len(lines[j].lstrip()))
                
                # Create new fuzzy matching block
                new_block = [
                    f'{indent}# Find target contract with fuzzy matching',
                    f'{indent}target_contract = None',
                    f'{indent}',
                    f'{indent}# Try exact match first',
                    f'{indent}for contract in self.slither.contracts:',
                    f'{indent}    if contract.name == contract_name:',
                    f'{indent}        target_contract = contract',
                    f'{indent}        break',
                    f'{indent}',
                    f'{indent}# Fuzzy match: case-insensitive, ignore underscores/dashes',
                    f'{indent}if not target_contract:',
                    f'{indent}    name_clean = contract_name.lower().replace("_", "").replace("-", "")',
                    f'{indent}    for contract in self.slither.contracts:',
                    f'{indent}        contract_clean = contract.name.lower().replace("_", "").replace("-", "")',
                    f'{indent}        if contract_clean in name_clean or name_clean in contract_clean:',
                    f'{indent}            target_contract = contract',
                    f'{indent}            logger.info(f"Fuzzy matched \\"{contract_name}\\" -> \\"{contract.name}\\"")',
                    f'{indent}            break',
                    f'{indent}',
                    f'{indent}# Use first non-interface contract if nothing matched',
                    f'{indent}if not target_contract and self.slither.contracts:',
                    f'{indent}    for contract in self.slither.contracts:',
                    f'{indent}        if not contract.is_interface and not contract.is_library:',
                    f'{indent}            target_contract = contract',
                    f'{indent}            logger.info(f"Using first contract \\"{contract.name}\\" for \\"{contract_name}\\"")',
                    f'{indent}            break',
                    f'{indent}',
                    f'{indent}if not target_contract:',
                    f'{indent}    logger.warning(f"No suitable contract found for {{contract_name}}")',
                    f'{indent}    return self._default_features()'
                ]
                
                # Replace old block with new
                new_lines = lines[:j] + new_block + lines[end_idx+1:]
                
                # Write back
                ast_file.write_text('\n'.join(new_lines))
                
                print(f"  ✅ Successfully patched ast_analyzer.py!")
                print(f"     Replaced {end_idx - j + 1} lines with {len(new_block)} lines")
                patched = True
                break
        
        if patched:
            break

if not patched:
    print("  ⚠️  Could not find the exact location to patch")
    print("     The file might have a different structure")

print("\n✅ Done! Re-run tests.")
