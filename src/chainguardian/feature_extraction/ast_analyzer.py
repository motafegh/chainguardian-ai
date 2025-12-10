"""
AST-based feature extraction using Slither Python API
WHY: Static detector flags alone aren't enough - need code structure metrics
"""

from slither import Slither
from pathlib import Path
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class ASTFeatureExtractor:
    """
    Extracts structural features from smart contract AST
    Research: Control flow complexity correlates with vulnerability likelihood
    """
    
    def __init__(self, contract_path: Path):
        """
        WHY: Slither's Python API gives us direct AST access
        """
        self.contract_path = contract_path
        # Slither analyzes contract and builds AST
        self.slither = Slither(str(contract_path))
        logger.info(f"Analyzed AST for {contract_path}")
    
    def extract_features(self, contract_name: str) -> Dict[str, int]:
        """
        Extract countable features from AST
        
        Returns:
            Dict with keys: num_functions, num_external_calls, 
                           num_state_vars, cyclomatic_complexity
        """
        features = {
            'num_functions': 0,
            'num_external_calls': 0,
            'num_state_vars': 0,
            'num_modifiers': 0,
            'max_cyclomatic_complexity': 0,
            'num_low_level_calls': 0,  # NEW: Track dangerous low-level calls separately
        }
        
        # Find target contract (file might have multiple contracts)
        contract = None
        for c in self.slither.contracts:
            if c.name == contract_name:
                contract = c
                break
        
        if not contract:
            logger.warning(f"Contract {contract_name} not found")
            return features
        
        # Count functions (excluding inherited)
        features['num_functions'] = len(contract.functions_declared)
        
        # Count state variables
        features['num_state_vars'] = len(contract.state_variables_declared)
        
        # Count modifiers
        features['num_modifiers'] = len(contract.modifiers_declared)
        
        # Analyze each function
        for func in contract.functions_declared:
            # Count external calls (ANY external interaction)
            # WHY: Slither tracks these as CallExpression objects
            features['num_external_calls'] += len(func.external_calls_as_expressions)
            
            # Count low-level calls specifically (call, delegatecall, etc.)
            # WHY: These are MORE dangerous than high-level calls (transfer/send)
            features['num_low_level_calls'] += len(func.low_level_calls)
            
            # Cyclomatic complexity (measure of code paths)
            # WHY: Higher complexity = harder to audit, more bugs
            complexity = self._calculate_complexity(func)
            features['max_cyclomatic_complexity'] = max(
                features['max_cyclomatic_complexity'], 
                complexity
            )
        
        logger.info(f"Extracted AST features for {contract_name}: {features}")
        return features
    
    def _calculate_complexity(self, function) -> int:
        """
        Simplified cyclomatic complexity: count decision points
        WHY: V(G) = E - N + 2P where E=edges, N=nodes, P=connected components
        Approximation: count if/for/while/require statements
        """
        complexity = 1  # Base complexity
        
        # Count control flow statements
        for node in function.nodes:
            node_type = str(node.type)
            if any(keyword in node_type.lower() for keyword in ['if', 'require', 'loop']):
                complexity += 1
        
        return complexity
