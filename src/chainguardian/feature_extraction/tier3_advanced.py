"""
Tier 3: Advanced Features (68 total)
SlithIR Operations (15) + Extended API (15) + Aggregations (38)
"""

from typing import Dict, Any, Set
from slither import Slither
from slither.core.declarations import Contract
from slither.slithir.operations import (
    HighLevelCall, LowLevelCall, InternalCall, LibraryCall,
    Assignment, Binary, Unary, Transfer, Send,
    SolidityCall, Index, Member, Return
)
from slither.slithir.variables import (
    ReferenceVariable, TemporaryVariable, TupleVariable
)
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# TIER 3 FEATURE EXTRACTION
# ============================================================================

def extract_tier3_features(slither: Slither, contract: Contract) -> Dict[str, Any]:
    """
    Extract all 68 Tier 3 advanced features.

    Args:
        slither: Slither analysis object
        contract: Target contract object

    Returns:
        Dictionary with 68 features
    """
    features = {}

    try:
        # Extract SlithIR operation features (15 features)
        ir_features = _extract_slithir_features(contract)
        features.update(ir_features)

        # Extract extended API features (15 features)
        extended_api = _extract_extended_api_features(slither, contract)
        features.update(extended_api)

        # Compute aggregations (38 features)
        # NOTE: Aggregations require Tier 1 features, so they're computed separately
        # For now, initialize with defaults
        aggregations = _compute_aggregations(features, {})
        features.update(aggregations)

    except Exception as e:
        logger.error(f"Tier 3 extraction failed: {e}")
        # Return defaults on failure
        from .feature_spec import TIER_DEFINITIONS
        for feature_name in TIER_DEFINITIONS['tier3']:
            if 'ratio' in feature_name or 'density' in feature_name:
                features[feature_name] = 0.0
            else:
                features[feature_name] = 0

    return features


# ============================================================================
# SLITHIR OPERATION ANALYSIS
# ============================================================================

def _extract_slithir_features(contract: Contract) -> Dict[str, Any]:
    """
    Deep SlithIR analysis with taint tracking.

    SlithIR = Slither's intermediate representation (like LLVM IR)
    - Enables precise data flow tracking
    - SSA form (Static Single Assignment)
    - Explicit operation types

    Returns:
        Dictionary with 15 SlithIR features
    """
    features = {
        'ir_highlevelcall_count': 0,
        'ir_lowlevelcall_count': 0,
        'ir_internalcall_count': 0,
        'ir_librarycall_count': 0,
        'ir_assignment_count': 0,
        'ir_binary_count': 0,
        'ir_unary_count': 0,
        'ir_transfer_count': 0,
        'ir_send_count': 0,
        'ir_taint_sources': 0,
        'ir_taint_sinks': 0,
        'ir_tainted_delegatecall': 0,
        'ir_unchecked_return_values': 0,
        'ir_taint_propagation_ratio': 0.0,
        'ir_arithmetic_ops': 0,
    }

    # Track tainted variables (SSA form)
    tainted_vars: Set[Any] = set()
    total_operations = 0

    for func in contract.functions_declared:
        if func.is_constructor or func.view or func.pure:
            continue

        # Initialize taint sources (function parameters)
        for param in func.parameters:
            tainted_vars.add(param)
            features['ir_taint_sources'] += 1

        # Analyze each IR operation
        for node in func.nodes:
            for ir in node.irs:
                total_operations += 1

                # Count operation types
                if isinstance(ir, HighLevelCall):
                    features['ir_highlevelcall_count'] += 1

                    # Check if call arguments are tainted
                    if hasattr(ir, 'arguments'):
                        if any(arg in tainted_vars for arg in ir.arguments):
                            # Tainted high-level call
                            pass

                    # Check return value usage (unchecked if lvalue not used)
                    if hasattr(ir, 'lvalue') and not ir.lvalue:
                        features['ir_unchecked_return_values'] += 1

                elif isinstance(ir, LowLevelCall):
                    features['ir_lowlevelcall_count'] += 1
                    features['ir_taint_sinks'] += 1

                    # Delegatecall with user-controlled input
                    if hasattr(ir, 'function_name'):
                        func_name = str(ir.function_name) if ir.function_name else ""
                        if 'delegatecall' in func_name.lower():
                            if hasattr(ir, 'arguments'):
                                if any(arg in tainted_vars for arg in ir.arguments):
                                    features['ir_tainted_delegatecall'] += 1

                elif isinstance(ir, InternalCall):
                    features['ir_internalcall_count'] += 1

                elif isinstance(ir, LibraryCall):
                    features['ir_librarycall_count'] += 1

                elif isinstance(ir, Assignment):
                    features['ir_assignment_count'] += 1

                    # Track taint propagation
                    if hasattr(ir, 'rvalue') and hasattr(ir, 'lvalue'):
                        if ir.rvalue in tainted_vars:
                            tainted_vars.add(ir.lvalue)

                elif isinstance(ir, Binary):
                    features['ir_binary_count'] += 1
                    features['ir_arithmetic_ops'] += 1

                elif isinstance(ir, Unary):
                    features['ir_unary_count'] += 1

                elif isinstance(ir, Transfer):
                    features['ir_transfer_count'] += 1
                    features['ir_taint_sinks'] += 1

                elif isinstance(ir, Send):
                    features['ir_send_count'] += 1
                    features['ir_taint_sinks'] += 1

    # Compute taint propagation ratio
    if total_operations > 0:
        features['ir_taint_propagation_ratio'] = round(
            len(tainted_vars) / total_operations, 3
        )
    else:
        features['ir_taint_propagation_ratio'] = 0.0

    return features


# ============================================================================
# EXTENDED API FEATURES
# ============================================================================

def _extract_extended_api_features(slither: Slither, contract: Contract) -> Dict[str, int]:
    """
    Extract extended contract-level features from Slither API.

    Returns:
        Dictionary with 15 extended API features
    """
    features = {
        'num_functions_declared': len(contract.functions_declared),
        'num_public_functions': 0,
        'num_external_functions': 0,
        'num_internal_functions': 0,
        'num_private_functions': 0,
        'num_view_functions': 0,
        'num_pure_functions': 0,
        'num_constructors': 0,
        'num_enums': len(contract.enums),
        'num_structs': len(contract.structures),
        'total_state_reads': 0,
        'total_state_writes': 0,
        'avg_state_reads_per_function': 0,
        'avg_state_writes_per_function': 0,
        'num_contracts_in_file': len(slither.contracts),
    }

    # Count by visibility and type
    for func in contract.functions_declared:
        # Visibility
        if func.visibility == 'public':
            features['num_public_functions'] += 1
        elif func.visibility == 'external':
            features['num_external_functions'] += 1
        elif func.visibility == 'internal':
            features['num_internal_functions'] += 1
        elif func.visibility == 'private':
            features['num_private_functions'] += 1

        # Type
        if func.view:
            features['num_view_functions'] += 1
        if func.pure:
            features['num_pure_functions'] += 1
        if func.is_constructor:
            features['num_constructors'] += 1

        # State variable access
        features['total_state_reads'] += len(func.state_variables_read)
        features['total_state_writes'] += len(func.state_variables_written)

    # Calculate averages
    num_funcs = features['num_functions_declared']
    if num_funcs > 0:
        features['avg_state_reads_per_function'] = round(
            features['total_state_reads'] / num_funcs, 2
        )
        features['avg_state_writes_per_function'] = round(
            features['total_state_writes'] / num_funcs, 2
        )

    return features


# ============================================================================
# AGGREGATIONS
# ============================================================================

def _compute_aggregations(tier3_features: Dict[str, Any],
                         tier1_features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute mathematical aggregations from extracted features.

    This function computes derived metrics and ratios from Tier 1 and Tier 3 features.

    Args:
        tier3_features: Features extracted in Tier 3
        tier1_features: Features from Tier 1 (for cross-tier aggregations)

    Returns:
        Dictionary with 38 aggregation features
    """
    features = {}

    # Get base counts (with safe defaults)
    high_sev = tier1_features.get('high_severity_count', 0)
    med_sev = tier1_features.get('medium_severity_count', 0)
    low_sev = tier1_features.get('low_severity_count', 0)
    total_sev = high_sev + med_sev + low_sev or 1  # Avoid division by zero

    high_conf = tier1_features.get('high_confidence_count', 0)
    med_conf = tier1_features.get('medium_confidence_count', 0)
    low_conf = tier1_features.get('low_confidence_count', 0)
    total_conf = high_conf + med_conf + low_conf or 1

    num_functions = tier3_features.get('num_functions_declared', 0) or 1  # Avoid division by zero
    num_external = tier3_features.get('num_external_functions', 0)
    num_public = tier3_features.get('num_public_functions', 0)
    num_view = tier3_features.get('num_view_functions', 0)
    num_payable = tier1_features.get('num_payable_functions', 0)

    state_reads = tier3_features.get('total_state_reads', 0)
    state_writes = tier3_features.get('total_state_writes', 0)
    total_state_ops = state_reads + state_writes or 1

    external_calls = tier1_features.get('num_external_calls', 0)
    loc = tier1_features.get('lines_of_code', 0) or 100  # Avoid division by zero

    # Confidence ratios (3 features)
    features['high_confidence_ratio'] = round(high_conf / total_conf, 3)
    features['medium_confidence_ratio'] = round(med_conf / total_conf, 3)
    features['low_confidence_ratio'] = round(low_conf / total_conf, 3)

    # Severity ratios (4 features)
    features['high_severity_ratio'] = round(high_sev / total_sev, 3)
    features['medium_severity_ratio'] = round(med_sev / total_sev, 3)
    features['low_severity_ratio'] = round(low_sev / total_sev, 3)
    features['critical_to_total_ratio'] = round(high_sev / total_sev, 3)  # Same as high_severity_ratio

    # Function ratios (4 features)
    features['external_to_total_functions'] = round(num_external / num_functions, 3)
    features['public_to_total_functions'] = round(num_public / num_functions, 3)
    features['view_to_total_functions'] = round(num_view / num_functions, 3)
    features['payable_to_total_functions'] = round(num_payable / num_functions, 3)

    # State interaction ratios (2 features)
    if state_writes > 0:
        features['state_reads_to_writes_ratio'] = round(state_reads / state_writes, 3)
    else:
        features['state_reads_to_writes_ratio'] = 0.0

    if num_functions > 0:
        features['external_calls_to_functions_ratio'] = round(external_calls / num_functions, 3)
    else:
        features['external_calls_to_functions_ratio'] = 0.0

    # Detector category counts (7 features)
    # These require parsing detector results, use placeholders for now
    features['security_detector_count'] = high_sev + med_sev
    features['optimization_detector_count'] = 0  # Requires detector metadata
    features['best_practice_detector_count'] = low_sev
    features['gas_detector_count'] = 0  # Requires detector metadata
    features['reentrancy_detector_count'] = 1 if tier1_features.get('has_reentrancy', False) else 0
    features['access_control_detector_count'] = 1 if tier1_features.get('has_access_control_issue', False) else 0
    features['arithmetic_detector_count'] = 1 if tier1_features.get('has_arithmetic_issue', False) else 0

    # Complexity aggregations (3 features)
    max_complexity = tier1_features.get('max_cyclomatic_complexity', 0)
    avg_complexity = tier1_features.get('avg_function_complexity', 0)

    # Variance approximation (simplified)
    features['complexity_variance'] = abs(max_complexity - avg_complexity)
    features['high_complexity_function_count'] = 1 if max_complexity > 10 else 0
    features['low_complexity_function_count'] = 1 if avg_complexity < 3 else 0

    # Code quality aggregations (3 features)
    features['avg_loc_per_function'] = round(loc / num_functions, 2)
    features['max_loc_per_function'] = 0  # Would require per-function LOC tracking
    comment_ratio = tier1_features.get('comment_to_code_ratio', 0)
    features['functions_with_comments_ratio'] = comment_ratio  # Approximation

    # Call pattern aggregations (3 features)
    features['recursive_call_count'] = 0  # Would require call graph analysis from Tier 2
    features['self_destruct_count'] = 0  # Would require AST analysis
    features['create_contract_count'] = 0  # Would require IR analysis

    # Node-level aggregations (5 features)
    # These require node-level analysis, use approximations
    features['if_node_count'] = max_complexity  # Approximation
    features['require_node_count'] = 0  # Would require node traversal
    features['assert_node_count'] = 0  # Would require node traversal
    features['assembly_node_count'] = 1 if tier1_features.get('has_assembly_usage', False) else 0
    features['return_node_count'] = num_functions  # Approximation: 1 return per function

    # Risk aggregations (4 features)
    features['high_risk_pattern_count'] = high_sev
    features['medium_risk_pattern_count'] = med_sev
    features['low_risk_pattern_count'] = low_sev
    features['vulnerability_density'] = round((total_sev / loc) * 100, 2)  # Per 100 LOC

    return features


# ============================================================================
# HELPER: Compute Aggregations with Tier 1 Context
# ============================================================================

def compute_tier3_aggregations(tier1_features: Dict[str, Any],
                              tier2_features: Dict[str, Any],
                              tier3_features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute aggregations that require features from multiple tiers.

    This is called AFTER all tiers are extracted to compute cross-tier aggregations.

    Args:
        tier1_features: Features from Tier 1
        tier2_features: Features from Tier 2
        tier3_features: Features from Tier 3

    Returns:
        Dictionary with updated Tier 3 aggregation features
    """
    # Merge all features for comprehensive aggregations
    all_features = {}
    all_features.update(tier1_features)
    all_features.update(tier2_features)
    all_features.update(tier3_features)

    # Recompute aggregations with full context
    aggregations = _compute_aggregations(all_features, tier1_features)

    # Add Tier 2-specific aggregations
    if 'call_graph_cyclic_calls' in tier2_features:
        aggregations['recursive_call_count'] = tier2_features['call_graph_cyclic_calls']

    if 'dataflow_sanitization_points' in tier2_features:
        aggregations['require_node_count'] = tier2_features['dataflow_sanitization_points']

    return aggregations
