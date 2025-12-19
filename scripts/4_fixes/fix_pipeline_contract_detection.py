"""
Fix pipeline to auto-detect contract names from Slither
"""

from pathlib import Path

print("🔧 Fixing pipeline to auto-detect contract names...")

pipeline_file = Path('src/chainguardian/feature_extraction/pipeline.py')

if not pipeline_file.exists():
    print("❌ pipeline.py not found!")
    exit(1)

content = pipeline_file.read_text()

# Find where contract_name is used and add auto-detection
# This is a more involved change - let's see if the fuzzy matching works first

print("✅ Use the fuzzy matching patch instead for now")
print("   If that doesn't work, we'll implement auto-detection")
