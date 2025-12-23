#!/usr/bin/env python3
"""
Fix import statements for the enhanced ML pipeline.
Run: python fix_imports.py
"""

import os
import re

def fix_file(filepath, old_imports, new_imports):
    """Fix imports in a file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    for old, new in zip(old_imports, new_imports):
        if old in content:
            content = content.replace(old, new)
            print(f"  Fixed import in {os.path.basename(filepath)}")
    
    with open(filepath, 'w') as f:
        f.write(content)

def main():
    print("🔧 Fixing import statements...")
    
    # Define file paths
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    files_to_fix = [
        {
            'path': os.path.join(project_root, 'scripts/3_training/train_production_v7.py'),
            'old': [
                'from config_manager import ConfigManager, get_config',
                'from hyperparameter_tuner import HyperparameterTuner',
                'from heterogeneous_ensemble import HeterogeneousEnsemble',
                'from data_augmenter import SmartContractAugmenter',
                'from model_registry import ModelRegistry'
            ],
            'new': [
                'from src.chainguardian.ml.core.config_manager import ConfigManager, get_config',
                'from src.chainguardian.ml.core.hyperparameter_tuner import HyperparameterTuner',
                'from src.chainguardian.ml.core.heterogeneous_ensemble import HeterogeneousEnsemble',
                'from src.chainguardian.ml.core.data_augmenter import SmartContractAugmenter',
                'from src.chainguardian.ml.core.model_registry import ModelRegistry'
            ]
        },
        {
            'path': os.path.join(project_root, 'src/chainguardian/ml/models/hybrid_predictor_enhanced_v2.py'),
            'old': [
                'from config_manager import get_config',
                'from monitoring import MLMonitor',
                'from heterogeneous_ensemble import HeterogeneousEnsemble'
            ],
            'new': [
                'from src.chainguardian.ml.core.config_manager import get_config',
                'from src.chainguardian.ml.core.monitoring import MLMonitor',
                'from src.chainguardian.ml.core.heterogeneous_ensemble import HeterogeneousEnsemble'
            ]
        }
    ]
    
    # Fix each file
    for file_info in files_to_fix:
        if os.path.exists(file_info['path']):
            print(f"\nFixing {os.path.basename(file_info['path'])}...")
            fix_file(file_info['path'], file_info['old'], file_info['new'])
        else:
            print(f"\n❌ File not found: {file_info['path']}")
    
    # Add sys.path.append to training script
    training_script = os.path.join(project_root, 'scripts/3_training/train_production_v7.py')
    if os.path.exists(training_script):
        with open(training_script, 'r') as f:
            content = f.read()
        
        # Add sys.path.append after imports
        if 'sys.path.append' not in content:
            import_section = """import sys
import pandas as pd
import numpy as np
import joblib
import json
import yaml
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Import our new modules"""
            
            content = content.replace("""import sys
import pandas as pd
import numpy as np
import joblib
import json
import yaml
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import our new modules""", import_section)
            
            with open(training_script, 'w') as f:
                f.write(content)
            print("\n✅ Added sys.path.append to training script")
    
    print("\n🎉 Import fixes completed!")
    print("\nNext: Run 'poetry run python scripts/3_training/train_production_v7.py'")

if __name__ == "__main__":
    main()
