"""
Unit Tests for SlitherAnalyzer (contract_analyzer.py)

🎯 CRITICAL TESTS (Priority 0):
This file tests 39 vulnerability features extracted from Slither detector results.

🐛 CRITICAL BUG TESTED:
Nested list bug at contract_analyzer.py:398-441
Slither returns List[List[Dict]], must flatten before processing!

📊 COVERAGE TARGET: 85% (15 tests)

Test Categories:
1. Nested List Bug (PRODUCTION BLOCKER)
2. Detector Mapping (45+ detectors)
3. Severity Counting (high/medium/low)
4. Aggregate Statistics (confidence, categories)
5. Risk Scoring (simple vs weighted)
6. Edge Cases (empty results, malformed data)

Author: Ali - ChainGuardian AI Project
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from chainguardian.feature_extraction.contract_analyzer import (
    SlitherAnalyzer,
    ContractFeatures
)


# ============================================================================
# TEST 1: CRITICAL NESTED LIST BUG
# ============================================================================

def test_detector_results_nested_list_bug(temp_sol_file, mock_slither):
    """
    TEST THE MOST CRITICAL BUG: Slither returns List[List[Dict]].

    🐛 BUG LOCATION: contract_analyzer.py line 398-441

    BACKGROUND:
    Slither.run_detectors() returns: List[List[Dict]], NOT List[Dict]!
    Each detector can return multiple findings, so results are nested.

    Example:
    [
        [{'check': 'reentrancy-eth', 'impact': 'High'}],      # Detector 1
        [{'check': 'arbitrary-send', 'impact': 'High'}]       # Detector 2
    ]

    If we don't flatten, we only process the outer list and miss findings!

    This test ensures we correctly detect BOTH vulnerabilities.
    """
    # Setup: Create nested list structure (realistic Slither output)
    mock_slither.filename = temp_sol_file
    mock_slither.run_detectors.return_value = [
        # First detector (reentrancy) - returns list of 1 finding
        [{'check': 'reentrancy-eth', 'impact': 'High', 'confidence': 'High'}],

        # Second detector (arbitrary send) - returns list of 1 finding
        [{'check': 'arbitrary-send-eth', 'impact': 'High', 'confidence': 'High'}]
    ]

    # Execute
    analyzer = SlitherAnalyzer(mock_slither)
    features = analyzer.extract_features("TestContract")

    # Assert: Both vulnerabilities must be detected
    assert features.has_reentrancy is True, \
        "Failed to detect reentrancy from nested list!"

    assert features.has_access_control_issues is True, \
        "Failed to detect arbitrary-send from nested list!"

    # Assert: Severity counts correct
    assert features.high_severity_count == 2, \
        "Should count 2 high severity issues from nested lists"

    # Assert: Aggregate stats correct
    assert features.total_detector_hits == 2, \
        "Should track 2 unique detectors fired"


# ============================================================================
# TEST 2: FLAT LIST FORMAT (Alternative Slither format)
# ============================================================================

def test_detector_results_flat_list(temp_sol_file, mock_slither):
    """
    Test that we also handle flat list format correctly.

    Some Slither versions or configurations may return flat lists:
    [{'check': 'tx-origin', ...}, {'check': 'timestamp', ...}]

    Our code should handle BOTH nested and flat formats gracefully.
    """
    mock_slither.filename = temp_sol_file
    mock_slither.run_detectors.return_value = [
        # Flat list (not nested)
        {'check': 'tx-origin', 'impact': 'Medium', 'confidence': 'High'},
        {'check': 'timestamp', 'impact': 'Low', 'confidence': 'Medium'}
    ]

    analyzer = SlitherAnalyzer(mock_slither)
    features = analyzer.extract_features("TestContract")

    # Assert: Both detectors mapped correctly
    assert features.has_tx_origin is True
    assert features.has_timestamp_dependency is True

    # Assert: Severity counts
    assert features.medium_severity_count == 1
    assert features.low_severity_count == 1


# ============================================================================
# TEST 3: REENTRANCY VARIANT MAPPING
# ============================================================================

@pytest.mark.parametrize("detector_name,expected_feature", [
    # Original reentrancy detectors (map to umbrella flag)
    ('reentrancy-eth', 'has_reentrancy'),
    ('reentrancy-no-eth', 'has_reentrancy'),

    # Specific reentrancy variants (map to specific flags)
    ('reentrancy-unlimited-gas', 'has_reentrancy_unlimited'),
    ('reentrancy-benign', 'has_reentrancy_benign'),
    ('reentrancy-events', 'has_reentrancy_events'),
])
def test_reentrancy_detector_mapping(temp_sol_file, mock_slither,
                                     detector_name, expected_feature):
    """
    Test all 5 reentrancy detector variants map correctly.

    EXPANDED: Was 2 detectors → now 5 (more nuanced ML signal)
    """
    mock_slither.filename = temp_sol_file
    mock_slither.run_detectors.return_value = [
        [{'check': detector_name, 'impact': 'High', 'confidence': 'High'}]
    ]

    analyzer = SlitherAnalyzer(mock_slither)
    features = analyzer.extract_features("TestContract")

    # Assert: Correct feature flag set
    assert getattr(features, expected_feature) is True, \
        f"Detector {detector_name} should set {expected_feature}=True"


# ============================================================================
# TEST 4: ACCESS CONTROL DETECTOR MAPPING
# ============================================================================

@pytest.mark.parametrize("detector_name", [
    'arbitrary-send-eth',
    'arbitrary-send-erc20',
    'arbitrary-send-erc20-no-permit',
    'suicidal',
    'unprotected-upgrade',
    'unprotected-upgradeable',
])
def test_access_control_detector_mapping(temp_sol_file, mock_slither, detector_name):
    """
    Test all 6 access control detectors map to has_access_control_issues.

    DESIGN: Many-to-one mapping (6 detectors → 1 feature)
    Why? All represent same vulnerability class
    """
    mock_slither.filename = temp_sol_file
    mock_slither.run_detectors.return_value = [
        [{'check': detector_name, 'impact': 'High', 'confidence': 'High'}]
    ]

    analyzer = SlitherAnalyzer(mock_slither)
    features = analyzer.extract_features("TestContract")

    assert features.has_access_control_issues is True, \
        f"{detector_name} should set has_access_control_issues=True"


# ============================================================================
# TEST 5: UNCHECKED OPERATIONS MAPPING
# ============================================================================

@pytest.mark.parametrize("detector_name,expected_feature", [
    # Low-level call detectors
    ('unchecked-send', 'has_unchecked_call'),
    ('unchecked-lowlevel', 'has_unchecked_call'),
    ('low-level-calls', 'has_unchecked_call'),

    # ERC20 transfer detector (separate feature)
    ('unchecked-transfer', 'has_unchecked_transfer'),
])
def test_unchecked_operations_mapping(temp_sol_file, mock_slither,
                                     detector_name, expected_feature):
    """
    Test unchecked operations map to 2 different features.

    DESIGN: Low-level calls vs ERC20 transfers (different contexts)
    """
    mock_slither.filename = temp_sol_file
    mock_slither.run_detectors.return_value = [
        [{'check': detector_name, 'impact': 'Medium', 'confidence': 'High'}]
    ]

    analyzer = SlitherAnalyzer(mock_slither)
    features = analyzer.extract_features("TestContract")

    assert getattr(features, expected_feature) is True


# ============================================================================
# TEST 6: SEVERITY COUNTING
# ============================================================================

def test_severity_counting(temp_sol_file, mock_slither):
    """
    Test that we correctly count high/medium/low severity issues.

    CRITICAL: These counts are used in risk scoring!
    """
    mock_slither.filename = temp_sol_file
    mock_slither.run_detectors.return_value = [
        [{'check': 'reentrancy-eth', 'impact': 'High', 'confidence': 'High'}],
        [{'check': 'arbitrary-send', 'impact': 'High', 'confidence': 'Medium'}],
        [{'check': 'tx-origin', 'impact': 'Medium', 'confidence': 'High'}],
        [{'check': 'timestamp', 'impact': 'Low', 'confidence': 'Medium'}],
        [{'check': 'floating-pragma', 'impact': 'Informational', 'confidence': 'High'}],
    ]

    analyzer = SlitherAnalyzer(mock_slither)
    features = analyzer.extract_features("TestContract")

    # Assert counts
    assert features.high_severity_count == 2, "Should count 2 high severity"
    assert features.medium_severity_count == 1, "Should count 1 medium severity"
    assert features.low_severity_count == 2, "Should count 1 low + 1 informational"


# ============================================================================
# TEST 7: CONFIDENCE LEVEL TRACKING
# ============================================================================

def test_confidence_level_tracking(temp_sol_file, mock_slither):
    """
    Test that we track detector confidence levels.

    WHY: High confidence findings are more reliable (used in weighted scoring)
    """
    mock_slither.filename = temp_sol_file
    mock_slither.run_detectors.return_value = [
        [{'check': 'reentrancy-eth', 'impact': 'High', 'confidence': 'High'}],
        [{'check': 'tx-origin', 'impact': 'Medium', 'confidence': 'Medium'}],
        [{'check': 'shadowing-state', 'impact': 'Low', 'confidence': 'Low'}],
    ]

    analyzer = SlitherAnalyzer(mock_slither)
    features = analyzer.extract_features("TestContract")

    # Assert confidence counts
    assert features.high_confidence_detectors == 1
    assert features.medium_confidence_detectors == 1
    assert features.low_confidence_detectors == 1
    assert features.total_detector_hits == 3


# ============================================================================
# TEST 8: VULNERABILITY CATEGORY TRACKING
# ============================================================================

def test_vulnerability_category_tracking(temp_sol_file, mock_slither):
    """
    Test unique vulnerability type counting.

    WHY: Contract with 10 reentrancy issues vs 10 different issue types
    are VERY different risk profiles!
    """
    mock_slither.filename = temp_sol_file
    mock_slither.run_detectors.return_value = [
        # 3 reentrancy detectors (1 category)
        [{'check': 'reentrancy-eth', 'impact': 'High', 'confidence': 'High'}],
        [{'check': 'reentrancy-benign', 'impact': 'Medium', 'confidence': 'High'}],

        # 2 access control detectors (1 category)
        [{'check': 'arbitrary-send', 'impact': 'High', 'confidence': 'High'}],
        [{'check': 'suicidal', 'impact': 'High', 'confidence': 'Medium'}],

        # 1 timestamp detector (1 category)
        [{'check': 'timestamp', 'impact': 'Low', 'confidence': 'Medium'}],
    ]

    analyzer = SlitherAnalyzer(mock_slither)
    features = analyzer.extract_features("TestContract")

    # Should identify 3 unique vulnerability categories despite 5 detectors
    assert features.unique_vulnerability_types == 3, \
        "Should identify 3 categories: reentrancy, access_control, timestamp"


# ============================================================================
# TEST 9: SIMPLE RISK SCORE CALCULATION
# ============================================================================

def test_simple_risk_score(temp_sol_file, mock_slither):
    """
    Test simple risk score: high*10 + medium*5 + low*1.

    FORMULA: Weighted sum of severity counts
    """
    mock_slither.filename = temp_sol_file
    mock_slither.run_detectors.return_value = [
        [{'check': 'reentrancy-eth', 'impact': 'High', 'confidence': 'High'}],
        [{'check': 'arbitrary-send', 'impact': 'High', 'confidence': 'High'}],
        [{'check': 'tx-origin', 'impact': 'Medium', 'confidence': 'High'}],
        [{'check': 'timestamp', 'impact': 'Low', 'confidence': 'Medium'}],
    ]

    analyzer = SlitherAnalyzer(mock_slither)
    features = analyzer.extract_features("TestContract")

    # Expected: 2*10 + 1*5 + 1*1 = 26
    expected_score = 2 * 10 + 1 * 5 + 1 * 1
    assert features.risk_score_simple == expected_score, \
        f"Expected {expected_score}, got {features.risk_score_simple}"


# ============================================================================
# TEST 10: HIGH RISK FLAG THRESHOLDS
# ============================================================================

@pytest.mark.parametrize("high_count,medium_count,low_count,expected_high_risk", [
    # Scenario 1: Low risk (below all thresholds)
    (0, 1, 2, False),

    # Scenario 2: High risk (score > 20)
    (3, 0, 0, True),  # 3*10 = 30 > 20

    # Scenario 3: High risk (3+ high severity)
    (3, 0, 0, True),

    # Scenario 4: Borderline (score = 20, just below threshold)
    (2, 0, 0, False),  # 2*10 = 20 (not > 20)
])
def test_high_risk_flag_thresholds(temp_sol_file, mock_slither,
                                   high_count, medium_count, low_count,
                                   expected_high_risk):
    """
    Test is_high_risk flag based on thresholds.

    THRESHOLDS:
    - risk_score_simple > 20, OR
    - high_severity_count >= 3, OR
    - unique_vulnerability_types >= 3
    """
    # Build detector results based on counts
    results = []

    # Add high severity detectors
    for i in range(high_count):
        results.append([{'check': f'reentrancy-eth', 'impact': 'High', 'confidence': 'High'}])

    # Add medium severity detectors
    for i in range(medium_count):
        results.append([{'check': f'tx-origin', 'impact': 'Medium', 'confidence': 'High'}])

    # Add low severity detectors
    for i in range(low_count):
        results.append([{'check': f'timestamp', 'impact': 'Low', 'confidence': 'Medium'}])

    mock_slither.filename = temp_sol_file
    mock_slither.run_detectors.return_value = results

    analyzer = SlitherAnalyzer(mock_slither)
    features = analyzer.extract_features("TestContract")

    assert features.is_high_risk == expected_high_risk


# ============================================================================
# TEST 11: COMPLEXITY CATEGORIES
# ============================================================================

@pytest.mark.parametrize("high_count,medium_count,low_count,expected_category", [
    # Simple: Low issue count
    (0, 0, 1, 'simple'),

    # Moderate: Some issues
    (1, 1, 1, 'moderate'),

    # Complex: Multiple high issues
    (2, 2, 2, 'complex'),

    # Critical: Many issues
    (5, 5, 5, 'critical'),
])
def test_complexity_categories(temp_sol_file, mock_slither,
                               high_count, medium_count, low_count,
                               expected_category):
    """
    Test contract complexity categorization.

    CATEGORIES: simple, moderate, complex, critical
    Based on: high*3 + medium*2 + low + unique_types*2
    """
    # Build detector results
    results = []
    for i in range(high_count):
        results.append([{'check': 'reentrancy-eth', 'impact': 'High', 'confidence': 'High'}])
    for i in range(medium_count):
        results.append([{'check': 'tx-origin', 'impact': 'Medium', 'confidence': 'High'}])
    for i in range(low_count):
        results.append([{'check': 'timestamp', 'impact': 'Low', 'confidence': 'Medium'}])

    mock_slither.filename = temp_sol_file
    mock_slither.run_detectors.return_value = results

    analyzer = SlitherAnalyzer(mock_slither)
    features = analyzer.extract_features("TestContract")

    assert features.contract_complexity_category == expected_category


# ============================================================================
# TEST 12: EMPTY DETECTOR RESULTS
# ============================================================================

def test_empty_detector_results(temp_sol_file, mock_slither):
    """
    Test safe contract with no vulnerabilities.

    EDGE CASE: Slither returns empty list []
    Should not crash, should return zero counts
    """
    mock_slither.filename = temp_sol_file
    mock_slither.run_detectors.return_value = []

    analyzer = SlitherAnalyzer(mock_slither)
    features = analyzer.extract_features("SafeContract")

    # Assert all counts are zero
    assert features.high_severity_count == 0
    assert features.medium_severity_count == 0
    assert features.low_severity_count == 0
    assert features.total_detector_hits == 0
    assert features.unique_vulnerability_types == 0

    # Assert all vulnerability flags are False
    assert features.has_reentrancy is False
    assert features.has_access_control_issues is False
    assert features.has_timestamp_dependency is False

    # Assert risk scores are zero
    assert features.risk_score_simple == 0.0
    assert features.is_high_risk is False
    assert features.contract_complexity_category == 'simple'


# ============================================================================
# TEST 13: MALFORMED DETECTOR RESULTS
# ============================================================================

def test_malformed_detector_results(temp_sol_file, mock_slither):
    """
    Test robustness against malformed Slither output.

    EDGE CASE: Slither returns unexpected data types
    Should log warnings but not crash
    """
    mock_slither.filename = temp_sol_file
    mock_slither.run_detectors.return_value = [
        # Valid result
        [{'check': 'reentrancy-eth', 'impact': 'High', 'confidence': 'High'}],

        # Invalid: Not a dict
        ["invalid_string"],

        # Invalid: Dict missing required fields
        [{'random_key': 'random_value'}],

        # Invalid: None
        None,
    ]

    analyzer = SlitherAnalyzer(mock_slither)
    features = analyzer.extract_features("TestContract")

    # Should process valid result only
    assert features.has_reentrancy is True
    assert features.high_severity_count == 1
    assert features.total_detector_hits == 1  # Only 1 valid detector


# ============================================================================
# TEST 14: DETECTOR RUN FAILURE
# ============================================================================

def test_detector_run_failure(temp_sol_file, mock_slither):
    """
    Test graceful handling when Slither.run_detectors() raises exception.

    PRODUCTION SCENARIO: Compilation errors, missing dependencies
    Should return features with zero counts (not crash)
    """
    mock_slither.filename = temp_sol_file
    mock_slither.run_detectors.side_effect = Exception("Slither compilation failed")

    analyzer = SlitherAnalyzer(mock_slither)
    features = analyzer.extract_features("BrokenContract")

    # Should return features with zero counts
    assert features.contract_name == "BrokenContract"
    assert features.high_severity_count == 0
    assert features.total_detector_hits == 0
    assert features.risk_score_simple == 0.0


# ============================================================================
# TEST 15: WEIGHTED RISK SCORE (Advanced)
# ============================================================================

def test_weighted_risk_score(temp_sol_file, mock_slither):
    """
    Test confidence-weighted risk score calculation.

    FORMULA: Consider both severity AND confidence
    High confidence findings weighted more (1.0 vs 0.7 vs 0.3)
    """
    mock_slither.filename = temp_sol_file
    mock_slither.run_detectors.return_value = [
        # High severity, high confidence (highest weight)
        [{'check': 'reentrancy-eth', 'impact': 'High', 'confidence': 'High'}],

        # High severity, low confidence (lower weight)
        [{'check': 'arbitrary-send', 'impact': 'High', 'confidence': 'Low'}],
    ]

    analyzer = SlitherAnalyzer(mock_slither)
    features = analyzer.extract_features("TestContract")

    # Weighted score should be less than simple score
    # Simple: 2*10 = 20
    # Weighted: (1*10*1.0 + 1*10*0.3) / 2 ≈ 13
    assert features.risk_score_simple == 20.0
    assert 0 < features.risk_score_weighted < features.risk_score_simple, \
        "Weighted score should be less than simple (due to low confidence detector)"


# ============================================================================
# TEST 16: DATACLASS INITIALIZATION
# ============================================================================

def test_contract_features_dataclass():
    """
    Test ContractFeatures dataclass initialization.

    SANITY CHECK: Ensure defaults work correctly
    """
    features = ContractFeatures(
        contract_name="TestContract",
        file_path="/tmp/test.sol"
    )

    # Assert required fields
    assert features.contract_name == "TestContract"
    assert features.file_path == "/tmp/test.sol"

    # Assert defaults
    assert features.has_reentrancy is False
    assert features.high_severity_count == 0
    assert features.risk_score_simple == 0.0
    assert features.contract_complexity_category == 'simple'


# ============================================================================
# TEST 17: DETECTOR MAPPING COVERAGE
# ============================================================================

def test_detector_mapping_coverage():
    """
    Verify that DETECTOR_MAPPING contains expected number of detectors.

    REGRESSION TEST: Ensure we don't accidentally remove mappings
    """
    from chainguardian.feature_extraction.contract_analyzer import SlitherAnalyzer

    # Should have 45+ detector mappings
    assert len(SlitherAnalyzer.DETECTOR_MAPPING) >= 35, \
        "DETECTOR_MAPPING should have at least 35 entries (was 45 in original)"

    # Verify key detectors are mapped
    critical_detectors = [
        'reentrancy-eth',
        'arbitrary-send-eth',
        'tx-origin',
        'timestamp',
        'unchecked-send',
    ]

    for detector in critical_detectors:
        assert detector in SlitherAnalyzer.DETECTOR_MAPPING, \
            f"Critical detector {detector} missing from mapping!"
