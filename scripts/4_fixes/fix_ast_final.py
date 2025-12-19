"""
Final fix for ast_analyzer.py based on actual structure
"""

from pathlib import Path

print("🔧 Fixing ast_analyzer.py with correct structure...")

ast_file = Path('src/chainguardian/feature_extraction/ast_analyzer.py')

if not ast_file.exists():
    print("❌ File not found!")
    exit(1)

content = ast_file.read_text()

# The old code block we need to replace (lines 147-153)
old_code = '''        contract = None
        for c in self.slither.contracts:
            if c.name == contract_name:
                contract = c
                break

        if not contract:
            logger.warning(f"Contract {contract_name} not found")
            return features'''

# New code with fuzzy matching
new_code = '''        # Find target contract with fuzzy matching
        contract = None
        
        # Try exact match first
        for c in self.slither.contracts:
            if c.name == contract_name:
                contract = c
                break
        
        # Fuzzy match: case-insensitive, ignore underscores/dashes
        if not contract:
            name_clean = contract_name.lower().replace("_", "").replace("-", "")
            for c in self.slither.contracts:
                contract_clean = c.name.lower().replace("_", "").replace("-", "")
                if contract_clean in name_clean or name_clean in contract_clean:
                    contract = c
                    logger.info(f"Fuzzy matched '{contract_name}' -> '{c.name}'")
                    break
        
        # Use first non-interface contract if nothing matched
        if not contract and self.slither.contracts:
            for c in self.slither.contracts:
                if not c.is_interface and not c.is_library:
                    contract = c
                    logger.info(f"Using first contract '{c.name}' for '{contract_name}'")
                    break
        
        if not contract:
            logger.warning(f"No suitable contract found for {contract_name}")
            return features'''

if old_code in content:
    content = content.replace(old_code, new_code)
    ast_file.write_text(content)
    print("  ✅ Successfully patched ast_analyzer.py!")
else:
    print("  ⚠️  Exact code block not found")
    print("  Trying with normalized whitespace...")
    
    # Try with flexible whitespace
    import re
    
    # More flexible pattern
    pattern = r'contract = None\s+for c in self\.slither\.contracts:\s+if c\.name == contract_name:\s+contract = c\s+break\s+if not contract:\s+logger\.warning\(f"Contract {contract_name} not found"\)\s+return features'
    
    replacement = '''contract = None
        
        # Try exact match first
        for c in self.slither.contracts:
            if c.name == contract_name:
                contract = c
                break
        
        # Fuzzy match: case-insensitive, ignore underscores/dashes
        if not contract:
            name_clean = contract_name.lower().replace("_", "").replace("-", "")
            for c in self.slither.contracts:
                contract_clean = c.name.lower().replace("_", "").replace("-", "")
                if contract_clean in name_clean or name_clean in contract_clean:
                    contract = c
                    logger.info(f"Fuzzy matched '{contract_name}' -> '{c.name}'")
                    break
        
        # Use first non-interface contract if nothing matched
        if not contract and self.slither.contracts:
            for c in self.slither.contracts:
                if not c.is_interface and not c.is_library:
                    contract = c
                    logger.info(f"Using first contract '{c.name}' for '{contract_name}'")
                    break
        
        if not contract:
            logger.warning(f"No suitable contract found for {contract_name}")
            return features'''
    
    new_content = re.sub(pattern, replacement, content)
    
    if new_content != content:
        ast_file.write_text(new_content)
        print("  ✅ Successfully patched with flexible matching!")
    else:
        print("  ❌ Could not apply patch automatically")
        print("\n  Manual fix needed. Here's what to change:")
        print("\n  FIND (around line 147):")
        print("  " + "-"*60)
        print(old_code)
        print("  " + "-"*60)
        print("\n  REPLACE WITH:")
        print("  " + "-"*60)
        print(new_code)
        print("  " + "-"*60)

print("\n✅ Done!")
