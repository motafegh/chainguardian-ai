"""
Tier 2: Semantic + Graph Features (33 total)
CEI Pattern Analysis (8) + CFG Analysis (8) + Call Graph (10) + Data Flow (7)
"""

from typing import Dict, Any
from slither.core.declarations import Contract
from slither.core.cfg.node import Node
from slither.slithir.operations import (
    HighLevelCall, LowLevelCall, Transfer, Send
)
import networkx as nx
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# TIER 2 FEATURE EXTRACTION
# ============================================================================

def extract_tier2_features(contract: Contract) -> Dict[str, Any]:
    """
    Extract all 33 Tier 2 semantic + graph features.

    Args:
        contract: Slither Contract object

    Returns:
        Dictionary with 33 features
    """
    features = {}

    try:
        # Extract semantic pattern features (8 features)
        semantic_features = _extract_semantic_patterns(contract)
        features.update(semantic_features)

        # Extract CFG features (8 features)
        cfg_features = _extract_cfg_features(contract)
        features.update(cfg_features)

        # Extract call graph features (10 features)
        call_graph_features = _extract_call_graph_features(contract)
        features.update(call_graph_features)

        # Extract data flow features (7 features)
        dataflow_features = _extract_dataflow_features(contract)
        features.update(dataflow_features)

    except Exception as e:
        logger.error(f"Tier 2 extraction failed: {e}")
        # Return defaults on failure
        from .feature_spec import TIER_DEFINITIONS
        for feature_name in TIER_DEFINITIONS['tier2']:
            if 'has_' in feature_name:
                features[feature_name] = False
            elif 'ratio' in feature_name or 'score' in feature_name:
                features[feature_name] = 0.0
            else:
                features[feature_name] = 0

    return features


# ============================================================================
# SEMANTIC PATTERN ANALYSIS (from semantic_analyzer.py)
# ============================================================================

def _extract_semantic_patterns(contract: Contract) -> Dict[str, Any]:
    """
    Analyze CEI pattern violations and reentrancy protection.

    Returns:
        Dictionary with 8 semantic features
    """
    features = {
        'cei_violations': _count_cei_violations(contract),
        'cei_safe_functions': _count_cei_safe_functions(contract),
        'has_reentrancy_guard': _detect_reentrancy_guard(contract),
        'state_before_call_count': _count_safe_state_modifications(contract),
        'state_after_call_count': 0,  # Will be calculated below
        'unchecked_calls_in_critical_context': _count_dangerous_unchecked_calls(contract),
    }

    # Calculate CEI pattern score
    violations = features['cei_violations']
    safe = features['cei_safe_functions']
    total = violations + safe
    features['cei_pattern_score'] = (safe / total) if total > 0 else 1.0

    # Count functions with reentrancy guard
    features['functions_with_reentrancy_guard'] = _count_guarded_functions(contract)

    # State after call count is same as violations
    features['state_after_call_count'] = violations

    return features


def _count_cei_violations(contract: Contract) -> int:
    """
    Count functions that violate CEI pattern.
    State modification AFTER external call = violation.
    """
    violations = 0

    for func in contract.functions:
        if func.is_constructor or func.view or func.pure:
            continue

        # Track if we've seen external call
        seen_external_call = False

        for node in func.nodes:
            # Check if this node is external call
            if _is_external_call(node):
                seen_external_call = True

            # Check if this node modifies state AFTER external call
            if seen_external_call and _modifies_state(node):
                violations += 1
                break  # Count once per function

    return violations


def _count_cei_safe_functions(contract: Contract) -> int:
    """Count functions that properly follow CEI pattern."""
    safe_count = 0

    for func in contract.functions:
        if func.is_constructor or func.view or func.pure:
            continue

        has_external_call = False
        has_state_mod = False
        state_before_call = True

        for node in func.nodes:
            if _modifies_state(node):
                has_state_mod = True
                if has_external_call:
                    state_before_call = False

            if _is_external_call(node):
                has_external_call = True

        # Safe if: (no calls) OR (state modified before calls)
        if has_external_call and has_state_mod and state_before_call:
            safe_count += 1

    return safe_count


def _detect_reentrancy_guard(contract: Contract) -> bool:
    """
    Detect if contract uses ReentrancyGuard pattern.
    - Has 'nonReentrant' modifier, OR
    - Has mutex/lock state variable
    """
    # Check for nonReentrant modifier
    for modifier in contract.modifiers:
        if 'nonreentrant' in modifier.name.lower():
            return True

    # Check for mutex pattern
    for var in contract.state_variables:
        name_lower = var.name.lower()
        if any(pattern in name_lower for pattern in ['lock', 'mutex', 'guard', 'entered']):
            return True

    return False


def _count_guarded_functions(contract: Contract) -> int:
    """Count functions protected by reentrancy guard."""
    if not _detect_reentrancy_guard(contract):
        return 0

    guarded = 0
    for func in contract.functions:
        if func.is_constructor or func.view or func.pure:
            continue

        # Check if function has nonReentrant modifier
        for modifier in func.modifiers:
            if 'nonreentrant' in modifier.name.lower():
                guarded += 1
                break

    return guarded


def _count_safe_state_modifications(contract: Contract) -> int:
    """Count state modifications that occur BEFORE external calls."""
    safe_count = 0

    for func in contract.functions:
        if func.is_constructor or func.view or func.pure:
            continue

        seen_state_mod = False

        for node in func.nodes:
            if _modifies_state(node):
                seen_state_mod = True

            if _is_external_call(node):
                if seen_state_mod:
                    safe_count += 1
                break

    return safe_count


def _count_dangerous_unchecked_calls(contract: Contract) -> int:
    """
    Count unchecked low-level calls in critical context.
    - Before state update (money could be lost)
    - Return value not checked
    """
    dangerous = 0

    for func in contract.functions:
        if func.view or func.pure:
            continue

        for node in func.nodes:
            if not _is_low_level_call(node):
                continue

            # Check if return value is used
            if not _return_value_checked(node):
                # Check if followed by state modification
                if _has_state_modification_after(func, node):
                    dangerous += 1

    return dangerous


# Helper methods for semantic analysis

def _is_external_call(node: Node) -> bool:
    """Check if node contains external call."""
    for ir in node.irs:
        if isinstance(ir, (HighLevelCall, LowLevelCall, Transfer, Send)):
            return True
    return False


def _is_low_level_call(node: Node) -> bool:
    """Check if node contains low-level call."""
    for ir in node.irs:
        if isinstance(ir, LowLevelCall):
            return True
    return False


def _modifies_state(node: Node) -> bool:
    """Check if node modifies contract state."""
    return len(node.state_variables_written) > 0


def _return_value_checked(node: Node) -> bool:
    """Check if call's return value is checked."""
    for ir in node.irs:
        if isinstance(ir, LowLevelCall):
            # Check if assigned to variable
            if hasattr(ir, 'lvalue') and ir.lvalue:
                return True
    return False


def _has_state_modification_after(func, call_node: Node) -> bool:
    """Check if state is modified after this call node."""
    found_call = False

    for node in func.nodes:
        if node == call_node:
            found_call = True
            continue

        if found_call and _modifies_state(node):
            return True

    return False


# ============================================================================
# CONTROL FLOW GRAPH ANALYSIS
# ============================================================================

def _extract_cfg_features(contract: Contract) -> Dict[str, Any]:
    """
    Extract CFG features using NetworkX.

    Returns:
        Dictionary with 8 CFG features
    """
    features = {
        'cfg_num_cycles': 0,
        'cfg_max_depth': 0,
        'cfg_avg_branching_factor': 0.0,
        'cfg_num_complex_loops': 0,
        'cfg_num_exit_points': 0,
        'cfg_unreachable_nodes': 0,
        'cfg_dominators_count': 0,
        'cfg_post_dominators_count': 0,
    }

    total_nodes = 0
    total_edges = 0
    max_depth = 0
    has_complex = False
    exit_points = 0

    for func in contract.functions_declared:
        if not func.nodes:
            continue

        # Build CFG as NetworkX graph
        G = nx.DiGraph()

        for node in func.nodes:
            G.add_node(node)
            total_nodes += 1

            # Count edges
            for son in node.sons:
                G.add_edge(node, son)
                total_edges += 1

            # Count exit points (return, revert, throw)
            node_type_str = str(node.type)
            if any(kw in node_type_str.lower() for kw in ['return', 'throw', 'revert']):
                exit_points += 1

        # Detect cycles in this function
        try:
            cycles = list(nx.simple_cycles(G))
            features['cfg_num_cycles'] += len(cycles)

            # Complex loops: nested loops (cycle within cycle)
            if len(cycles) > 1:
                features['cfg_num_complex_loops'] += 1

        except Exception:
            pass

        # Calculate max depth (longest path)
        try:
            if len(G.nodes) > 0:
                entry = func.entry_point if func.entry_point else list(G.nodes)[0]
                lengths = nx.single_source_shortest_path_length(G, entry)
                func_max_depth = max(lengths.values()) if lengths else 0
                max_depth = max(max_depth, func_max_depth)
        except Exception:
            pass

        # Count dominators (simplified: just use NetworkX algorithms)
        try:
            if len(G.nodes) > 0 and func.entry_point:
                dominators = nx.dominance_frontiers(G, func.entry_point)
                features['cfg_dominators_count'] += len(dominators)
        except Exception:
            pass

    features['cfg_max_depth'] = max_depth
    features['cfg_num_exit_points'] = exit_points

    # Average branching factor
    if total_nodes > 0:
        features['cfg_avg_branching_factor'] = round(total_edges / total_nodes, 2)

    return features


# ============================================================================
# CALL GRAPH ANALYSIS
# ============================================================================

def _extract_call_graph_features(contract: Contract) -> Dict[str, Any]:
    """
    Extract call graph features using NetworkX.

    Returns:
        Dictionary with 10 call graph features
    """
    features = {
        'call_graph_depth': 0,
        'call_graph_num_external_calls': 0,
        'call_graph_num_internal_calls': 0,
        'call_graph_cyclic_calls': 0,
        'call_graph_num_leaf_functions': 0,
        'call_graph_max_fan_out': 0,
        'call_graph_max_fan_in': 0,
        'call_graph_strongly_connected_components': 0,
        'call_graph_longest_path': 0,
        'call_graph_critical_functions': 0,
    }

    functions = contract.functions_declared
    if not functions:
        return features

    # Build call graph
    G = nx.DiGraph()

    for func in functions:
        G.add_node(func.name)

        # Add edges for internal calls
        for called_func in func.internal_calls:
            if hasattr(called_func, 'name'):
                G.add_edge(func.name, called_func.name)
                features['call_graph_num_internal_calls'] += 1

        # Count external calls
        features['call_graph_num_external_calls'] += len(func.external_calls_as_expressions)

    # Calculate call depth (longest path in call graph)
    try:
        if len(G.nodes) > 0:
            public_funcs = [f for f in functions if f.visibility in ['public', 'external']]
            max_depth = 0
            for pub_func in public_funcs:
                try:
                    lengths = nx.single_source_shortest_path_length(G, pub_func.name)
                    if lengths:
                        max_depth = max(max_depth, max(lengths.values()))
                except Exception:
                    pass
            features['call_graph_depth'] = max_depth
    except Exception:
        pass

    # Detect cyclic calls (recursion)
    try:
        cycles = list(nx.simple_cycles(G))
        features['call_graph_cyclic_calls'] = len(cycles)
    except Exception:
        pass

    # Leaf functions (no outgoing calls)
    for node in G.nodes:
        if G.out_degree(node) == 0:
            features['call_graph_num_leaf_functions'] += 1

    # Max fan-out and fan-in
    try:
        if len(G.nodes) > 0:
            features['call_graph_max_fan_out'] = max([G.out_degree(n) for n in G.nodes])
            features['call_graph_max_fan_in'] = max([G.in_degree(n) for n in G.nodes])
    except Exception:
        pass

    # Strongly connected components
    try:
        scc = list(nx.strongly_connected_components(G))
        features['call_graph_strongly_connected_components'] = len(scc)
    except Exception:
        pass

    # Longest path
    try:
        if nx.is_directed_acyclic_graph(G):
            longest = nx.dag_longest_path_length(G)
            features['call_graph_longest_path'] = longest
    except Exception:
        pass

    # Critical functions (high fan-in, indicating many callers)
    try:
        for node in G.nodes:
            if G.in_degree(node) >= 3:  # Threshold: 3+ callers
                features['call_graph_critical_functions'] += 1
    except Exception:
        pass

    return features


# ============================================================================
# DATA FLOW ANALYSIS
# ============================================================================

def _extract_dataflow_features(contract: Contract) -> Dict[str, Any]:
    """
    Extract data flow features.

    Returns:
        Dictionary with 7 data flow features
    """
    features = {
        'dataflow_num_tainted_flows': 0,
        'dataflow_num_sinks': 0,
        'dataflow_cross_function_flows': 0,
        'dataflow_unvalidated_inputs': 0,
        'dataflow_tainted_storage_writes': 0,
        'dataflow_tainted_external_calls': 0,
        'dataflow_sanitization_points': 0,
    }

    # Analyze each function for data flows
    state_writers = set()
    state_readers = set()

    for func in contract.functions_declared:
        # State variable usage
        vars_written = func.state_variables_written
        vars_read = func.state_variables_read

        for var in vars_written:
            state_writers.add(var.name)
        for var in vars_read:
            state_readers.add(var.name)

        # Sensitive sinks (transfer, send, call, delegatecall, selfdestruct)
        for call in func.external_calls_as_expressions:
            call_str = str(call).lower()
            if any(sink in call_str for sink in ['transfer', 'send', 'call', 'delegatecall', 'selfdestruct']):
                features['dataflow_num_sinks'] += 1

        # Tainted flows (simplified: parameters used in sensitive operations)
        if func.parameters and (func.external_calls_as_expressions or vars_written):
            features['dataflow_num_tainted_flows'] += 1

            # Tainted storage writes
            if vars_written:
                features['dataflow_tainted_storage_writes'] += 1

            # Tainted external calls
            if func.external_calls_as_expressions:
                features['dataflow_tainted_external_calls'] += 1

        # Unvalidated inputs (functions with params but no require/assert)
        if func.parameters:
            has_validation = False
            for node in func.nodes:
                node_type = str(node.type).lower()
                if 'require' in node_type or 'assert' in node_type:
                    has_validation = True
                    features['dataflow_sanitization_points'] += 1
                    break

            if not has_validation:
                features['dataflow_unvalidated_inputs'] += 1

    # Cross-function flows (state vars both read and written)
    cross_flows = state_writers.intersection(state_readers)
    features['dataflow_cross_function_flows'] = len(cross_flows)

    return features
