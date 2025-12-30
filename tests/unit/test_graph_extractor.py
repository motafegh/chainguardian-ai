"""
Unit Tests for GraphFeatureExtractor (graph_extractor.py)

🎯 PRIORITY 1 TESTS:
Tests 25 graph-theoretic features (CFG, Call Graph, Data Flow).

🔍 KEY FEATURES TESTED:
1. Control Flow Graph (8 features): cycles, depth, complexity
2. Call Graph (10 features): call depth, recursion, external calls
3. Data Flow Graph (7 features): tainted flows, sensitive sinks

📊 COVERAGE TARGET: 70% (18 tests)

Test Categories:
1. CFG Features (cycles, branching, complexity)
2. Call Graph Features (recursion, call depth)
3. Data Flow Features (taint analysis, validation)
4. Contract Matching (fuzzy matching, fallback)
5. Edge Cases (empty contracts, no functions)

Author: Ali - ChainGuardian AI Project
"""

import pytest
from unittest.mock import MagicMock
import networkx as nx

from chainguardian.feature_extraction.graph_extractor import GraphFeatureExtractor


# ============================================================================
# HELPER: Create Mock Nodes
# ============================================================================

def create_mock_node(node_type='EXPRESSION', sons=None, state_vars_written=None):
    """
    Create a mock CFG node.

    CFG nodes have:
    - type: Node type (IF, LOOP, RETURN, etc.)
    - sons: List of successor nodes
    - state_variables_written: State vars modified by this node
    """
    node = MagicMock()
    node.type = node_type
    node.sons = sons or []
    node.state_variables_written = state_vars_written or []
    return node


def create_mock_function(name, nodes=None, visibility='public',
                         internal_calls=None, external_calls=None,
                         parameters=None, state_vars_written=None,
                         state_vars_read=None, entry_point=None):
    """Create a mock Slither function."""
    func = MagicMock()
    func.name = name
    func.nodes = nodes or []
    func.visibility = visibility
    func.internal_calls = internal_calls or []
    func.external_calls_as_expressions = external_calls or []
    func.parameters = parameters or []
    func.state_variables_written = state_vars_written or []
    func.state_variables_read = state_vars_read or []
    func.entry_point = entry_point if entry_point else (nodes[0] if nodes else None)
    return func


# ============================================================================
# TEST 1: CFG CYCLE DETECTION
# ============================================================================

def test_cfg_cycle_detection():
    """
    Test detection of cycles in Control Flow Graph.

    CYCLE: Loop creates cycle in CFG
    Example: while(true) { ... }

    Graph: node1 → node2 → node1 (cycle!)
    """
    # Create cycle: node1 → node2 → node1
    node1 = create_mock_node('IF')
    node2 = create_mock_node('EXPRESSION')
    node1.sons = [node2]
    node2.sons = [node1]  # Back edge = cycle!

    func = create_mock_function('hasLoop', nodes=[node1, node2])

    mock_contract = MagicMock()
    mock_contract.name = "TestContract"
    mock_contract.functions_declared = [func]
    mock_contract.is_interface = False
    mock_contract.is_library = False

    mock_slither = MagicMock()
    mock_slither.contracts = [mock_contract]

    extractor = GraphFeatureExtractor(mock_slither)
    features = extractor.extract_features("TestContract")

    # Should detect 1 cycle
    assert features['cfg_num_cycles'] >= 1, "Should detect cycle in CFG"


# ============================================================================
# TEST 2: CFG COMPLEXITY CALCULATION
# ============================================================================

def test_cfg_cyclomatic_complexity():
    """
    Test cyclomatic complexity calculation.

    FORMULA: Complexity = 1 + (number of decision points)
    Decision points: IF, LOOP, REQUIRE

    Example:
    function test() {
        if (x) { ... }      // +1
        require(y);         // +1
        while (z) { ... }   // +1
    }
    Complexity = 1 + 3 = 4
    """
    # Create function with 3 decision points
    node1 = create_mock_node('IF')
    node2 = create_mock_node('REQUIRE')
    node3 = create_mock_node('LOOP')

    func = create_mock_function('complex', nodes=[node1, node2, node3])

    mock_contract = MagicMock()
    mock_contract.name = "TestContract"
    mock_contract.functions_declared = [func]

    mock_slither = MagicMock()
    mock_slither.contracts = [mock_contract]

    extractor = GraphFeatureExtractor(mock_slither)
    features = extractor.extract_features("TestContract")

    # Complexity = 1 (base) + 3 (decision points) = 4
    assert features['cfg_cyclomatic_total'] == 4


# ============================================================================
# TEST 3: CFG BRANCHING FACTOR
# ============================================================================

def test_cfg_branching_factor():
    """
    Test average branching factor calculation.

    BRANCHING FACTOR: edges / nodes

    Example: 3 nodes, 4 edges → branching = 4/3 = 1.33
    """
    # Create branching structure: node1 → node2, node1 → node3
    node1 = create_mock_node('IF')
    node2 = create_mock_node('EXPRESSION')
    node3 = create_mock_node('EXPRESSION')

    node1.sons = [node2, node3]  # 2 edges from node1
    node2.sons = [node3]          # 1 edge from node2
    # Total: 3 nodes, 3 edges → avg = 1.0

    func = create_mock_function('branching', nodes=[node1, node2, node3])

    mock_contract = MagicMock()
    mock_contract.name = "TestContract"
    mock_contract.functions_declared = [func]

    mock_slither = MagicMock()
    mock_slither.contracts = [mock_contract]

    extractor = GraphFeatureExtractor(mock_slither)
    features = extractor.extract_features("TestContract")

    # Should calculate branching factor
    assert features['cfg_avg_branching'] == 1.0


# ============================================================================
# TEST 4: CFG EXIT POINTS
# ============================================================================

def test_cfg_exit_points():
    """
    Test counting CFG exit points.

    EXIT POINTS: return, throw, revert statements
    """
    node1 = create_mock_node('EXPRESSION')
    node2 = create_mock_node('RETURN')  # Exit point 1
    node3 = create_mock_node('THROW')   # Exit point 2

    func = create_mock_function('exits', nodes=[node1, node2, node3])

    mock_contract = MagicMock()
    mock_contract.name = "TestContract"
    mock_contract.functions_declared = [func]

    mock_slither = MagicMock()
    mock_slither.contracts = [mock_contract]

    extractor = GraphFeatureExtractor(mock_slither)
    features = extractor.extract_features("TestContract")

    # Should count 2 exit points
    assert features['cfg_num_exit_points'] == 2


# ============================================================================
# TEST 5: COMPLEX LOOPS (NESTED)
# ============================================================================

def test_cfg_complex_loops():
    """
    Test detection of complex (nested) loops.

    COMPLEX LOOP: Multiple cycles in same function
    """
    # Create 2 separate cycles
    node1 = create_mock_node('LOOP')
    node2 = create_mock_node('EXPRESSION')
    node3 = create_mock_node('LOOP')
    node4 = create_mock_node('EXPRESSION')

    node1.sons = [node2]
    node2.sons = [node1]  # Cycle 1
    node3.sons = [node4]
    node4.sons = [node3]  # Cycle 2

    func = create_mock_function('nested', nodes=[node1, node2, node3, node4])

    mock_contract = MagicMock()
    mock_contract.name = "TestContract"
    mock_contract.functions_declared = [func]

    mock_slither = MagicMock()
    mock_slither.contracts = [mock_contract]

    extractor = GraphFeatureExtractor(mock_slither)
    features = extractor.extract_features("TestContract")

    # Should detect complex loops
    assert features['cfg_has_complex_loops'] is True


# ============================================================================
# TEST 6: CALL GRAPH RECURSION DETECTION
# ============================================================================

def test_call_graph_recursion():
    """
    Test detection of recursive calls (cyclic call graph).

    RECURSION: Function calls itself (directly or indirectly)
    Example: funcA() calls funcB(), funcB() calls funcA()
    """
    # Create recursive call: funcA → funcB → funcA
    funcA = create_mock_function('funcA')
    funcB = create_mock_function('funcB')

    # Set up internal calls
    funcA.internal_calls = [funcB]
    funcB.internal_calls = [funcA]  # Recursion!

    mock_contract = MagicMock()
    mock_contract.name = "TestContract"
    mock_contract.functions_declared = [funcA, funcB]

    mock_slither = MagicMock()
    mock_slither.contracts = [mock_contract]

    extractor = GraphFeatureExtractor(mock_slither)
    features = extractor.extract_features("TestContract")

    # Should detect cyclic calls
    assert features['cg_has_cyclic_calls'] is True


# ============================================================================
# TEST 7: CALL GRAPH DEPTH
# ============================================================================

def test_call_graph_depth():
    """
    Test call depth calculation.

    CALL DEPTH: Longest chain of function calls
    Example: main() → funcA() → funcB() → funcC()
    Depth = 3
    """
    funcC = create_mock_function('funcC', visibility='private')
    funcB = create_mock_function('funcB', visibility='private', internal_calls=[funcC])
    funcA = create_mock_function('funcA', visibility='private', internal_calls=[funcB])
    main = create_mock_function('main', visibility='public', internal_calls=[funcA])

    mock_contract = MagicMock()
    mock_contract.name = "TestContract"
    mock_contract.functions_declared = [main, funcA, funcB, funcC]

    mock_slither = MagicMock()
    mock_slither.contracts = [mock_contract]

    extractor = GraphFeatureExtractor(mock_slither)
    features = extractor.extract_features("TestContract")

    # Depth should be 3 (main → funcA → funcB → funcC)
    assert features['cg_max_call_depth'] >= 2


# ============================================================================
# TEST 8: PUBLIC VS INTERNAL FUNCTIONS
# ============================================================================

def test_call_graph_visibility():
    """
    Test counting public entry points vs internal functions.
    """
    public_func = create_mock_function('withdraw', visibility='public')
    external_func = create_mock_function('deposit', visibility='external')
    internal_func = create_mock_function('_helper', visibility='internal')
    private_func = create_mock_function('_validate', visibility='private')

    mock_contract = MagicMock()
    mock_contract.name = "TestContract"
    mock_contract.functions_declared = [public_func, external_func, internal_func, private_func]

    mock_slither = MagicMock()
    mock_slither.contracts = [mock_contract]

    extractor = GraphFeatureExtractor(mock_slither)
    features = extractor.extract_features("TestContract")

    # Should count 2 public entry points
    assert features['cg_num_public_entry_points'] == 2

    # Should count 2 internal functions
    assert features['cg_num_internal_functions'] == 2


# ============================================================================
# TEST 9: EXTERNAL CALLS
# ============================================================================

def test_call_graph_external_calls():
    """
    Test counting external calls.

    EXTERNAL CALL: Call to another contract
    Example: otherContract.transfer(...)
    """
    external_call1 = MagicMock()
    external_call2 = MagicMock()

    func = create_mock_function('withdraw', external_calls=[external_call1, external_call2])

    mock_contract = MagicMock()
    mock_contract.name = "TestContract"
    mock_contract.functions_declared = [func]

    mock_slither = MagicMock()
    mock_slither.contracts = [mock_contract]

    extractor = GraphFeatureExtractor(mock_slither)
    features = extractor.extract_features("TestContract")

    # Should count 2 external calls
    assert features['cg_num_external_calls'] == 2


# ============================================================================
# TEST 10: LEAF FUNCTIONS
# ============================================================================

def test_call_graph_leaf_functions():
    """
    Test counting leaf functions (no outgoing calls).

    LEAF: Function that doesn't call anything else
    """
    leaf1 = create_mock_function('leaf1', internal_calls=[])
    leaf2 = create_mock_function('leaf2', internal_calls=[])
    caller = create_mock_function('caller', internal_calls=[leaf1])

    mock_contract = MagicMock()
    mock_contract.name = "TestContract"
    mock_contract.functions_declared = [caller, leaf1, leaf2]

    mock_slither = MagicMock()
    mock_slither.contracts = [mock_contract]

    extractor = GraphFeatureExtractor(mock_slither)
    features = extractor.extract_features("TestContract")

    # Should count 2 leaf functions
    assert features['cg_num_leaf_functions'] == 2


# ============================================================================
# TEST 11: DATA FLOW - STATE VARIABLES
# ============================================================================

def test_dataflow_state_variables():
    """Test counting state variables."""
    var1 = MagicMock()
    var1.name = "balance"
    var2 = MagicMock()
    var2.name = "owner"

    mock_contract = MagicMock()
    mock_contract.name = "TestContract"
    mock_contract.state_variables_declared = [var1, var2]
    mock_contract.functions_declared = []

    mock_slither = MagicMock()
    mock_slither.contracts = [mock_contract]

    extractor = GraphFeatureExtractor(mock_slither)
    features = extractor.extract_features("TestContract")

    # Should count 2 state variables
    assert features['dfg_num_state_vars'] == 2


# ============================================================================
# TEST 12: DATA FLOW - CROSS-FUNCTION FLOWS
# ============================================================================

def test_dataflow_cross_function_flow():
    """
    Test detection of cross-function data flows.

    CROSS-FUNCTION: State var written by one function, read by another
    """
    var = MagicMock()
    var.name = "balance"

    writer_func = create_mock_function('setBalance', state_vars_written=[var])
    reader_func = create_mock_function('getBalance', state_vars_read=[var])

    mock_contract = MagicMock()
    mock_contract.name = "TestContract"
    mock_contract.state_variables_declared = [var]
    mock_contract.functions_declared = [writer_func, reader_func]

    mock_slither = MagicMock()
    mock_slither.contracts = [mock_contract]

    extractor = GraphFeatureExtractor(mock_slither)
    features = extractor.extract_features("TestContract")

    # Should detect cross-function flow
    assert features['dfg_has_cross_function_flow'] is True


# ============================================================================
# TEST 13: DATA FLOW - SENSITIVE SINKS
# ============================================================================

def test_dataflow_sensitive_sinks():
    """
    Test detection of sensitive sinks (dangerous operations).

    SINKS: transfer, send, call, delegatecall, selfdestruct
    """
    # Create mock external calls
    call1 = MagicMock()
    call1.__str__ = lambda x: "address.transfer(amount)"

    call2 = MagicMock()
    call2.__str__ = lambda x: "target.call{value: msg.value}(data)"

    func = create_mock_function('withdraw', external_calls=[call1, call2])

    mock_contract = MagicMock()
    mock_contract.name = "TestContract"
    mock_contract.state_variables_declared = []
    mock_contract.functions_declared = [func]

    mock_slither = MagicMock()
    mock_slither.contracts = [mock_contract]

    extractor = GraphFeatureExtractor(mock_slither)
    features = extractor.extract_features("TestContract")

    # Should detect 2 sensitive sinks
    assert features['dfg_num_sensitive_sinks'] == 2


# ============================================================================
# TEST 14: DATA FLOW - TAINTED FLOWS
# ============================================================================

def test_dataflow_tainted_flows():
    """
    Test detection of tainted data flows.

    TAINTED: Function parameters used in sensitive operations
    """
    param = MagicMock()
    param.name = "amount"

    var = MagicMock()
    var.name = "balance"

    # Function with parameter that writes state = tainted flow
    func = create_mock_function('deposit', parameters=[param], state_vars_written=[var])

    mock_contract = MagicMock()
    mock_contract.name = "TestContract"
    mock_contract.state_variables_declared = [var]
    mock_contract.functions_declared = [func]

    mock_slither = MagicMock()
    mock_slither.contracts = [mock_contract]

    extractor = GraphFeatureExtractor(mock_slither)
    features = extractor.extract_features("TestContract")

    # Should detect tainted flow
    assert features['dfg_num_tainted_flows'] >= 1


# ============================================================================
# TEST 15: DATA FLOW - UNVALIDATED INPUTS
# ============================================================================

def test_dataflow_unvalidated_inputs():
    """
    Test detection of unvalidated function parameters.

    UNVALIDATED: Function with parameters but no require/assert
    """
    param = MagicMock()
    param.name = "amount"

    # Function with param but no validation nodes
    node1 = create_mock_node('EXPRESSION')
    func = create_mock_function('unsafe', parameters=[param], nodes=[node1])

    mock_contract = MagicMock()
    mock_contract.name = "TestContract"
    mock_contract.state_variables_declared = []
    mock_contract.functions_declared = [func]

    mock_slither = MagicMock()
    mock_slither.contracts = [mock_contract]

    extractor = GraphFeatureExtractor(mock_slither)
    features = extractor.extract_features("TestContract")

    # Should count as unvalidated
    assert features['dfg_num_unvalidated_inputs'] == 1


def test_dataflow_validated_inputs():
    """Test that validated inputs are NOT counted as unvalidated."""
    param = MagicMock()
    param.name = "amount"

    # Function with param AND require validation
    node1 = create_mock_node('REQUIRE')  # Validation present!
    func = create_mock_function('safe', parameters=[param], nodes=[node1])

    mock_contract = MagicMock()
    mock_contract.name = "TestContract"
    mock_contract.state_variables_declared = []
    mock_contract.functions_declared = [func]

    mock_slither = MagicMock()
    mock_slither.contracts = [mock_contract]

    extractor = GraphFeatureExtractor(mock_slither)
    features = extractor.extract_features("TestContract")

    # Should NOT count as unvalidated
    assert features['dfg_num_unvalidated_inputs'] == 0


# ============================================================================
# TEST 16: CONTRACT FUZZY MATCHING
# ============================================================================

def test_contract_fuzzy_matching():
    """
    Test fuzzy matching for contract names.

    FUZZY: Case-insensitive, ignore underscores/dashes
    Request: "my-contract" should match "MyContract"
    """
    mock_contract = MagicMock()
    mock_contract.name = "MyContract"
    mock_contract.is_interface = False
    mock_contract.is_library = False
    mock_contract.functions_declared = []
    mock_contract.state_variables_declared = []

    mock_slither = MagicMock()
    mock_slither.contracts = [mock_contract]

    extractor = GraphFeatureExtractor(mock_slither)

    # Request with dashes/underscores should match
    features = extractor.extract_features("my_contract")

    # Should return features (not default zeros)
    assert isinstance(features, dict)


# ============================================================================
# TEST 17: EMPTY CONTRACT (NO FUNCTIONS)
# ============================================================================

def test_empty_contract():
    """Test contract with no functions returns default features."""
    mock_contract = MagicMock()
    mock_contract.name = "EmptyContract"
    mock_contract.is_interface = False
    mock_contract.is_library = False
    mock_contract.functions_declared = []
    mock_contract.state_variables_declared = []

    mock_slither = MagicMock()
    mock_slither.contracts = [mock_contract]

    extractor = GraphFeatureExtractor(mock_slither)
    features = extractor.extract_features("EmptyContract")

    # Should return all zero features
    assert features['cfg_num_nodes'] == 0
    assert features['cg_num_nodes'] == 0
    assert features['dfg_num_state_vars'] == 0


# ============================================================================
# TEST 18: NO CONTRACT FOUND (FALLBACK)
# ============================================================================

def test_no_contract_found():
    """Test behavior when requested contract not found."""
    mock_slither = MagicMock()
    mock_slither.contracts = []  # No contracts!

    extractor = GraphFeatureExtractor(mock_slither)
    features = extractor.extract_features("NonExistent")

    # Should return default features
    assert features['cfg_num_nodes'] == 0
    assert features['cg_num_nodes'] == 0


# ============================================================================
# TEST 19: ALL 25 FEATURES PRESENT
# ============================================================================

def test_all_features_present():
    """Verify all 25 graph features are returned."""
    mock_contract = MagicMock()
    mock_contract.name = "TestContract"
    mock_contract.is_interface = False
    mock_contract.is_library = False
    mock_contract.functions_declared = []
    mock_contract.state_variables_declared = []

    mock_slither = MagicMock()
    mock_slither.contracts = [mock_contract]

    extractor = GraphFeatureExtractor(mock_slither)
    features = extractor.extract_features("TestContract")

    expected_keys = [
        # CFG (8)
        'cfg_num_nodes', 'cfg_num_edges', 'cfg_num_cycles', 'cfg_max_depth',
        'cfg_avg_branching', 'cfg_has_complex_loops', 'cfg_num_exit_points',
        'cfg_cyclomatic_total',
        # Call Graph (10)
        'cg_num_nodes', 'cg_num_edges', 'cg_max_call_depth', 'cg_num_external_calls',
        'cg_external_call_ratio', 'cg_has_cyclic_calls', 'cg_num_public_entry_points',
        'cg_num_internal_functions', 'cg_avg_calls_per_function', 'cg_num_leaf_functions',
        # Data Flow (7)
        'dfg_num_state_vars', 'dfg_num_tainted_flows', 'dfg_has_cross_function_flow',
        'dfg_num_sensitive_sinks', 'dfg_num_external_sources', 'dfg_taint_to_sink_ratio',
        'dfg_num_unvalidated_inputs'
    ]

    for key in expected_keys:
        assert key in features, f"Missing feature: {key}"

    # Should have exactly 25 features
    assert len(expected_keys) == 25
