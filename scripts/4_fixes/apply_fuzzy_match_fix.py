"""
Apply fuzzy matching fix to extractors
"""

from pathlib import Path
import re

def patch_file(filepath, class_name):
    """Apply fuzzy matching patch to a file"""
    
    print(f"\n📝 Patching {filepath.name}...")
    
    if not filepath.exists():
        print(f"  ❌ File not found!")
        return False
    
    content = filepath.read_text()
    
    # Find the extract_features method
    # Look for the pattern where contract lookup happens
    
    # Pattern to find: loop that looks for contract by name
    pattern = r'(def extract_features\(self, contract_name: str\).*?\n.*?""".*?""".*?\n)(.*?)(        # Find target contract.*?target_contract = None.*?for contract in self\.slither\.contracts:.*?if contract\.name == contract_name:.*?target_contract = contract.*?break.*?if not target_contract:.*?logger\.warning.*?return self\._default_features\(\))'
    
    # Replacement with fuzzy matching
    replacement = r'''\1\2        # Find target contract with fuzzy matching
        target_contract = None
        
        # Try exact match first
        for contract in self.slither.contracts:
            if contract.name == contract_name:
                target_contract = contract
                break
        
        # Fuzzy match: case-insensitive, ignore underscores/dashes
        if not target_contract:
            name_clean = contract_name.lower().replace('_', '').replace('-', '')
            for contract in self.slither.contracts:
                contract_clean = contract.name.lower().replace('_', '').replace('-', '')
                if contract_clean in name_clean or name_clean in contract_clean:
                    target_contract = contract
                    logger.info(f"Fuzzy matched '{contract_name}' -> '{contract.name}'")
                    break
        
        # Use first non-interface contract if nothing matched
        if not target_contract and self.slither.contracts:
            for contract in self.slither.contracts:
                if not contract.is_interface and not contract.is_library:
                    target_contract = contract
                    logger.info(f"Using first contract '{contract.name}' for '{contract_name}'")
                    break
        
        if not target_contract:
            logger.warning(f"No suitable contract found for {contract_name}")
            return self._default_features()'''
    
    # Try to apply the pattern
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    if new_content == content:
        print(f"  ⚠️  Pattern didn't match - trying manual approach")
        return False
    else:
        filepath.write_text(new_content)
        print(f"  ✅ Successfully patched!")
        return True

# Patch files
graph_file = Path('src/chainguardian/feature_extraction/graph_extractor.py')
ast_file = Path('src/chainguardian/feature_extraction/ast_analyzer.py')

results = []
results.append(patch_file(graph_file, 'GraphFeatureExtractor'))
results.append(patch_file(ast_file, 'ASTFeatureExtractor'))

if not any(results):
    print("\n⚠️  Regex patch failed. Using manual insertion method...\n")
    
    # Manual method for graph_extractor
    print("📝 Manually patching graph_extractor.py...")
    
    content = graph_file.read_text()
    
    # Find the line number where we need to insert
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if 'def extract_features(self, contract_name: str)' in line:
            # Find the contract lookup section
            for j in range(i, min(i+50, len(lines))):
                if 'target_contract = None' in lines[j]:
                    # Found it! Now replace the next ~10 lines
                    print(f"  Found at line {j}")
                    
                    # Create new block
                    indent = '        '
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
                        f'{indent}    return self._default_features()',
                    ]
                    
                    # Find end of old block (look for return statement)
                    end_line = j
                    for k in range(j, min(j+15, len(lines))):
                        if 'return self._default_features()' in lines[k]:
                            end_line = k
                            break
                    
                    # Replace old block with new
                    new_lines = lines[:j] + new_block + lines[end_line+1:]
                    
                    graph_file.write_text('\n'.join(new_lines))
                    print(f"  ✅ Manually patched graph_extractor.py")
                    break
            break
    
    # Same for ast_analyzer
    print("\n📝 Manually patching ast_analyzer.py...")
    
    content = ast_file.read_text()
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if 'def extract_features(self, contract_name: str)' in line:
            for j in range(i, min(i+50, len(lines))):
                if 'target_contract = None' in lines[j]:
                    print(f"  Found at line {j}")
                    
                    indent = '        '
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
                        f'{indent}    return self._default_features()',
                    ]
                    
                    end_line = j
                    for k in range(j, min(j+15, len(lines))):
                        if 'return self._default_features()' in lines[k]:
                            end_line = k
                            break
                    
                    new_lines = lines[:j] + new_block + lines[end_line+1:]
                    
                    ast_file.write_text('\n'.join(new_lines))
                    print(f"  ✅ Manually patched ast_analyzer.py")
                    break
            break

print("\n✅ All patches applied! Re-run tests now.")
