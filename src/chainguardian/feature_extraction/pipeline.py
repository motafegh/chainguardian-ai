"""
Unified feature extraction pipeline
Combines Slither JSON + AST analysis into single feature vector
"""

import json
from pathlib import Path
from typing import Dict, Optional
import pandas as pd
import logging

from contract_analyzer import SlitherParser, ContractFeatures
from ast_analyzer import ASTFeatureExtractor

logger = logging.getLogger(__name__)


class FeaturePipeline:
    """
    End-to-end pipeline: Contract → Feature Vector → ML-ready format
    WHY: ML models need consistent feature vectors across all contracts
    """
    
    def __init__(self):
        """
        Initialize with empty feature list
        WHY: We'll collect features from multiple contracts into a dataset
        """
        self.features: list[Dict] = []
    
    def analyze_contract(
        self, 
        contract_path: Path, 
        contract_name: str,
        json_output_path: Optional[Path] = None
    ) -> Dict:
        """
        Extract ALL features from a single contract
        
        Args:
            contract_path: Path to .sol file
            contract_name: Name of contract to analyze
            json_output_path: Path to existing Slither JSON (optional)
        
        Returns:
            Complete feature dict combining JSON + AST features
        """
        logger.info(f"Analyzing {contract_name} from {contract_path}")
        
        # Initialize feature dict with metadata
        combined_features = {
            'contract_name': contract_name,
            'file_path': str(contract_path),
        }
        
        # STEP 1: Extract vulnerability flags from JSON
        if json_output_path and json_output_path.exists():
            parser = SlitherParser(json_output_path)
            vuln_features = parser.extract_features(contract_name)
            
            # Convert dataclass to dict
            combined_features.update({
                'has_reentrancy': vuln_features.has_reentrancy,
                'has_access_control_issues': vuln_features.has_access_control_issues,
                'has_timestamp_dependency': vuln_features.has_timestamp_dependency,
                'has_unchecked_call': vuln_features.has_unchecked_call,
                'high_severity_count': vuln_features.high_severity_count,
                'medium_severity_count': vuln_features.medium_severity_count,
                'low_severity_count': vuln_features.low_severity_count,
            })
        else:
            logger.warning("No JSON output provided, skipping vulnerability flags")
        
        # STEP 2: Extract AST features
        try:
            ast_extractor = ASTFeatureExtractor(contract_path)
            ast_features = ast_extractor.extract_features(contract_name)
            combined_features.update(ast_features)
        except Exception as e:
            logger.error(f"AST extraction failed: {e}")
            # Set default values if extraction fails
            combined_features.update({
                'num_functions': 0,
                'num_external_calls': 0,
                'num_state_vars': 0,
                'num_modifiers': 0,
                'max_cyclomatic_complexity': 0,
                'num_low_level_calls': 0,
            })
        
        # Store in collection
        self.features.append(combined_features)
        
        logger.info(f"Extracted {len(combined_features)} features for {contract_name}")
        return combined_features
    
    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert collected features to pandas DataFrame
        WHY: scikit-learn and PyTorch expect DataFrame/numpy format
        """
        if not self.features:
            logger.warning("No features collected yet")
            return pd.DataFrame()
        
        df = pd.DataFrame(self.features)
        logger.info(f"Created DataFrame with {len(df)} contracts and {len(df.columns)} features")
        return df
    
    def save_dataset(self, output_path: Path):
        """
        Save features as CSV for training
        WHY: CSV is version-controllable and inspectable
        """
        df = self.to_dataframe()
        df.to_csv(output_path, index=False)
        logger.info(f"Saved dataset to {output_path}")
