"""
Shared test fixtures for ChainGuardian AI test suite.

This file provides reusable fixtures for all tests, following the DRY principle.
Fixtures are automatically discovered by pytest and can be used across all test files.
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock
from typing import Generator
import sys


# ============================================================================
# TEMP FILE FIXTURES
# ============================================================================

@pytest.fixture
def temp_sol_file() -> Generator[Path, None, None]:
    """
    Create a temporary .sol file with basic safe contract.

    🎓 Why tempfile? Real files ensure proper file handling
    Don't use fake paths - they don't test actual file I/O

    Cleanup is automatic via try/except in finally block.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sol', delete=False) as f:
        f.write("""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SimpleToken {
    uint256 public totalSupply;
    mapping(address => uint256) public balances;

    function transfer(address to, uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        balances[to] += amount;
    }
}
""")
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    try:
        temp_path.unlink()
    except:
        pass  # Already deleted, no problem


@pytest.fixture
def vulnerable_contract_file() -> Generator[Path, None, None]:
    """
    Temp file with reentrancy vulnerability (CEI violation).

    🎓 Bad pattern: External call BEFORE state change
    This is the classic DAO hack vulnerability.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sol', delete=False) as f:
        f.write("""
pragma solidity ^0.8.0;

contract VulnerableBank {
    mapping(address => uint) public balances;

    function withdraw() public {
        uint amount = balances[msg.sender];

        // VULNERABILITY: External call BEFORE state change
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");

        // State change happens AFTER external call (CEI violation)
        balances[msg.sender] = 0;
    }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }
}
""")
        temp_path = Path(f.name)

    yield temp_path

    try:
        temp_path.unlink()
    except:
        pass


@pytest.fixture
def empty_contract_file() -> Generator[Path, None, None]:
    """Temp file with empty contract (edge case testing)."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sol', delete=False) as f:
        f.write("""
pragma solidity ^0.8.0;

contract EmptyContract {
    // No functions, no state variables
}
""")
        temp_path = Path(f.name)

    yield temp_path

    try:
        temp_path.unlink()
    except:
        pass


# ============================================================================
# MOCK SLITHER FIXTURES
# ============================================================================

@pytest.fixture
def mock_slither():
    """
    Create a basic mock Slither object.

    🎓 Why mock Slither? Real Slither takes 2-5 seconds per contract.
    Tests should run in milliseconds, not minutes.
    """
    slither = MagicMock()
    slither.contracts = []
    slither.detector_results = []
    return slither


@pytest.fixture
def mock_contract():
    """
    Create a basic mock Slither contract.

    Mimics the structure of slither.core.declarations.Contract
    """
    contract = MagicMock()
    contract.name = "TestContract"
    contract.functions_declared = []
    contract.state_variables_declared = []
    contract.state_variables = []
    contract.modifiers_declared = []
    contract.modifiers = []
    contract.inheritance = []
    contract.is_interface = False
    contract.is_library = False
    contract.functions = []
    return contract


@pytest.fixture
def mock_function():
    """
    Create a basic mock Slither function.

    Mimics slither.core.declarations.Function
    """
    func = MagicMock()
    func.name = "testFunction"
    func.nodes = []
    func.external_calls_as_expressions = []
    func.low_level_calls = []
    func.high_level_calls = []
    func.internal_calls = []
    func.payable = False
    func.is_constructor = False
    func.view = False
    func.pure = False
    func.visibility = "public"
    func.state_variables_read = []
    func.state_variables_written = []
    return func


def create_mock_node(node_type: str = "EXPRESSION", has_external_call: bool = False):
    """
    Helper to create mock CFG nodes.

    Args:
        node_type: Type of node (EXPRESSION, IF, LOOP, etc.)
        has_external_call: Whether node contains external call

    Returns:
        Mock node object
    """
    node = MagicMock()
    node.type = node_type
    node.sons = []  # Child nodes in CFG
    node.fathers = []  # Parent nodes in CFG

    if has_external_call:
        node.high_level_calls = [MagicMock()]
        node.external_calls_as_expressions = [MagicMock()]
    else:
        node.high_level_calls = []
        node.external_calls_as_expressions = []

    node.state_variables_written = []
    node.state_variables_read = []

    return node


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture
def mock_db_manager():
    """
    Mock DatabaseManager for testing without real DB.

    🎓 Unit tests should NOT require database setup.
    Use this mock for testing business logic.
    Use real DB only in integration tests.
    """
    db = MagicMock()
    db.save_contract_and_features.return_value = 123  # Mock contract_id
    db.get_contract_count.return_value = 0
    db.get_stats.return_value = {
        'total_contracts': 0,
        'successful_extractions': 0,
        'failed_extractions': 0
    }
    return db


# ============================================================================
# FEATURE DICT FIXTURES
# ============================================================================

@pytest.fixture
def minimal_features() -> dict:
    """
    Minimal feature dict (all zeros) for edge case testing.

    Represents an empty contract or failed feature extraction.
    """
    return {
        'contract_name': 'EmptyContract',
        'file_path': '/tmp/empty.sol',
        'num_functions': 0,
        'num_external_calls': 0,
        'max_cyclomatic_complexity': 0,
        'lines_of_code': 0,
        'has_reentrancy': False,
        'cei_violations': 0,
        'cei_pattern_score': 1.0,
        'risk_score_simple': 0.0,
        'risk_score_weighted': 0.0,
    }


@pytest.fixture
def realistic_features() -> dict:
    """
    Realistic feature dict for a medium-complexity safe contract.

    Based on actual ERC20 token contracts.
    """
    return {
        'contract_name': 'SafeToken',
        'file_path': '/tmp/safe_token.sol',
        'num_functions': 12,
        'num_external_calls': 5,
        'max_cyclomatic_complexity': 8,
        'lines_of_code': 250,
        'has_reentrancy': False,
        'cei_violations': 0,
        'cei_pattern_score': 1.0,
        'cei_safe_functions': 5,
        'has_reentrancy_guard': False,
        'num_state_vars': 4,
        'num_modifiers': 2,
        'high_severity_count': 0,
        'medium_severity_count': 1,
        'low_severity_count': 3,
        'risk_score_simple': 0.1,
        'risk_score_weighted': 0.15,
    }


@pytest.fixture
def vulnerable_features() -> dict:
    """
    Feature dict for a contract with reentrancy vulnerability.

    Based on known vulnerable contracts (DAO hack pattern).
    """
    return {
        'contract_name': 'VulnerableBank',
        'file_path': '/tmp/vulnerable.sol',
        'num_functions': 3,
        'num_external_calls': 1,
        'max_cyclomatic_complexity': 3,
        'lines_of_code': 45,
        'has_reentrancy': True,
        'cei_violations': 1,  # State change after call
        'cei_pattern_score': 0.5,
        'cei_safe_functions': 2,
        'has_reentrancy_guard': False,
        'state_after_call_count': 1,
        'unchecked_calls_in_critical_context': 1,
        'high_severity_count': 1,
        'medium_severity_count': 0,
        'low_severity_count': 0,
        'risk_score_simple': 0.8,
        'risk_score_weighted': 0.85,
    }


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (require DB)"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


# ============================================================================
# HELPER FUNCTIONS (not fixtures, but useful across tests)
# ============================================================================

def create_mock_slither_with_contract(contract_name: str = "TestContract"):
    """
    Create a fully-configured mock Slither with one contract.

    Args:
        contract_name: Name for the mock contract

    Returns:
        tuple: (mock_slither, mock_contract)
    """
    slither = MagicMock()
    contract = MagicMock()
    contract.name = contract_name
    contract.functions_declared = []
    contract.state_variables_declared = []
    contract.modifiers_declared = []
    contract.is_interface = False
    contract.is_library = False

    slither.contracts = [contract]
    slither.detector_results = []

    return slither, contract


def create_mock_detector_result(check_name: str, impact: str = "High", confidence: str = "High"):
    """
    Create a mock Slither detector result.

    🎓 Slither returns List[List[Dict]], this helper creates one Dict

    Args:
        check_name: Detector name (e.g., 'reentrancy-eth')
        impact: Severity (High/Medium/Low)
        confidence: Confidence level

    Returns:
        Dict representing one detector finding
    """
    return {
        'check': check_name,
        'impact': impact,
        'confidence': confidence,
        'description': f'{check_name} vulnerability detected'
    }
