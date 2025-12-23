"""Test Final Hybrid Predictor"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from chainguardian.ml.models.hybrid_predictor import HybridPredictor

# Initialize
predictor = HybridPredictor(enable_shap=True)

# Test features
test_features = {
    'cei_violations': 3,
    'state_after_call_count': 3,
    'has_reentrancy_guard': False,
    'cei_pattern_score': 0.5,
    'lines_of_code': 450,
    'num_functions': 12,
    'has_reentrancy': True,
    'total_detector_hits': 15
}

# Predict with LLM-ready output
result = predictor.predict(
    features=test_features,
    return_details=True,
    explain=True,
    llm_ready=True  # ⭐ This formats for LLM
)

import json
print(json.dumps(result, indent=2))