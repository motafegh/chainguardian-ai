"""
Tier 4: Individual Detector Flags (69 unique, 93 total)
One boolean flag per Slither detector (auto-discovered)
"""

from typing import Dict, Any, List
from slither import Slither
from slither.core.declarations import Contract
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# TIER 4 FEATURE EXTRACTION
# ============================================================================

def extract_tier4_features(slither: Slither, contract: Contract,
                          detector_results: list = None) -> Dict[str, bool]:
    """
    Extract individual detector boolean flags.

    Creates one boolean feature per Slither detector (detector_<name>).
    Auto-discovers all available detectors, making this future-proof.

    Args:
        slither: Slither analysis object
        contract: Target contract object
        detector_results: Pre-run detector results (optional, for performance)

    Returns:
        Dictionary with ~93 detector boolean flags
    """
    features = {}

    try:
        # Auto-discover all detectors
        detector_map = _auto_discover_all_detectors()

        # Initialize all detector flags to False
        for detector_name in detector_map.keys():
            feature_name = _sanitize_detector_name(detector_name)
            features[feature_name] = False

        # Run detectors if not provided
        if detector_results is None:
            logger.debug("Running Slither detectors for Tier 4...")
            detector_results = slither.run_detectors()

        # Mark detectors that fired
        fired_detectors = _extract_fired_detectors(detector_results, contract.name)

        for detector_name in fired_detectors:
            feature_name = _sanitize_detector_name(detector_name)
            if feature_name in features:
                features[feature_name] = True

        logger.info(f"Tier 4: {len(fired_detectors)} detectors fired out of {len(features)} total")

    except Exception as e:
        logger.error(f"Tier 4 extraction failed: {e}")
        # Return defaults on failure (all False)
        pass

    return features


# ============================================================================
# AUTO-DISCOVERY
# ============================================================================

def _auto_discover_all_detectors() -> Dict[str, str]:
    """
    Auto-discover ALL available detectors from Slither's registry.

    Uses Slither's internal detector registry to dynamically discover
    all detector classes. This makes the system future-proof - new
    detectors added to Slither will automatically be included.

    Returns:
        Dictionary mapping detector ARGUMENT (name) to detector class name
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

    for detector_class in all_detectors:
        detector_name = detector_class.ARGUMENT  # e.g., 'reentrancy-eth'
        detector_impact = detector_class.IMPACT   # HIGH, MEDIUM, LOW, INFORMATIONAL
        detector_confidence = detector_class.CONFIDENCE  # HIGH, MEDIUM, LOW

        # Map all detectors (no filtering by impact/confidence in Tier 4)
        detector_map[detector_name] = {
            'class': detector_class.__name__,
            'impact': detector_impact,
            'confidence': detector_confidence,
        }

    logger.info(f"Auto-discovered {len(detector_map)} detectors")
    return detector_map


# ============================================================================
# DETECTOR RESULT PARSING
# ============================================================================

def _extract_fired_detectors(detector_results: list, contract_name: str) -> List[str]:
    """
    Extract list of detector names that fired for the target contract.

    Args:
        detector_results: List of detector results from slither.run_detectors()
        contract_name: Name of target contract for filtering

    Returns:
        List of detector names (ARGUMENT) that fired
    """
    fired_detectors = set()

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

            # Filter for target contract if possible
            description = result.get('description', '').lower()
            if contract_name and contract_name.lower() in description:
                fired_detectors.add(check_name)
            elif not contract_name:
                # If no contract name filtering, include all
                fired_detectors.add(check_name)

    return list(fired_detectors)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _sanitize_detector_name(detector_name: str) -> str:
    """
    Convert detector ARGUMENT to valid feature name.

    Examples:
        'reentrancy-eth' -> 'detector_reentrancy_eth'
        'unchecked-send' -> 'detector_unchecked_send'
        'tx-origin' -> 'detector_tx_origin'

    Args:
        detector_name: Detector ARGUMENT from Slither

    Returns:
        Sanitized feature name
    """
    sanitized = detector_name.replace('-', '_')
    return f'detector_{sanitized}'


def get_tier4_feature_names() -> List[str]:
    """
    Get list of all Tier 4 feature names.

    Useful for:
    - CSV column generation
    - Feature validation
    - Documentation

    Returns:
        List of feature names (detector_<name>)
    """
    detector_map = _auto_discover_all_detectors()
    return [_sanitize_detector_name(name) for name in detector_map.keys()]


def get_detector_metadata(detector_name: str) -> Dict[str, Any]:
    """
    Get metadata for a specific detector.

    Args:
        detector_name: Sanitized detector name (e.g., 'detector_reentrancy_eth')

    Returns:
        Dictionary with impact, confidence, and class name
    """
    # Remove 'detector_' prefix and convert back to ARGUMENT format
    original_name = detector_name.replace('detector_', '').replace('_', '-')

    detector_map = _auto_discover_all_detectors()
    return detector_map.get(original_name, {
        'class': 'Unknown',
        'impact': 'UNKNOWN',
        'confidence': 'UNKNOWN',
    })


# ============================================================================
# FEATURE DESCRIPTION GENERATION
# ============================================================================

def generate_tier4_descriptions() -> Dict[str, str]:
    """
    Generate human-readable descriptions for all Tier 4 features.

    Returns:
        Dictionary mapping feature name to description
    """
    detector_map = _auto_discover_all_detectors()
    descriptions = {}

    for detector_name, metadata in detector_map.items():
        feature_name = _sanitize_detector_name(detector_name)
        impact = metadata.get('impact', 'UNKNOWN')
        confidence = metadata.get('confidence', 'UNKNOWN')

        descriptions[feature_name] = (
            f"Boolean flag indicating '{detector_name}' detector fired "
            f"(Impact: {impact}, Confidence: {confidence})"
        )

    return descriptions


# ============================================================================
# TIER 4 STATISTICS
# ============================================================================

def compute_tier4_statistics(tier4_features: Dict[str, bool]) -> Dict[str, Any]:
    """
    Compute aggregate statistics from Tier 4 features.

    Useful for analyzing detector distributions and patterns.

    Args:
        tier4_features: Dictionary with all Tier 4 boolean flags

    Returns:
        Dictionary with statistics
    """
    total_detectors = len(tier4_features)
    fired_detectors = sum(1 for value in tier4_features.values() if value)

    # Count by impact level (requires metadata lookup)
    detector_map = _auto_discover_all_detectors()
    high_impact = 0
    medium_impact = 0
    low_impact = 0
    informational = 0

    for feature_name, fired in tier4_features.items():
        if not fired:
            continue

        original_name = feature_name.replace('detector_', '').replace('_', '-')
        metadata = detector_map.get(original_name, {})
        impact = metadata.get('impact', 'UNKNOWN')

        if impact == 'HIGH':
            high_impact += 1
        elif impact == 'MEDIUM':
            medium_impact += 1
        elif impact == 'LOW':
            low_impact += 1
        elif impact == 'INFORMATIONAL':
            informational += 1

    return {
        'total_detectors_available': total_detectors,
        'detectors_fired': fired_detectors,
        'fire_rate': round(fired_detectors / total_detectors, 3) if total_detectors > 0 else 0.0,
        'high_impact_fired': high_impact,
        'medium_impact_fired': medium_impact,
        'low_impact_fired': low_impact,
        'informational_fired': informational,
    }
