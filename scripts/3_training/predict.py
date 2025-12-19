"""
Vulnerability Prediction Script

Use trained ML models to predict vulnerabilities in new smart contracts.

Usage:
    # Predict on a single contract
    python predict.py --contract path/to/contract.sol
    
    # Predict on all contracts in a directory
    python predict.py --directory path/to/contracts/
    
    # Use specific models
    python predict.py --contract path/to/contract.sol --models reentrancy unchecked_call
"""

import argparse
from pathlib import Path
import pandas as pd
import joblib
import sys
import logging
from typing import Dict, List

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from chainguardian.feature_extraction.pipeline import FeaturePipeline

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


# Code structure features (must match training!)
REQUIRED_FEATURES = [
    'num_functions', 'num_external_calls', 'num_state_vars',
    'num_modifiers', 'max_cyclomatic_complexity', 'num_low_level_calls',
    'lines_of_code', 'num_contracts_in_file', 'num_dependencies',
    'avg_function_complexity', 'num_functions_high_complexity',
    'num_comments', 'comment_to_code_ratio', 'num_payable_functions',
    'num_library_calls', 'inheritance_depth', 'num_unused_functions'
]


def load_models() -> Dict[str, object]:
    """
    Load all trained models from models/vulnerability_specific/.
    
    Returns:
        Dictionary mapping vulnerability names to loaded models
    """
    models_dir = Path('models/vulnerability_specific')
    
    if not models_dir.exists():
        logger.error(f"Models directory not found: {models_dir}")
        logger.error("Run train_multi_label.py first to train models!")
        return {}
    
    models = {}
    for model_file in models_dir.glob('has_*_rf.pkl'):
        vuln_name = model_file.stem.replace('_rf', '')
        try:
            models[vuln_name] = joblib.load(model_file)
            logger.debug(f"Loaded model: {vuln_name}")
        except Exception as e:
            logger.warning(f"Failed to load {model_file.name}: {e}")
    
    logger.info(f"✓ Loaded {len(models)} models")
    return models


def extract_features(contract_path: Path) -> Dict:
    """
    Extract code structure features from a contract.
    
    Args:
        contract_path: Path to Solidity file or directory
    
    Returns:
        Dictionary of features
    """
    pipeline = FeaturePipeline()
    
    # Get contract name from path
    if contract_path.is_dir():
        contract_name = contract_path.name
    else:
        contract_name = contract_path.stem
    
    # Extract features
    features = pipeline.analyze_contract(contract_path, contract_name)
    
    return features


def predict_vulnerabilities(
    features: Dict,
    models: Dict[str, object],
    threshold: float = 0.5
) -> pd.DataFrame:
    """
    Predict vulnerabilities using all loaded models.
    
    Args:
        features: Contract features dictionary
        models: Dictionary of trained models
        threshold: Probability threshold for positive prediction
    
    Returns:
        DataFrame with predictions and probabilities
    """
    # Extract only required features
    feature_vector = []
    missing_features = []
    
    for feat in REQUIRED_FEATURES:
        if feat in features:
            feature_vector.append(features[feat])
        else:
            feature_vector.append(0)  # Default to 0 if missing
            missing_features.append(feat)
    
    if missing_features:
        logger.warning(f"Missing features (using 0): {missing_features[:3]}...")
    
    # Convert to DataFrame (single row)
    X = pd.DataFrame([feature_vector], columns=REQUIRED_FEATURES)
    
    # Predict with each model
    predictions = []
    
    for vuln_name, model in models.items():
        try:
            prob = model.predict_proba(X)[0, 1]  # Probability of positive class
            pred = 1 if prob >= threshold else 0
            
            predictions.append({
                'vulnerability': vuln_name.replace('has_', '').replace('_', ' ').title(),
                'prediction': 'VULNERABLE' if pred == 1 else 'SAFE',
                'probability': prob,
                'confidence': 'HIGH' if abs(prob - 0.5) > 0.3 else 'MEDIUM' if abs(prob - 0.5) > 0.15 else 'LOW'
            })
        except Exception as e:
            logger.warning(f"Prediction failed for {vuln_name}: {e}")
    
    return pd.DataFrame(predictions).sort_values('probability', ascending=False)


def main():
    parser = argparse.ArgumentParser(description='Predict smart contract vulnerabilities')
    parser.add_argument('--contract', type=str, help='Path to single contract file')
    parser.add_argument('--directory', type=str, help='Path to directory of contracts')
    parser.add_argument('--threshold', type=float, default=0.5, help='Probability threshold (0.0-1.0)')
    parser.add_argument('--models', nargs='+', help='Specific models to use (default: all)')
    
    args = parser.parse_args()
    
    if not args.contract and not args.directory:
        parser.error("Provide either --contract or --directory")
    
    print("="*70)
    print("CHAINGUARDIAN AI - VULNERABILITY PREDICTION")
    print("="*70)
    
    # Load models
    logger.info("\nLoading trained models...")
    all_models = load_models()
    
    if not all_models:
        logger.error("No models loaded. Exiting.")
        return
    
    # Filter models if specified
    if args.models:
        filtered_models = {}
        for model_name in args.models:
            key = f"has_{model_name}"
            if key in all_models:
                filtered_models[key] = all_models[key]
            else:
                logger.warning(f"Model not found: {model_name}")
        models = filtered_models
    else:
        models = all_models
    
    logger.info(f"Using {len(models)} models\n")
    
    # Process contracts
    if args.contract:
        contracts = [Path(args.contract)]
    else:
        contracts_dir = Path(args.directory)
        contracts = list(contracts_dir.glob('**/*.sol'))
    
    logger.info(f"Analyzing {len(contracts)} contract(s)...\n")
    
    for contract_path in contracts:
        print("="*70)
        print(f"CONTRACT: {contract_path.name}")
        print("="*70)
        
        # Extract features
        logger.info("Extracting features...")
        features = extract_features(contract_path)
        
        if features.get('failure_reason'):
            logger.error(f"Feature extraction failed: {features['failure_reason']}")
            continue
        
        # Predict
        logger.info("Running predictions...\n")
        predictions = predict_vulnerabilities(features, models, args.threshold)
        
        # Display results
        print(predictions.to_string(index=False))
        
        # Summary
        vulnerable_count = (predictions['prediction'] == 'VULNERABLE').sum()
        if vulnerable_count > 0:
            print(f"\n⚠️  {vulnerable_count} potential vulnerabilities detected!")
            print("\nRecommendation: Run full Slither analysis for confirmation")
        else:
            print(f"\n✅ No high-probability vulnerabilities detected")
            print("\nNote: This is a screening tool. Manual audit still recommended.")
        
        print()
    
    print("="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
