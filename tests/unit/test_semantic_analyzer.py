"""
Unit Tests for SemanticAnalyzer (semantic_analyzer.py)

🎯 PRIORITY 1 TESTS:
Tests semantic security pattern detection (CEI, reentrancy guards).

🔍 KEY PATTERNS TESTED:
1. CEI (Checks-Effects-Interactions) violation detection
2. Reentrancy guard detection (nonReentrant modifier, mutex patterns)
3. State-call ordering analysis
4. Unchecked low-level calls in critical context

📊 COVERAGE TARGET: 75% (12 tests)

Test Categories:
1. CEI Violation Detection
2. CEI Safe Functions
3. CEI Score Calculation
4. Reentrancy Guard Detection
5. Unchecked Calls

Author: Ali - ChainGuardian AI Project
"""

import pytest
from unittest.mock import MagicMock

from chainguardian.feature_extraction.semantic_analyzer import (
    SemanticAnalyzer,
    extract_semantic_features
)


# ============================================================================
# HELPER: Create Mock Nodes
# ============================================================================

def create_mock_node(has_external_call=False, has_state_write=False, has_low_level_call=False):
    """
    Create a properly configured mock CFG node.

    Slither nodes have:
    - irs: List of IR operations (HighLevelCall, LowLevelCall, etc.)
    - state_variables_written: List of state vars modified
    """
    node = MagicMock()

    # Configure IR operations
    node.irs = []
    if has_external_call:
        mock_call = MagicMock()
        mock_call.__class__.__name__ = 'HighLevelCall'
        # Mock isinstance check
        from slither.slithir.operations import HighLevelCall
        mock_call.__class__ = HighLevelCall
        node.irs.append(mock_call)

    if has_low_level_call:
        mock_call = MagicMock()
        from slither.slithir.operations import LowLevelCall
        mock_call.__class__ = LowLevelCall
        mock_call.lvalue = None  # Return value not checked
        node.irs.append(mock_call)

    # Configure state variable writes
    if has_state_write:
        mock_var = MagicMock()
        mock_var.name = "balance"
        node.state_variables_written = [mock_var]
    else:
        node.state_variables_written = []

    return node


def create_mock_function(name, nodes, modifiers=None, is_view=False, is_pure=False, is_constructor=False):
    """Create a properly configured mock function."""
    func = MagicMock()
    func.name = name
    func.nodes = nodes
    func.modifiers = modifiers or []
    func.view = is_view
    func.pure = is_pure
    func.is_constructor = is_constructor
    return func


# ============================================================================
# TEST 1: CEI VIOLATION DETECTION (CRITICAL!)
# ============================================================================

def test_cei_violation_detection():
    """
    Test detection of CEI pattern violations.

    VIOLATION: External call → State modification
    This is the classic DAO hack vulnerability!

    Example:
    function withdraw() {
        msg.sender.call{value: balance}("");  // External call
        balance = 0;  // State change AFTER call = VIOLATION!
    }
    """
    # Create vulnerable function (call then state)
    vulnerable_func = create_mock_function(
        name="withdraw",
        nodes=[
            create_mock_node(has_external_call=True),   # External call first
            create_mock_node(has_state_write=True),     # State write AFTER = BAD!
        ]
    )

    # Create mock contract
    mock_contract = MagicMock()
    mock_contract.functions = [vulnerable_func]

    # Analyze
    analyzer = SemanticAnalyzer(mock_contract)
    violations = analyzer._count_cei_violations()

    # Should detect 1 violation
    assert violations == 1, "Should detect CEI violation (state after call)"


# ============================================================================
# TEST 2: CEI SAFE FUNCTION
# ============================================================================

def test_cei_safe_function():
    """
    Test detection of CEI-compliant functions.

    SAFE: State modification → External call

    Example:
    function withdraw() {
        balance = 0;  // State change FIRST
        msg.sender.call{value: balance}("");  // External call AFTER = SAFE!
    }
    """
    # Create safe function (state then call)
    safe_func = create_mock_function(
        name="safeWithdraw",
        nodes=[
            create_mock_node(has_state_write=True),     # State write FIRST = GOOD!
            create_mock_node(has_external_call=True),   # External call AFTER
        ]
    )

    mock_contract = MagicMock()
    mock_contract.functions = [safe_func]

    analyzer = SemanticAnalyzer(mock_contract)
    safe_count = analyzer._count_cei_safe_functions()

    # Should count as safe
    assert safe_count == 1, "Should recognize CEI-compliant function"


# ============================================================================
# TEST 3: CEI SCORE CALCULATION
# ============================================================================

def test_cei_score_perfect():
    """
    Test CEI score with all safe functions.

    Score = safe / (safe + violations)
    Perfect = 1.0
    """
    safe_func = create_mock_function(
        name="safe",
        nodes=[
            create_mock_node(has_state_write=True),
            create_mock_node(has_external_call=True),
        ]
    )

    mock_contract = MagicMock()
    mock_contract.functions = [safe_func]

    analyzer = SemanticAnalyzer(mock_contract)
    score = analyzer._calculate_cei_score()

    assert score == 1.0, "Perfect CEI compliance should score 1.0"


def test_cei_score_all_violations():
    """Test CEI score with all violations (score = 0.0)."""
    vulnerable_func = create_mock_function(
        name="vulnerable",
        nodes=[
            create_mock_node(has_external_call=True),
            create_mock_node(has_state_write=True),
        ]
    )

    mock_contract = MagicMock()
    mock_contract.functions = [vulnerable_func]

    analyzer = SemanticAnalyzer(mock_contract)
    score = analyzer._calculate_cei_score()

    assert score == 0.0, "All violations should score 0.0"


def test_cei_score_mixed():
    """Test CEI score with mixed safe/vulnerable functions."""
    safe_func = create_mock_function(
        name="safe",
        nodes=[
            create_mock_node(has_state_write=True),
            create_mock_node(has_external_call=True),
        ]
    )

    vulnerable_func = create_mock_function(
        name="vulnerable",
        nodes=[
            create_mock_node(has_external_call=True),
            create_mock_node(has_state_write=True),
        ]
    )

    mock_contract = MagicMock()
    mock_contract.functions = [safe_func, vulnerable_func]

    analyzer = SemanticAnalyzer(mock_contract)
    score = analyzer._calculate_cei_score()

    # 1 safe, 1 violation = 1 / 2 = 0.5
    assert score == 0.5, "50% safe should score 0.5"


# ============================================================================
# TEST 4: REENTRANCY GUARD DETECTION (nonReentrant modifier)
# ============================================================================

def test_reentrancy_guard_nonreentrant_modifier():
    """
    Test detection of OpenZeppelin's ReentrancyGuard pattern.

    Uses 'nonReentrant' modifier:
    modifier nonReentrant() { ... }
    """
    # Create mock modifier
    mock_modifier = MagicMock()
    mock_modifier.name = "nonReentrant"

    mock_contract = MagicMock()
    mock_contract.modifiers = [mock_modifier]
    mock_contract.state_variables = []

    analyzer = SemanticAnalyzer(mock_contract)
    has_guard = analyzer._detect_reentrancy_guard()

    assert has_guard is True, "Should detect nonReentrant modifier"


# ============================================================================
# TEST 5: REENTRANCY GUARD DETECTION (mutex pattern)
# ============================================================================

@pytest.mark.parametrize("var_name", [
    "lock",
    "mutex",
    "reentrancyGuard",
    "locked",
    "entered",
])
def test_reentrancy_guard_mutex_pattern(var_name):
    """
    Test detection of manual mutex patterns.

    Uses state variable with lock/mutex/guard in name:
    bool private locked;
    """
    mock_var = MagicMock()
    mock_var.name = var_name

    mock_contract = MagicMock()
    mock_contract.modifiers = []
    mock_contract.state_variables = [mock_var]

    analyzer = SemanticAnalyzer(mock_contract)
    has_guard = analyzer._detect_reentrancy_guard()

    assert has_guard is True, f"Should detect mutex pattern with var: {var_name}"


# ============================================================================
# TEST 6: NO REENTRANCY GUARD
# ============================================================================

def test_no_reentrancy_guard():
    """Test contract without any reentrancy protection."""
    mock_var = MagicMock()
    mock_var.name = "balance"  # Regular variable

    mock_contract = MagicMock()
    mock_contract.modifiers = []
    mock_contract.state_variables = [mock_var]

    analyzer = SemanticAnalyzer(mock_contract)
    has_guard = analyzer._detect_reentrancy_guard()

    assert has_guard is False, "Should not detect guard in unprotected contract"


# ============================================================================
# TEST 7: COUNT GUARDED FUNCTIONS
# ============================================================================

def test_count_guarded_functions():
    """
    Test counting functions with nonReentrant modifier.
    """
    # Create modifier
    guard_modifier = MagicMock()
    guard_modifier.name = "nonReentrant"

    # Create function with guard
    guarded_func = create_mock_function(
        name="withdraw",
        nodes=[],
        modifiers=[guard_modifier]
    )

    # Create function without guard
    unguarded_func = create_mock_function(
        name="deposit",
        nodes=[],
        modifiers=[]
    )

    mock_contract = MagicMock()
    mock_contract.modifiers = [guard_modifier]  # Contract has the modifier
    mock_contract.functions = [guarded_func, unguarded_func]

    analyzer = SemanticAnalyzer(mock_contract)
    count = analyzer._count_guarded_functions()

    assert count == 1, "Should count 1 guarded function"


# ============================================================================
# TEST 8: VIEW/PURE FUNCTIONS EXCLUDED
# ============================================================================

def test_view_functions_excluded_from_cei():
    """
    Test that view/pure functions are excluded from CEI analysis.

    WHY: View/pure can't modify state, so CEI violations impossible.
    """
    # Create view function with "violation" pattern
    view_func = create_mock_function(
        name="getBalance",
        nodes=[
            create_mock_node(has_external_call=True),
            create_mock_node(has_state_write=True),  # Would be violation in normal func
        ],
        is_view=True
    )

    mock_contract = MagicMock()
    mock_contract.functions = [view_func]

    analyzer = SemanticAnalyzer(mock_contract)
    violations = analyzer._count_cei_violations()

    assert violations == 0, "View functions should be excluded from CEI analysis"


# ============================================================================
# TEST 9: CONSTRUCTOR EXCLUDED
# ============================================================================

def test_constructor_excluded_from_cei():
    """Test that constructors are excluded from CEI analysis."""
    constructor = create_mock_function(
        name="constructor",
        nodes=[
            create_mock_node(has_external_call=True),
            create_mock_node(has_state_write=True),
        ],
        is_constructor=True
    )

    mock_contract = MagicMock()
    mock_contract.functions = [constructor]

    analyzer = SemanticAnalyzer(mock_contract)
    violations = analyzer._count_cei_violations()

    assert violations == 0, "Constructor should be excluded from CEI analysis"


# ============================================================================
# TEST 10: SAFE STATE MODIFICATIONS (before calls)
# ============================================================================

def test_count_safe_state_modifications():
    """
    Test counting state mods that occur BEFORE external calls.

    PATTERN: state_write → external_call (SAFE)
    """
    safe_func = create_mock_function(
        name="withdraw",
        nodes=[
            create_mock_node(has_state_write=True),     # State FIRST
            create_mock_node(has_external_call=True),   # Call AFTER
        ]
    )

    mock_contract = MagicMock()
    mock_contract.functions = [safe_func]

    analyzer = SemanticAnalyzer(mock_contract)
    safe_count = analyzer._count_safe_state_modifications()

    assert safe_count == 1, "Should count safe state modification"


# ============================================================================
# TEST 11: UNSAFE STATE MODIFICATIONS (after calls)
# ============================================================================

def test_count_unsafe_state_modifications():
    """
    Test counting state mods that occur AFTER external calls.

    PATTERN: external_call → state_write (UNSAFE)
    """
    unsafe_func = create_mock_function(
        name="withdraw",
        nodes=[
            create_mock_node(has_external_call=True),   # Call FIRST
            create_mock_node(has_state_write=True),     # State AFTER = UNSAFE!
        ]
    )

    mock_contract = MagicMock()
    mock_contract.functions = [unsafe_func]

    analyzer = SemanticAnalyzer(mock_contract)
    unsafe_count = analyzer._count_unsafe_state_modifications()

    assert unsafe_count == 1, "Should count unsafe state modification"


# ============================================================================
# TEST 12: EXTRACT_SEMANTIC_FEATURES FUNCTION
# ============================================================================

def test_extract_semantic_features_integration():
    """
    Test the convenience function extract_semantic_features().

    Should return dict with all 8 semantic features.
    """
    # Create simple safe contract
    safe_func = create_mock_function(
        name="safe",
        nodes=[
            create_mock_node(has_state_write=True),
            create_mock_node(has_external_call=True),
        ]
    )

    guard_modifier = MagicMock()
    guard_modifier.name = "nonReentrant"

    mock_contract = MagicMock()
    mock_contract.functions = [safe_func]
    mock_contract.modifiers = [guard_modifier]
    mock_contract.state_variables = []

    # Call convenience function
    features = extract_semantic_features(mock_contract)

    # Verify all expected keys present
    expected_keys = [
        'cei_violations',
        'cei_safe_functions',
        'cei_pattern_score',
        'has_reentrancy_guard',
        'functions_with_reentrancy_guard',
        'state_before_call_count',
        'state_after_call_count',
        'unchecked_calls_in_critical_context',
    ]

    for key in expected_keys:
        assert key in features, f"Missing key: {key}"

    # Verify values make sense
    assert features['cei_violations'] == 0
    assert features['cei_safe_functions'] == 1
    assert features['cei_pattern_score'] == 1.0
    assert features['has_reentrancy_guard'] is True


# ============================================================================
# TEST 13: EMPTY CONTRACT
# ============================================================================

def test_empty_contract():
    """Test contract with no functions."""
    mock_contract = MagicMock()
    mock_contract.functions = []
    mock_contract.modifiers = []
    mock_contract.state_variables = []

    analyzer = SemanticAnalyzer(mock_contract)
    features = analyzer.analyze()

    # Should return safe defaults
    assert features['cei_violations'] == 0
    assert features['cei_safe_functions'] == 0
    assert features['cei_pattern_score'] == 1.0  # No functions = safe by default
    assert features['has_reentrancy_guard'] is False
