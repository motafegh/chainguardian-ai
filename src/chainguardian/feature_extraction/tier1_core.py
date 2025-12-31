"""
Tier 1: Core Features (56 total)
Auto-discovery of detectors + Direct Slither API + Complexity + LOC + Risk Scores
"""

from typing import Dict, Any, Set
from slither import Slither
from slither.core.declarations import Contract
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# AUTO-DISCOVERY OF DETECTORS
# ============================================================================

def auto_discover_detectors() -> Dict[str, str]:
    """
    Auto-discover all available detectors from Slither's registry.
    Maps detector names to grouped feature flags.

    Returns:
        Dictionary mapping detector name (ARGUMENT) to feature flag
    """
    try:
        import slither.detectors.all_detectors as detector_module
        import inspect
    except ImportError:
        logger.error("Failed to import slither.detectors.all_detectors")
        return {}

    detector_map = {}

    # Get all detector classes from the module
    all_detectors = []
    for name in dir(detector_module):
        obj = getattr(detector_module, name)
        # Check if it's a class and has ARGUMENT attribute (detector classes have this)
        if inspect.isclass(obj) and hasattr(obj, 'ARGUMENT'):
            all_detectors.append(obj)

    # Define detector categories for grouping
    DETECTOR_CATEGORIES = {
        'has_reentrancy': ['reentrancy-eth', 'reentrancy-no-eth', 'reentrancy-unlimited-gas'],
        'has_tx_origin': ['tx-origin'],
        'has_unchecked_call': ['unchecked-send', 'unchecked-lowlevel', 'low-level-calls'],
        'has_delegatecall': ['controlled-delegatecall', 'delegatecall-loop'],
        'has_timestamp_dependence': ['timestamp', 'weak-prng', 'block-timestamp'],
        'has_access_control_issue': ['arbitrary-send-eth', 'arbitrary-send-erc20',
                                      'arbitrary-send-erc20-no-permit', 'suicidal',
                                      'unprotected-upgrade', 'unprotected-upgradeable'],
        'has_arithmetic_issue': ['divide-before-multiply', 'incorrect-shift',
                                 'too-many-digits'],
        'has_unchecked_low_level_call': ['unchecked-transfer'],
        'has_dangerous_strict_equality': ['dangerous-strict-equalities'],
        'has_locked_ether': ['locked-ether'],
        'has_state_variable_shadowing': ['shadowing-state', 'shadowing-local',
                                          'shadowing-abstract'],
        'has_uninitialized_storage': ['uninitialized-state', 'uninitialized-storage',
                                       'uninitialized-local', 'uninitialized-state-variables'],
        'has_naming_convention_violation': ['naming-convention'],
        'has_unused_state_variable': ['unused-state', 'unused-return'],
        'has_costly_loop': ['costly-loop'],
        'has_external_function': ['external-function'],
        'has_deprecated_construct': ['deprecated-standards', 'solc-version',
                                      'incorrect-version', 'pragma', 'floating-pragma'],
        'has_incorrect_equality': ['incorrect-equality'],
        'has_boolean_constant_misuse': ['boolean-cst', 'boolean-equal'],
        'has_divide_before_multiply': ['divide-before-multiply'],
        'has_weak_randomness': ['weak-prng'],
        'has_assembly_usage': ['assembly', 'incorrect-assembly'],
        'has_low_level_calls': ['low-level-calls', 'controlled-array-length'],
    }

    # Build reverse mapping
    for feature_flag, detector_names in DETECTOR_CATEGORIES.items():
        for detector_name in detector_names:
            detector_map[detector_name] = feature_flag

    # Auto-discover detectors and add to map if not already grouped
    for detector_class in all_detectors:
        detector_name = detector_class.ARGUMENT

        # If not in predefined categories, create individual flag
        if detector_name not in detector_map:
            # Skip informational/optimization detectors for Tier 1
            impact = detector_class.IMPACT
            if impact in ['HIGH', 'MEDIUM', 'LOW']:
                # Create individual flag (will be similar to Tier 4 but grouped)
                sanitized_name = detector_name.replace('-', '_')
                detector_map[detector_name] = f'has_{sanitized_name}'

    logger.info(f"Auto-discovered {len(detector_map)} detector mappings")
    return detector_map


# ============================================================================
# TIER 1 FEATURE EXTRACTION
# ============================================================================

def extract_tier1_features(slither: Slither, contract: Contract,
                          detector_results: list = None) -> Dict[str, Any]:
    """
    Extract all 56 Tier 1 core features.

    Args:
        slither: Slither analysis object
        contract: Target contract object
        detector_results: Pre-run detector results (optional, for performance)

    Returns:
        Dictionary with 56 core features
    """
    features = {}

    try:
        # Run detectors if not provided
        if detector_results is None:
            logger.debug("Running Slither detectors...")
            detector_results = slither.run_detectors()

        # Extract detector-based features (23 flags + 3 severity counts)
        detector_features = _extract_detector_features(detector_results, contract.name)
        features.update(detector_features)

        # Extract API-based counts (8 features)
        api_features = _extract_api_counts(contract)
        features.update(api_features)

        # Extract complexity metrics (3 features)
        complexity_features = _extract_complexity_metrics(contract)
        features.update(complexity_features)

        # Extract code quality metrics (3 features)
        if slither.filename:
            code_features = _extract_code_metrics(Path(slither.filename))
            features.update(code_features)
        else:
            features.update({
                'lines_of_code': 0,
                'comment_lines': 0,
                'comment_to_code_ratio': 0.0,
            })

        # Calculate detector statistics (7 features)
        stat_features = _calculate_detector_stats(detector_features, features)
        features.update(stat_features)

        # Calculate risk scores (4 features)
        risk_features = _calculate_risk_scores(features)
        features.update(risk_features)

    except Exception as e:
        logger.error(f"Tier 1 extraction failed: {e}")
        # Return defaults on failure
        from .feature_spec import TIER_DEFINITIONS
        for feature_name in TIER_DEFINITIONS['tier1']:
            if feature_name not in features:
                if 'has_' in feature_name or 'is_' in feature_name:
                    features[feature_name] = False
                elif 'ratio' in feature_name or 'score' in feature_name:
                    features[feature_name] = 0.0
                else:
                    features[feature_name] = 0

    return features


# ============================================================================
# DETECTOR FEATURE EXTRACTION
# ============================================================================

def _extract_detector_features(detector_results: list, contract_name: str) -> Dict[str, Any]:
    """
    Extract detector flags and severity counts from Slither detector results.

    Args:
        detector_results: List of detector results from slither.run_detectors()
        contract_name: Name of target contract for filtering

    Returns:
        Dictionary with 26 features (23 boolean flags + 3 severity counts)
    """
    features = {}

    # Initialize all detector flags to False
    detector_map = auto_discover_detectors()
    unique_flags = set(detector_map.values())
    for flag in unique_flags:
        features[flag] = False

    # Initialize severity counts
    features['high_severity_count'] = 0
    features['medium_severity_count'] = 0
    features['low_severity_count'] = 0

    # Track detectors that fired
    fired_detectors = set()

    # Process detector results
    for detector_result in detector_results:
        # Handle nested list structure
        if not isinstance(detector_result, list):
            detector_result = [detector_result]

        for result in detector_result:
            if not isinstance(result, dict):
                continue

            # Extract detector metadata
            check_name = result.get('check') or result.get('detector', '')
            if not check_name:
                continue

            impact = result.get('impact', '').lower()

            # Filter for target contract if possible
            description = result.get('description', '').lower()
            if contract_name and contract_name.lower() not in description:
                # Skip results not related to target contract
                continue

            # Map detector to feature flag
            if check_name in detector_map:
                feature_flag = detector_map[check_name]
                features[feature_flag] = True
                fired_detectors.add(check_name)

            # Count by severity
            if impact == 'high':
                features['high_severity_count'] += 1
            elif impact == 'medium':
                features['medium_severity_count'] += 1
            elif impact in ['low', 'informational']:
                features['low_severity_count'] += 1

    logger.debug(f"Detector extraction: {len(fired_detectors)} unique detectors fired")
    return features


# ============================================================================
# API-BASED COUNTS
# ============================================================================

def _extract_api_counts(contract: Contract) -> Dict[str, int]:
    """
    Extract contract-level counts directly from Slither API.
    No manual counting required!

    Args:
        contract: Slither Contract object

    Returns:
        Dictionary with 8 API count features
    """
    return {
        'num_functions': len(contract.functions),
        'num_state_vars': len(contract.state_variables),
        'num_modifiers': len(contract.modifiers),
        'num_events': len(contract.events),
        'num_external_calls': sum(
            len(f.external_calls_as_expressions) for f in contract.functions
        ),
        'num_low_level_calls': sum(
            len(f.low_level_calls) for f in contract.functions
        ),
        'num_payable_functions': sum(
            1 for f in contract.functions if f.payable
        ),
        'inheritance_depth': len(contract.inheritance),
    }


# ============================================================================
# COMPLEXITY METRICS
# ============================================================================

def _extract_complexity_metrics(contract: Contract) -> Dict[str, int]:
    """
    Calculate cyclomatic complexity metrics.

    Complexity = 1 + number of decision points (if, require, loop)

    Args:
        contract: Slither Contract object

    Returns:
        Dictionary with 3 complexity features
    """
    complexities = []

    for function in contract.functions_declared:
        complexity = 1  # Base complexity

        for node in function.nodes:
            node_type = str(node.type).lower()
            # Increment for each decision point
            if any(kw in node_type for kw in ['if', 'require', 'loop', 'assert']):
                complexity += 1

        complexities.append(complexity)

    if not complexities:
        return {
            'max_cyclomatic_complexity': 0,
            'avg_function_complexity': 0,
            'total_cyclomatic_complexity': 0,
        }

    return {
        'max_cyclomatic_complexity': max(complexities),
        'avg_function_complexity': int(sum(complexities) / len(complexities)),
        'total_cyclomatic_complexity': sum(complexities),
    }


# ============================================================================
# CODE QUALITY METRICS
# ============================================================================

def _extract_code_metrics(file_path: Path) -> Dict[str, Any]:
    """
    Extract LOC and comment metrics by parsing source code.

    Args:
        file_path: Path to Solidity source file

    Returns:
        Dictionary with 3 code quality features
    """
    try:
        source_code = file_path.read_text(encoding='utf-8')
        lines = source_code.split('\n')

        # Count non-empty lines
        non_empty_lines = [line for line in lines if line.strip()]
        loc = len(non_empty_lines)

        # Count comment lines
        comment_lines = 0
        in_block_comment = False

        for line in lines:
            stripped = line.strip()

            # Handle block comments /* ... */
            if '/*' in stripped:
                in_block_comment = True
                comment_lines += 1
                if '*/' in stripped:
                    in_block_comment = False
                continue

            if in_block_comment:
                comment_lines += 1
                if '*/' in stripped:
                    in_block_comment = False
                continue

            # Handle line comments //
            if stripped.startswith('//'):
                comment_lines += 1

        # Calculate ratio
        ratio = comment_lines / loc if loc > 0 else 0.0

        return {
            'lines_of_code': loc,
            'comment_lines': comment_lines,
            'comment_to_code_ratio': round(ratio, 3),
        }

    except Exception as e:
        logger.warning(f"Failed to extract code metrics from {file_path}: {e}")
        return {
            'lines_of_code': 0,
            'comment_lines': 0,
            'comment_to_code_ratio': 0.0,
        }


# ============================================================================
# DETECTOR STATISTICS
# ============================================================================

def _calculate_detector_stats(detector_features: Dict, all_features: Dict) -> Dict[str, int]:
    """
    Calculate aggregate detector statistics.

    Args:
        detector_features: Dictionary with detector flags and severity counts
        all_features: Dictionary with all features (for LOC)

    Returns:
        Dictionary with 7 detector statistic features
    """
    # Count total detectors fired (count True flags)
    total_fired = sum(
        1 for key, value in detector_features.items()
        if key.startswith('has_') and value is True
    )

    # Count confidence levels (placeholder - Slither doesn't separate these in results)
    # These will be properly calculated in Tier 3 with more detailed analysis
    high_conf = detector_features.get('high_severity_count', 0)  # Approximate
    med_conf = detector_features.get('medium_severity_count', 0)
    low_conf = detector_features.get('low_severity_count', 0)

    # Count unique vulnerability types (count how many different has_* flags are True)
    unique_types = sum(
        1 for key, value in detector_features.items()
        if key.startswith('has_') and value is True
    )

    # Calculate ratios (avoid division by zero)
    num_functions = all_features.get('num_functions', 0) or 1  # Use 1 if 0 or None
    loc = all_features.get('lines_of_code', 0) or 1

    return {
        'total_detectors_fired': total_fired,
        'high_confidence_count': high_conf,
        'medium_confidence_count': med_conf,
        'low_confidence_count': low_conf,
        'unique_detector_types': unique_types,
        'detectors_per_function': round(total_fired / num_functions, 2),
        'detectors_per_loc': round((total_fired / loc) * 100, 2),  # Per 100 LOC
    }


# ============================================================================
# RISK SCORES
# ============================================================================

def _calculate_risk_scores(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate composite risk scores from extracted features.

    Risk scores help ML models learn faster by providing pre-computed combinations.

    Args:
        features: Dictionary with all extracted features

    Returns:
        Dictionary with 4 risk score features
    """
    high_sev = features.get('high_severity_count', 0)
    med_sev = features.get('medium_severity_count', 0)
    low_sev = features.get('low_severity_count', 0)

    # Score 1: Simple risk score (weighted sum)
    security_risk_score = (high_sev * 10) + (med_sev * 5) + (low_sev * 1)

    # Score 2: Code quality score (complexity + LOC-based)
    max_complexity = features.get('max_cyclomatic_complexity', 0)
    avg_complexity = features.get('avg_function_complexity', 0)
    comment_ratio = features.get('comment_to_code_ratio', 0)

    # Lower score = better quality
    code_quality_score = (
        (max_complexity * 2) +
        avg_complexity -
        (comment_ratio * 10)  # Comments reduce score
    )
    code_quality_score = max(0, code_quality_score)  # No negative scores

    # Score 3: Overall risk (combination)
    overall_risk_score = security_risk_score + (code_quality_score * 0.5)

    # Score 4: Binary high-risk flag
    is_high_risk = (
        security_risk_score > 20 or
        high_sev >= 3 or
        features.get('unique_detector_types', 0) >= 3
    )

    return {
        'security_risk_score': round(security_risk_score, 2),
        'code_quality_score': round(code_quality_score, 2),
        'overall_risk_score': round(overall_risk_score, 2),
        'is_high_risk': is_high_risk,
    }
