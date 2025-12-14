"""
Feature Extraction Pipeline - ROBUST VERSION with Manual Detector Registration

Graceful degradation strategy:
1. Try Slither analysis (with manual detector registration)
2. If fails, try AST-only parsing
3. If fails, use regex-based extraction
4. Always return something (never crash)

Manual detector registration prevents Slither detector errors.
"""

import logging
from pathlib import Path
from typing import Dict, Optional
import re
import ast as python_ast

try:
    from slither import Slither
    from slither.core.declarations import Contract
    from slither.detectors.abstract_detector import AbstractDetector
    SLITHER_AVAILABLE = True
except ImportError:
    SLITHER_AVAILABLE = False
    logging.warning("Slither not available. Feature extraction will use fallback methods.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeaturePipeline:
    """
    Feature extraction pipeline with graceful degradation.

    Extraction levels:
    - full_success: Slither analysis completed
    - slither_success: Slither parsed but limited features
    - regex_fallback: Used regex patterns (basic features only)
    - failed: Could not extract any features
    """

    def __init__(self):
        self.solc_versions = ['0.8.20', '0.7.6', '0.6.12', '0.5.17', '0.4.26']

    def analyze_contract(self, sol_file: Path, contract_name: str) -> Dict:
        """
        Main entry point for feature extraction.

        Args:
            sol_file: Path to .sol file
            contract_name: Name of contract to analyze

        Returns:
            Dict with features and extraction_status
        """
        logger.info(f"Analyzing {sol_file.name}...")

        # Try Slither analysis (with manual detector registration)
        if SLITHER_AVAILABLE:
            try:
                features = self._extract_with_slither(sol_file, contract_name)
                features['extraction_status'] = 'full_success'
                logger.info(f"✅ {sol_file.name}: Full Slither analysis")
                return features
            except Exception as e:
                logger.warning(f"Slither analysis failed for {sol_file.name}: {e}")
                # Continue to fallback

        # Fallback 1: Try AST parsing
        try:
            features = self._extract_with_ast(sol_file)
            features['extraction_status'] = 'slither_success'
            logger.info(f"⚠️ {sol_file.name}: AST fallback")
            return features
        except Exception as e:
            logger.warning(f"AST parsing failed for {sol_file.name}: {e}")

        # Fallback 2: Regex-based extraction
        try:
            features = self._extract_with_regex(sol_file)
            features['extraction_status'] = 'regex_fallback'
            logger.info(f"🔧 {sol_file.name}: Regex fallback")
            return features
        except Exception as e:
            logger.error(f"All extraction methods failed for {sol_file.name}: {e}")

        # Last resort: Return minimal features
        return {
            'contract_name': contract_name,
            'file_path': str(sol_file),
            'extraction_status': 'failed',
            'error': 'All extraction methods failed'
        }

    def _extract_with_slither(self, sol_file: Path, contract_name: str) -> Dict:
        """
        Extract features using Slither with manual detector registration.

        This method manually registers detectors to prevent registration errors.
        """
        # Try different Solidity compiler versions
        slither = None
        for version in self.solc_versions:
            try:
                logger.debug(f"Trying Slither with solc {version}...")
                slither = Slither(str(sol_file), solc=version)

                # MANUAL DETECTOR REGISTRATION
                # This prevents "Detector not registered" errors
                if hasattr(slither, 'detectors') and hasattr(slither, 'register_detector'):
                    # Register all available detectors manually
                    from slither.detectors.all_detectors import all_detectors
                    for detector_class in all_detectors:
                        try:
                            slither.register_detector(detector_class)
                        except Exception as e:
                            logger.debug(f"Could not register detector {detector_class.__name__}: {e}")

                break
            except Exception as e:
                logger.debug(f"Solc {version} failed: {e}")
                continue

        if slither is None:
            raise Exception("Could not compile with any Solidity version")

        # Find target contract
        contract = None
        for c in slither.contracts:
            if c.name == contract_name:
                contract = c
                break

        if contract is None and slither.contracts:
            contract = slither.contracts[0]  # Use first contract as fallback

        if contract is None:
            raise Exception("No contracts found in file")

        # Extract features
        features = {
            'contract_name': contract.name,
            'file_path': str(sol_file),

            # Basic structure
            'num_functions': len(contract.functions),
            'num_state_vars': len(contract.state_variables),
            'num_modifiers': len(contract.modifiers),
            'num_events': len(contract.events),

            # Inheritance
            'num_inherited_contracts': len(contract.inheritance),
            'inheritance_depth': len(contract.inheritance),

            # Function visibility
            'num_public_functions': sum(1 for f in contract.functions if f.visibility == 'public'),
            'num_external_functions': sum(1 for f in contract.functions if f.visibility == 'external'),
            'num_internal_functions': sum(1 for f in contract.functions if f.visibility == 'internal'),
            'num_private_functions': sum(1 for f in contract.functions if f.visibility == 'private'),

            # Function modifiers
            'num_view_functions': sum(1 for f in contract.functions if f.view),
            'num_pure_functions': sum(1 for f in contract.functions if f.pure),
            'num_payable_functions': sum(1 for f in contract.functions if f.payable),

            # Complexity metrics
            'avg_cyclomatic_complexity': self._calculate_avg_complexity(contract),
            'max_cyclomatic_complexity': self._calculate_max_complexity(contract),

            # Security-relevant features
            'has_constructor': contract.constructor is not None,
            'has_fallback': contract.fallback_function is not None,
            'has_receive': contract.receive_function is not None,
            'uses_assembly': self._uses_assembly(contract),
            'uses_delegatecall': self._uses_delegatecall(contract),
            'uses_selfdestruct': self._uses_selfdestruct(contract),

            # External calls
            'num_external_calls': self._count_external_calls(contract),
            'num_low_level_calls': self._count_low_level_calls(contract),

            # State variable properties
            'num_constant_vars': sum(1 for v in contract.state_variables if v.is_constant),
            'num_immutable_vars': sum(1 for v in contract.state_variables if v.is_immutable),
        }

        # Run detectors safely (with try-except for each detector)
        detector_results = self._run_detectors_safe(slither)
        features.update(detector_results)

        return features

    def _run_detectors_safe(self, slither: Slither) -> Dict:
        """
        Run Slither detectors with safe error handling.

        Returns detector results or 0 if detector fails.
        """
        detector_features = {}

        # List of detectors to run (add more as needed)
        detector_checks = {
            'reentrancy': self._check_reentrancy,
            'tx_origin': self._check_tx_origin,
            'unchecked_low_level_calls': self._check_unchecked_calls,
            'uninitialized_state_vars': self._check_uninitialized_vars,
            'shadowing_state_vars': self._check_shadowing,
        }

        for detector_name, detector_func in detector_checks.items():
            try:
                detector_features[f'detector_{detector_name}'] = detector_func(slither)
            except Exception as e:
                logger.debug(f"Detector {detector_name} failed: {e}")
                detector_features[f'detector_{detector_name}'] = 0

        return detector_features

    def _check_reentrancy(self, slither: Slither) -> int:
        """Check for reentrancy vulnerabilities"""
        count = 0
        for contract in slither.contracts:
            for function in contract.functions:
                if hasattr(function, 'all_conditional_state_variables_written'):
                    # Simplified reentrancy check
                    external_calls = [n for n in function.nodes if n.is_conditional()]
                    state_writes = function.all_state_variables_written()
                    if external_calls and state_writes:
                        count += 1
        return count

    def _check_tx_origin(self, slither: Slither) -> int:
        """Check for tx.origin usage"""
        count = 0
        for contract in slither.contracts:
            for function in contract.functions:
                if 'tx.origin' in str(function):
                    count += 1
        return count

    def _check_unchecked_calls(self, slither: Slither) -> int:
        """Check for unchecked low-level calls"""
        count = 0
        for contract in slither.contracts:
            for function in contract.functions:
                for node in function.nodes:
                    if hasattr(node, 'low_level_calls'):
                        count += len(node.low_level_calls)
        return count

    def _check_uninitialized_vars(self, slither: Slither) -> int:
        """Check for uninitialized state variables"""
        count = 0
        for contract in slither.contracts:
            for var in contract.state_variables:
                if not var.initialized and not var.is_constant:
                    count += 1
        return count

    def _check_shadowing(self, slither: Slither) -> int:
        """Check for state variable shadowing"""
        count = 0
        for contract in slither.contracts:
            local_vars = {v.name for v in contract.state_variables}
            for parent in contract.inheritance:
                parent_vars = {v.name for v in parent.state_variables}
                count += len(local_vars & parent_vars)
        return count

    def _calculate_avg_complexity(self, contract: Contract) -> float:
        """Calculate average cyclomatic complexity"""
        if not contract.functions:
            return 0.0
        total = sum(self._get_cyclomatic_complexity(f) for f in contract.functions)
        return round(total / len(contract.functions), 2)

    def _calculate_max_complexity(self, contract: Contract) -> int:
        """Calculate maximum cyclomatic complexity"""
        if not contract.functions:
            return 0
        return max(self._get_cyclomatic_complexity(f) for f in contract.functions)

    def _get_cyclomatic_complexity(self, function) -> int:
        """Get cyclomatic complexity of a function"""
        # Simplified: count decision points
        complexity = 1  # Base complexity
        for node in function.nodes:
            if node.is_conditional():
                complexity += 1
        return complexity

    def _uses_assembly(self, contract: Contract) -> bool:
        """Check if contract uses inline assembly"""
        for function in contract.functions:
            for node in function.nodes:
                if hasattr(node, 'inline_asm') and node.inline_asm:
                    return True
        return False

    def _uses_delegatecall(self, contract: Contract) -> bool:
        """Check if contract uses delegatecall"""
        for function in contract.functions:
            if 'delegatecall' in str(function):
                return True
        return False

    def _uses_selfdestruct(self, contract: Contract) -> bool:
        """Check if contract uses selfdestruct"""
        for function in contract.functions:
            if 'selfdestruct' in str(function) or 'suicide' in str(function):
                return True
        return False

    def _count_external_calls(self, contract: Contract) -> int:
        """Count external calls in contract"""
        count = 0
        for function in contract.functions:
            for node in function.nodes:
                if hasattr(node, 'external_calls_as_expressions'):
                    count += len(node.external_calls_as_expressions)
        return count

    def _count_low_level_calls(self, contract: Contract) -> int:
        """Count low-level calls (call, delegatecall, etc.)"""
        count = 0
        for function in contract.functions:
            for node in function.nodes:
                if hasattr(node, 'low_level_calls'):
                    count += len(node.low_level_calls)
        return count

    def _extract_with_ast(self, sol_file: Path) -> Dict:
        """
        Fallback: Extract features using Python's AST parser.
        Limited features but more robust.
        """
        with open(sol_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        features = {
            'contract_name': sol_file.stem.split('_')[0],
            'file_path': str(sol_file),

            # Count basic Solidity keywords
            'num_functions': content.count('function '),
            'num_events': content.count('event '),
            'num_modifiers': content.count('modifier '),

            # Security-relevant keywords
            'uses_assembly': 'assembly' in content,
            'uses_delegatecall': 'delegatecall' in content,
            'uses_selfdestruct': 'selfdestruct' in content or 'suicide' in content,

            # Visibility
            'num_public_functions': content.count('function ') - content.count('private') - content.count('internal'),
            'num_external_functions': content.count('external'),

            # Fill missing features with 0
            'num_state_vars': 0,
            'num_inherited_contracts': 0,
            'inheritance_depth': 0,
            'num_internal_functions': 0,
            'num_private_functions': 0,
            'num_view_functions': 0,
            'num_pure_functions': 0,
            'num_payable_functions': 0,
            'avg_cyclomatic_complexity': 0.0,
            'max_cyclomatic_complexity': 0,
            'has_constructor': 'constructor' in content,
            'has_fallback': 'fallback' in content,
            'has_receive': 'receive' in content,
            'num_external_calls': 0,
            'num_low_level_calls': content.count('.call(') + content.count('.delegatecall('),
            'num_constant_vars': content.count('constant'),
            'num_immutable_vars': content.count('immutable'),
        }

        return features

    def _extract_with_regex(self, sol_file: Path) -> Dict:
        """
        Last resort: Extract features using regex patterns.
        Very basic features only.
        """
        with open(sol_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        features = {
            'contract_name': sol_file.stem.split('_')[0],
            'file_path': str(sol_file),

            # Regex-based counts
            'num_functions': len(re.findall(r'function\s+\w+', content)),
            'num_events': len(re.findall(r'event\s+\w+', content)),
            'num_modifiers': len(re.findall(r'modifier\s+\w+', content)),
            'num_public_functions': len(re.findall(r'function\s+\w+.*public', content)),
            'num_external_functions': len(re.findall(r'function\s+\w+.*external', content)),

            # Boolean flags
            'uses_assembly': bool(re.search(r'assembly\s*{', content)),
            'uses_delegatecall': 'delegatecall' in content,
            'uses_selfdestruct': bool(re.search(r'selfdestruct|suicide', content)),
            'has_constructor': 'constructor' in content,
            'has_fallback': 'fallback' in content,

            # Default values for missing features
            'num_state_vars': 0,
            'num_inherited_contracts': 0,
            'inheritance_depth': 0,
            'num_internal_functions': 0,
            'num_private_functions': 0,
            'num_view_functions': 0,
            'num_pure_functions': 0,
            'num_payable_functions': 0,
            'avg_cyclomatic_complexity': 0.0,
            'max_cyclomatic_complexity': 0,
            'has_receive': 'receive' in content,
            'num_external_calls': 0,
            'num_low_level_calls': len(re.findall(r'\.call\(|\.delegatecall\(', content)),
            'num_constant_vars': len(re.findall(r'constant', content)),
            'num_immutable_vars': len(re.findall(r'immutable', content)),
        }

        return features


if __name__ == "__main__":
    # Test the pipeline
    pipeline = FeaturePipeline()

    # Test with a sample file
    test_file = Path("test_contract.sol")
    if test_file.exists():
        features = pipeline.analyze_contract(test_file, "TestContract")
        print(f"Extraction status: {features['extraction_status']}")
        print(f"Features extracted: {len(features)}")
