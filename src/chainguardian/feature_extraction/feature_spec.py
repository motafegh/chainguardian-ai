"""
Feature Specification and Registry.
Centralized feature definitions, defaults, and tier mappings for all 226 features.
"""

from typing import Dict, Any, List

# ============================================================================
# TIER 1: Core Features (56 total)
# ============================================================================

TIER1_DETECTOR_FLAGS = [
    # Grouped detector boolean flags (23 features)
    'has_reentrancy',
    'has_tx_origin',
    'has_unchecked_call',
    'has_delegatecall',
    'has_timestamp_dependence',
    'has_access_control_issue',
    'has_arithmetic_issue',
    'has_unchecked_low_level_call',
    'has_dangerous_strict_equality',
    'has_locked_ether',
    'has_state_variable_shadowing',
    'has_uninitialized_storage',
    'has_naming_convention_violation',
    'has_unused_state_variable',
    'has_costly_loop',
    'has_external_function',
    'has_deprecated_construct',
    'has_incorrect_equality',
    'has_boolean_constant_misuse',
    'has_divide_before_multiply',
    'has_weak_randomness',
    'has_assembly_usage',
    'has_low_level_calls',
]

TIER1_SEVERITY_COUNTS = [
    # Detector severity counts (3 features)
    'high_severity_count',
    'medium_severity_count',
    'low_severity_count',
]

TIER1_API_COUNTS = [
    # Direct from Slither Contract API (8 features)
    'num_functions',
    'num_state_vars',
    'num_modifiers',
    'num_events',
    'num_external_calls',
    'num_low_level_calls',
    'num_payable_functions',
    'inheritance_depth',
]

TIER1_COMPLEXITY = [
    # Code complexity metrics (3 features)
    'max_cyclomatic_complexity',
    'avg_function_complexity',
    'total_cyclomatic_complexity',
]

TIER1_CODE_QUALITY = [
    # Source code parsing (3 features)
    'lines_of_code',
    'comment_lines',
    'comment_to_code_ratio',
]

TIER1_DETECTOR_STATS = [
    # Aggregated detector statistics (7 features)
    'total_detectors_fired',
    'high_confidence_count',
    'medium_confidence_count',
    'low_confidence_count',
    'unique_detector_types',
    'detectors_per_function',
    'detectors_per_loc',
]

TIER1_RISK_SCORES = [
    # Composite risk scores (4 features)
    'security_risk_score',
    'code_quality_score',
    'overall_risk_score',
    'is_high_risk',
]

# ============================================================================
# TIER 2: Semantic + Graph Features (33 total)
# ============================================================================

TIER2_SEMANTIC = [
    # CEI Pattern & Reentrancy Protection (8 features)
    'cei_violations',
    'cei_safe_functions',
    'cei_pattern_score',
    'has_reentrancy_guard',
    'functions_with_reentrancy_guard',
    'state_before_call_count',
    'state_after_call_count',
    'unchecked_calls_in_critical_context',
]

TIER2_CFG = [
    # Control Flow Graph analysis (8 features)
    'cfg_num_cycles',
    'cfg_max_depth',
    'cfg_avg_branching_factor',
    'cfg_num_complex_loops',
    'cfg_num_exit_points',
    'cfg_unreachable_nodes',
    'cfg_dominators_count',
    'cfg_post_dominators_count',
]

TIER2_CALL_GRAPH = [
    # Call graph analysis (10 features)
    'call_graph_depth',
    'call_graph_num_external_calls',
    'call_graph_num_internal_calls',
    'call_graph_cyclic_calls',
    'call_graph_num_leaf_functions',
    'call_graph_max_fan_out',
    'call_graph_max_fan_in',
    'call_graph_strongly_connected_components',
    'call_graph_longest_path',
    'call_graph_critical_functions',
]

TIER2_DATAFLOW = [
    # Data flow analysis (7 features)
    'dataflow_num_tainted_flows',
    'dataflow_num_sinks',
    'dataflow_cross_function_flows',
    'dataflow_unvalidated_inputs',
    'dataflow_tainted_storage_writes',
    'dataflow_tainted_external_calls',
    'dataflow_sanitization_points',
]

# ============================================================================
# TIER 3: Advanced Features (68 total)
# ============================================================================

TIER3_SLITHIR = [
    # SlithIR operation counts (15 features)
    'ir_highlevelcall_count',
    'ir_lowlevelcall_count',
    'ir_internalcall_count',
    'ir_librarycall_count',
    'ir_assignment_count',
    'ir_binary_count',
    'ir_unary_count',
    'ir_transfer_count',
    'ir_send_count',
    'ir_taint_sources',
    'ir_taint_sinks',
    'ir_tainted_delegatecall',
    'ir_unchecked_return_values',
    'ir_taint_propagation_ratio',
    'ir_arithmetic_ops',
]

TIER3_EXTENDED_API = [
    # Extended Slither API features (15 features)
    'num_functions_declared',
    'num_public_functions',
    'num_external_functions',
    'num_internal_functions',
    'num_private_functions',
    'num_view_functions',
    'num_pure_functions',
    'num_constructors',
    'num_enums',
    'num_structs',
    'total_state_reads',
    'total_state_writes',
    'avg_state_reads_per_function',
    'avg_state_writes_per_function',
    'num_contracts_in_file',
]

TIER3_AGGREGATIONS = [
    # Mathematical aggregations (38 features)
    # Confidence ratios
    'high_confidence_ratio',
    'medium_confidence_ratio',
    'low_confidence_ratio',
    # Severity ratios
    'high_severity_ratio',
    'medium_severity_ratio',
    'low_severity_ratio',
    'critical_to_total_ratio',
    # Function ratios
    'external_to_total_functions',
    'public_to_total_functions',
    'view_to_total_functions',
    'payable_to_total_functions',
    # State interaction ratios
    'state_reads_to_writes_ratio',
    'external_calls_to_functions_ratio',
    # Detector category counts
    'security_detector_count',
    'optimization_detector_count',
    'best_practice_detector_count',
    'gas_detector_count',
    'reentrancy_detector_count',
    'access_control_detector_count',
    'arithmetic_detector_count',
    # Complexity aggregations
    'complexity_variance',
    'high_complexity_function_count',
    'low_complexity_function_count',
    # Code quality aggregations
    'avg_loc_per_function',
    'max_loc_per_function',
    'functions_with_comments_ratio',
    # Call pattern aggregations
    'recursive_call_count',
    'self_destruct_count',
    'create_contract_count',
    # Node-level aggregations
    'if_node_count',
    'require_node_count',
    'assert_node_count',
    'assembly_node_count',
    'return_node_count',
    # Risk aggregations
    'high_risk_pattern_count',
    'medium_risk_pattern_count',
    'low_risk_pattern_count',
    'vulnerability_density',  # detectors per 100 LOC
]

# ============================================================================
# TIER 4: Individual Detector Flags (69 unique, 93 total with overlap)
# ============================================================================

# Note: TIER 4 features are dynamically generated from slither.detectors.all_detectors
# These are examples of detector names that may be discovered:
TIER4_DETECTOR_EXAMPLES = [
    'detector_reentrancy_eth',
    'detector_reentrancy_no_eth',
    'detector_reentrancy_benign',
    'detector_tx_origin',
    'detector_unchecked_send',
    'detector_unchecked_transfer',
    'detector_unchecked_lowlevel',
    'detector_delegatecall_loop',
    'detector_msg_value_loop',
    'detector_timestamp',
    'detector_block_number',
    'detector_dangerous_strict_equality',
    'detector_locked_ether',
    'detector_arbitrary_send_eth',
    'detector_arbitrary_send_erc20',
    'detector_suicidal',
    'detector_uninitialized_state',
    'detector_uninitialized_storage',
    'detector_uninitialized_local',
    'detector_unprotected_upgrade',
    'detector_function_id_collision',
    'detector_name_reused',
    'detector_shadowing_state',
    'detector_shadowing_local',
    'detector_shadowing_builtin',
    'detector_weak_prng',
    'detector_controlled_array_length',
    'detector_divide_before_multiply',
    'detector_boolean_cst',
    'detector_incorrect_equality',
    'detector_write_after_write',
    'detector_dead_code',
    'detector_unused_state',
    'detector_costly_loop',
    'detector_external_function',
    'detector_naming_convention',
    'detector_deprecated_standards',
    # ... (up to 93 total detectors auto-discovered)
]

# ============================================================================
# TIER DEFINITIONS
# ============================================================================

TIER_DEFINITIONS = {
    'tier1': (
        TIER1_DETECTOR_FLAGS +
        TIER1_SEVERITY_COUNTS +
        TIER1_API_COUNTS +
        TIER1_COMPLEXITY +
        TIER1_CODE_QUALITY +
        TIER1_DETECTOR_STATS +
        TIER1_RISK_SCORES
    ),  # 56 features
    'tier2': (
        TIER2_SEMANTIC +
        TIER2_CFG +
        TIER2_CALL_GRAPH +
        TIER2_DATAFLOW
    ),  # 33 features
    'tier3': (
        TIER3_SLITHIR +
        TIER3_EXTENDED_API +
        TIER3_AGGREGATIONS
    ),  # 68 features
    'tier4': [],  # Dynamically populated with detector_* features (69 unique)
}

# ============================================================================
# MODE DEFINITIONS
# ============================================================================

MODE_TIER_MAPPING = {
    'comprehensive': ['tier1', 'tier2', 'tier3'],      # 157 features
    'maximum': ['tier1', 'tier2', 'tier3', 'tier4'],  # 226 features
    'optimized': ['tier1', 'tier2'],                  # 89 features (future: custom subset)
}

# ============================================================================
# FEATURE DEFAULTS
# ============================================================================

# Default values for each feature type
BOOLEAN_DEFAULT = False
COUNT_DEFAULT = 0
RATIO_DEFAULT = 0.0
SCORE_DEFAULT = 0.0
STRING_DEFAULT = "unknown"

def get_feature_defaults() -> Dict[str, Any]:
    """
    Get default values for all features.

    Returns:
        Dictionary with all features set to appropriate defaults
    """
    defaults = {}

    # Tier 1 defaults
    for feature in TIER1_DETECTOR_FLAGS:
        defaults[feature] = BOOLEAN_DEFAULT
    for feature in TIER1_SEVERITY_COUNTS:
        defaults[feature] = COUNT_DEFAULT
    for feature in TIER1_API_COUNTS:
        defaults[feature] = COUNT_DEFAULT
    for feature in TIER1_COMPLEXITY:
        defaults[feature] = COUNT_DEFAULT
    for feature in TIER1_CODE_QUALITY:
        defaults[feature] = COUNT_DEFAULT
    for feature in TIER1_DETECTOR_STATS:
        defaults[feature] = COUNT_DEFAULT
    for feature in TIER1_RISK_SCORES:
        if 'is_' in feature:
            defaults[feature] = BOOLEAN_DEFAULT
        else:
            defaults[feature] = SCORE_DEFAULT

    # Tier 2 defaults
    for feature in TIER2_SEMANTIC:
        if 'has_' in feature:
            defaults[feature] = BOOLEAN_DEFAULT
        elif 'score' in feature or 'ratio' in feature:
            defaults[feature] = RATIO_DEFAULT
        else:
            defaults[feature] = COUNT_DEFAULT

    for feature in TIER2_CFG + TIER2_CALL_GRAPH + TIER2_DATAFLOW:
        defaults[feature] = COUNT_DEFAULT

    # Tier 3 defaults
    for feature in TIER3_SLITHIR:
        if 'ratio' in feature:
            defaults[feature] = RATIO_DEFAULT
        else:
            defaults[feature] = COUNT_DEFAULT

    for feature in TIER3_EXTENDED_API:
        defaults[feature] = COUNT_DEFAULT

    for feature in TIER3_AGGREGATIONS:
        if 'ratio' in feature or 'density' in feature:
            defaults[feature] = RATIO_DEFAULT
        else:
            defaults[feature] = COUNT_DEFAULT

    return defaults


def get_default_feature_dict(failure_reason: str, error_message: str,
                            contract_name: str = "", file_path: str = "") -> Dict[str, Any]:
    """
    Get complete feature dictionary with defaults for failed extractions.

    Args:
        failure_reason: Category of failure (COMPILATION_ERROR, IMPORT_ERROR, etc.)
        error_message: Detailed error message
        contract_name: Name of the contract (optional)
        file_path: Path to the contract file (optional)

    Returns:
        Dictionary with all features set to defaults plus metadata
    """
    features = get_feature_defaults()

    # Add metadata
    features['contract_name'] = contract_name
    features['file_path'] = file_path
    features['extraction_status'] = 'failed'
    features['failure_reason'] = failure_reason
    features['error_message'] = error_message

    return features


def get_features_for_mode(mode: str) -> List[str]:
    """
    Get list of feature names for a given mode.

    Args:
        mode: Extraction mode ('comprehensive', 'maximum', 'optimized')

    Returns:
        List of feature names to extract
    """
    if mode not in MODE_TIER_MAPPING:
        raise ValueError(f"Unknown mode: {mode}. Must be one of {list(MODE_TIER_MAPPING.keys())}")

    features = []
    for tier in MODE_TIER_MAPPING[mode]:
        features.extend(TIER_DEFINITIONS[tier])

    return features


def get_tier_count() -> Dict[str, int]:
    """
    Get feature count for each tier.

    Returns:
        Dictionary mapping tier name to feature count
    """
    return {
        'tier1': len(TIER_DEFINITIONS['tier1']),  # 56
        'tier2': len(TIER_DEFINITIONS['tier2']),  # 33
        'tier3': len(TIER_DEFINITIONS['tier3']),  # 68
        'tier4': 69,  # Dynamically generated, approximate unique count
    }


# ============================================================================
# FEATURE METADATA (for documentation and validation)
# ============================================================================

FEATURE_DESCRIPTIONS = {
    # Tier 1 examples
    'has_reentrancy': 'Boolean flag indicating reentrancy vulnerability detected',
    'high_severity_count': 'Count of high-severity detector findings',
    'num_functions': 'Total number of functions in contract',
    'security_risk_score': 'Composite security risk score (0-100)',

    # Tier 2 examples
    'cei_violations': 'Number of Checks-Effects-Interactions pattern violations',
    'cfg_num_cycles': 'Number of cycles in control flow graph',

    # Tier 3 examples
    'ir_highlevelcall_count': 'Number of high-level calls in SlithIR',
    'high_confidence_ratio': 'Ratio of high-confidence detectors to total',
}

FEATURE_CATEGORIES = {
    'security': TIER1_DETECTOR_FLAGS + TIER2_SEMANTIC[:4] + ['security_risk_score'],
    'complexity': TIER1_COMPLEXITY + TIER2_CFG,
    'code_quality': TIER1_CODE_QUALITY + TIER1_DETECTOR_STATS,
    'dataflow': TIER2_DATAFLOW + TIER3_SLITHIR[:9],
}
