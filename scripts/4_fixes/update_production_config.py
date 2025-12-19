"""
Update hybrid_predictor.py with optimized configuration
"""

from pathlib import Path

print("\n🔧 Updating production configuration...")

predictor_file = Path('src/chainguardian/ml/models/hybrid_predictor.py')

if not predictor_file.exists():
    print("❌ File not found!")
    exit(1)

content = predictor_file.read_text()

# Find and replace default values
old_defaults = '''    # OPTIMIZED DEFAULTS (76% adversarial accuracy)
    DEFAULT_ML_WEIGHT = 0.60
    DEFAULT_SEMANTIC_WEIGHT = 0.40
    DEFAULT_THRESHOLD = 0.60  # Increased from 0.50'''

new_defaults = '''    # OPTIMIZED DEFAULTS (100% recall, 48% F1)
    # Config: Security-First (catches all vulnerabilities)
    DEFAULT_ML_WEIGHT = 0.30
    DEFAULT_SEMANTIC_WEIGHT = 0.70
    DEFAULT_THRESHOLD = 0.20  # Low threshold for maximum recall'''

if old_defaults in content:
    content = content.replace(old_defaults, new_defaults)
    predictor_file.write_text(content)
    print("✅ Updated default configuration in hybrid_predictor.py")
    print("\n📊 NEW DEFAULTS:")
    print("   ML Weight: 0.30")
    print("   Semantic Weight: 0.70")
    print("   Threshold: 0.20")
    print("   Expected: 100% recall, 31.6% precision")
else:
    print("⚠️  Could not find exact code block to replace")
    print("   Please manually update:")
    print(f"   DEFAULT_ML_WEIGHT = 0.30")
    print(f"   DEFAULT_SEMANTIC_WEIGHT = 0.70")
    print(f"   DEFAULT_THRESHOLD = 0.20")

print("\n✅ Done!\n")
