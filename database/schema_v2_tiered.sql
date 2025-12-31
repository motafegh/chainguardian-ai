-- ============================================================================
-- ChainGuardian AI - Database Schema V2 (Tier-Based 152-Feature System)
-- ============================================================================
-- Created: 2024-12-31
-- Version: 2.0.0
-- Features: 152 features across 3 tiers (comprehensive mode)
-- Architecture: Normalized schema with separate tables for contracts and features
-- ============================================================================

-- Drop existing tables if they exist (clean slate)
DROP TABLE IF EXISTS vulnerability_labels CASCADE;
DROP TABLE IF EXISTS contract_features CASCADE;
DROP TABLE IF EXISTS contracts CASCADE;

-- ============================================================================
-- TABLE 1: contracts (Contract Metadata)
-- ============================================================================
-- Stores basic contract information and metadata
-- Each contract has one entry here, linked to features by contract_id
-- ============================================================================

CREATE TABLE contracts (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Contract identification
    contract_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    address VARCHAR(42),  -- Ethereum address (0x + 40 hex chars)

    -- Source code and compilation
    source_code TEXT,
    compiler_version VARCHAR(50),

    -- Extraction metadata
    extraction_status VARCHAR(50) DEFAULT 'success',  -- 'success' or failure reason
    extraction_mode VARCHAR(50) DEFAULT 'comprehensive',  -- 'comprehensive', 'maximum', 'optimized'
    extraction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    failure_reason TEXT,

    -- Data source and provenance
    dataset VARCHAR(100),  -- e.g., 'smartbugs_curated', 'production'
    data_source VARCHAR(100),  -- Original source name

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes for performance
    CONSTRAINT unique_contract UNIQUE (file_path, contract_name)
);

-- Indexes for faster queries
DROP INDEX IF EXISTS idx_contracts_dataset;
DROP INDEX IF EXISTS idx_contracts_extraction_status;
DROP INDEX IF EXISTS idx_contracts_extraction_mode;
DROP INDEX IF EXISTS idx_contracts_created_at;

CREATE INDEX idx_contracts_dataset ON contracts(dataset);
CREATE INDEX idx_contracts_extraction_status ON contracts(extraction_status);
CREATE INDEX idx_contracts_extraction_mode ON contracts(extraction_mode);
CREATE INDEX idx_contracts_created_at ON contracts(created_at);

-- ============================================================================
-- TABLE 2: contract_features (152 Feature Columns)
-- ============================================================================
-- Stores all 152 features for each contract
-- One-to-one relationship with contracts table
-- Features organized by tier for clarity
-- ============================================================================

CREATE TABLE contract_features (
    -- Primary key and foreign key
    id SERIAL PRIMARY KEY,
    contract_id INTEGER NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,

    -- ========================================================================
    -- TIER 1: CORE FEATURES (51 features)
    -- ========================================================================
    -- Detector Flags (23 features)
    has_reentrancy BOOLEAN DEFAULT FALSE,
    has_tx_origin BOOLEAN DEFAULT FALSE,
    has_unchecked_call BOOLEAN DEFAULT FALSE,
    has_delegatecall BOOLEAN DEFAULT FALSE,
    has_timestamp_dependence BOOLEAN DEFAULT FALSE,
    has_access_control_issue BOOLEAN DEFAULT FALSE,
    has_arithmetic_issue BOOLEAN DEFAULT FALSE,
    has_unchecked_low_level_call BOOLEAN DEFAULT FALSE,
    has_dangerous_strict_equality BOOLEAN DEFAULT FALSE,
    has_locked_ether BOOLEAN DEFAULT FALSE,
    has_state_variable_shadowing BOOLEAN DEFAULT FALSE,
    has_uninitialized_storage BOOLEAN DEFAULT FALSE,
    has_naming_convention_violation BOOLEAN DEFAULT FALSE,
    has_unused_state_variable BOOLEAN DEFAULT FALSE,
    has_costly_loop BOOLEAN DEFAULT FALSE,
    has_external_function BOOLEAN DEFAULT FALSE,
    has_deprecated_construct BOOLEAN DEFAULT FALSE,
    has_incorrect_equality BOOLEAN DEFAULT FALSE,
    has_boolean_constant_misuse BOOLEAN DEFAULT FALSE,
    has_divide_before_multiply BOOLEAN DEFAULT FALSE,
    has_weak_randomness BOOLEAN DEFAULT FALSE,
    has_assembly_usage BOOLEAN DEFAULT FALSE,
    has_low_level_calls BOOLEAN DEFAULT FALSE,

    -- Severity Counts (3 features)
    high_severity_count INTEGER DEFAULT 0,
    medium_severity_count INTEGER DEFAULT 0,
    low_severity_count INTEGER DEFAULT 0,

    -- API Counts (8 features)
    num_functions INTEGER DEFAULT 0,
    num_state_vars INTEGER DEFAULT 0,
    num_modifiers INTEGER DEFAULT 0,
    num_events INTEGER DEFAULT 0,
    num_external_calls INTEGER DEFAULT 0,
    num_low_level_calls INTEGER DEFAULT 0,
    num_payable_functions INTEGER DEFAULT 0,
    inheritance_depth INTEGER DEFAULT 0,

    -- Complexity Metrics (3 features)
    max_cyclomatic_complexity INTEGER DEFAULT 0,
    avg_function_complexity FLOAT DEFAULT 0.0,
    total_cyclomatic_complexity INTEGER DEFAULT 0,

    -- Code Quality (3 features)
    lines_of_code INTEGER DEFAULT 0,
    comment_lines INTEGER DEFAULT 0,
    comment_to_code_ratio FLOAT DEFAULT 0.0,

    -- Detector Statistics (7 features)
    total_detectors_fired INTEGER DEFAULT 0,
    high_confidence_count INTEGER DEFAULT 0,
    medium_confidence_count INTEGER DEFAULT 0,
    low_confidence_count INTEGER DEFAULT 0,
    unique_detector_types INTEGER DEFAULT 0,
    detectors_per_function FLOAT DEFAULT 0.0,
    detectors_per_loc FLOAT DEFAULT 0.0,

    -- Risk Scores (4 features)
    security_risk_score FLOAT DEFAULT 0.0,
    code_quality_score FLOAT DEFAULT 0.0,
    overall_risk_score FLOAT DEFAULT 0.0,
    is_high_risk BOOLEAN DEFAULT FALSE,

    -- ========================================================================
    -- TIER 2: SEMANTIC + GRAPH FEATURES (33 features)
    -- ========================================================================
    -- CEI Pattern Analysis (8 features)
    cei_violations INTEGER DEFAULT 0,
    cei_safe_functions INTEGER DEFAULT 0,
    cei_pattern_score FLOAT DEFAULT 0.0,
    has_reentrancy_guard BOOLEAN DEFAULT FALSE,
    functions_with_reentrancy_guard INTEGER DEFAULT 0,
    state_before_call_count INTEGER DEFAULT 0,
    state_after_call_count INTEGER DEFAULT 0,
    unchecked_calls_in_critical_context INTEGER DEFAULT 0,

    -- Control Flow Graph (8 features)
    cfg_num_cycles INTEGER DEFAULT 0,
    cfg_max_depth INTEGER DEFAULT 0,
    cfg_avg_branching_factor FLOAT DEFAULT 0.0,
    cfg_num_complex_loops INTEGER DEFAULT 0,
    cfg_num_exit_points INTEGER DEFAULT 0,
    cfg_unreachable_nodes INTEGER DEFAULT 0,
    cfg_dominators_count INTEGER DEFAULT 0,
    cfg_post_dominators_count INTEGER DEFAULT 0,

    -- Call Graph Analysis (10 features)
    call_graph_depth INTEGER DEFAULT 0,
    call_graph_num_external_calls INTEGER DEFAULT 0,
    call_graph_num_internal_calls INTEGER DEFAULT 0,
    call_graph_cyclic_calls INTEGER DEFAULT 0,
    call_graph_num_leaf_functions INTEGER DEFAULT 0,
    call_graph_max_fan_out INTEGER DEFAULT 0,
    call_graph_max_fan_in INTEGER DEFAULT 0,
    call_graph_strongly_connected_components INTEGER DEFAULT 0,
    call_graph_longest_path INTEGER DEFAULT 0,
    call_graph_critical_functions INTEGER DEFAULT 0,

    -- Data Flow Analysis (7 features)
    dataflow_num_tainted_flows INTEGER DEFAULT 0,
    dataflow_num_sinks INTEGER DEFAULT 0,
    dataflow_cross_function_flows INTEGER DEFAULT 0,
    dataflow_unvalidated_inputs INTEGER DEFAULT 0,
    dataflow_tainted_storage_writes INTEGER DEFAULT 0,
    dataflow_tainted_external_calls INTEGER DEFAULT 0,
    dataflow_sanitization_points INTEGER DEFAULT 0,

    -- ========================================================================
    -- TIER 3: ADVANCED FEATURES (68 features)
    -- ========================================================================
    -- SlithIR Operations (15 features)
    ir_highlevelcall_count INTEGER DEFAULT 0,
    ir_lowlevelcall_count INTEGER DEFAULT 0,
    ir_internalcall_count INTEGER DEFAULT 0,
    ir_librarycall_count INTEGER DEFAULT 0,
    ir_assignment_count INTEGER DEFAULT 0,
    ir_binary_count INTEGER DEFAULT 0,
    ir_unary_count INTEGER DEFAULT 0,
    ir_transfer_count INTEGER DEFAULT 0,
    ir_send_count INTEGER DEFAULT 0,
    ir_taint_sources INTEGER DEFAULT 0,
    ir_taint_sinks INTEGER DEFAULT 0,
    ir_tainted_delegatecall INTEGER DEFAULT 0,
    ir_unchecked_return_values INTEGER DEFAULT 0,
    ir_taint_propagation_ratio FLOAT DEFAULT 0.0,
    ir_arithmetic_ops INTEGER DEFAULT 0,

    -- Extended API (15 features)
    num_functions_declared INTEGER DEFAULT 0,
    num_public_functions INTEGER DEFAULT 0,
    num_external_functions INTEGER DEFAULT 0,
    num_internal_functions INTEGER DEFAULT 0,
    num_private_functions INTEGER DEFAULT 0,
    num_view_functions INTEGER DEFAULT 0,
    num_pure_functions INTEGER DEFAULT 0,
    num_constructors INTEGER DEFAULT 0,
    num_enums INTEGER DEFAULT 0,
    num_structs INTEGER DEFAULT 0,
    total_state_reads INTEGER DEFAULT 0,
    total_state_writes INTEGER DEFAULT 0,
    avg_state_reads_per_function FLOAT DEFAULT 0.0,
    avg_state_writes_per_function FLOAT DEFAULT 0.0,
    num_contracts_in_file INTEGER DEFAULT 0,

    -- Mathematical Aggregations (38 features)
    -- Ratios and Percentages
    high_confidence_ratio FLOAT DEFAULT 0.0,
    medium_confidence_ratio FLOAT DEFAULT 0.0,
    low_confidence_ratio FLOAT DEFAULT 0.0,
    high_severity_ratio FLOAT DEFAULT 0.0,
    medium_severity_ratio FLOAT DEFAULT 0.0,
    low_severity_ratio FLOAT DEFAULT 0.0,
    critical_to_total_ratio FLOAT DEFAULT 0.0,
    external_to_total_functions FLOAT DEFAULT 0.0,
    public_to_total_functions FLOAT DEFAULT 0.0,
    view_to_total_functions FLOAT DEFAULT 0.0,
    payable_to_total_functions FLOAT DEFAULT 0.0,
    state_reads_to_writes_ratio FLOAT DEFAULT 0.0,
    external_calls_to_functions_ratio FLOAT DEFAULT 0.0,

    -- Detector Category Counts
    security_detector_count INTEGER DEFAULT 0,
    optimization_detector_count INTEGER DEFAULT 0,
    best_practice_detector_count INTEGER DEFAULT 0,
    gas_detector_count INTEGER DEFAULT 0,
    reentrancy_detector_count INTEGER DEFAULT 0,
    access_control_detector_count INTEGER DEFAULT 0,
    arithmetic_detector_count INTEGER DEFAULT 0,

    -- Complexity Statistics
    complexity_variance FLOAT DEFAULT 0.0,
    high_complexity_function_count INTEGER DEFAULT 0,
    low_complexity_function_count INTEGER DEFAULT 0,
    avg_loc_per_function FLOAT DEFAULT 0.0,
    max_loc_per_function INTEGER DEFAULT 0,
    functions_with_comments_ratio FLOAT DEFAULT 0.0,

    -- Advanced Patterns
    recursive_call_count INTEGER DEFAULT 0,
    self_destruct_count INTEGER DEFAULT 0,
    create_contract_count INTEGER DEFAULT 0,
    if_node_count INTEGER DEFAULT 0,
    require_node_count INTEGER DEFAULT 0,
    assert_node_count INTEGER DEFAULT 0,
    assembly_node_count INTEGER DEFAULT 0,
    return_node_count INTEGER DEFAULT 0,

    -- Risk Patterns
    high_risk_pattern_count INTEGER DEFAULT 0,
    medium_risk_pattern_count INTEGER DEFAULT 0,
    low_risk_pattern_count INTEGER DEFAULT 0,
    vulnerability_density FLOAT DEFAULT 0.0,

    -- Constraints
    CONSTRAINT unique_contract_features UNIQUE (contract_id)
);

-- Index for faster joins
DROP INDEX IF EXISTS idx_features_contract_id;
CREATE INDEX idx_features_contract_id ON contract_features(contract_id);

-- ============================================================================
-- TABLE 3: vulnerability_labels (Ground Truth Labels)
-- ============================================================================
-- Stores ground truth vulnerability labels for training/evaluation
-- Supports multiple vulnerability types per contract
-- ============================================================================

CREATE TABLE vulnerability_labels (
    id SERIAL PRIMARY KEY,
    contract_id INTEGER NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,

    -- Vulnerability information
    vulnerability_type VARCHAR(100) NOT NULL,  -- e.g., 'reentrancy', 'access_control'
    is_vulnerable BOOLEAN DEFAULT FALSE,
    severity VARCHAR(20),  -- 'critical', 'high', 'medium', 'low'
    confidence FLOAT DEFAULT 0.0,  -- 0.0 to 1.0

    -- Source of label
    label_source VARCHAR(100),  -- e.g., 'smartbugs', 'manual_audit', 'slither'
    verified BOOLEAN DEFAULT FALSE,  -- Has label been manually verified?

    -- Additional context
    description TEXT,
    cwe_id VARCHAR(20),  -- Common Weakness Enumeration ID

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Prevent duplicate labels
    CONSTRAINT unique_vuln_label UNIQUE (contract_id, vulnerability_type, label_source)
);

-- Indexes
DROP INDEX IF EXISTS idx_labels_contract_id;
DROP INDEX IF EXISTS idx_labels_vuln_type;
DROP INDEX IF EXISTS idx_labels_is_vulnerable;

CREATE INDEX idx_labels_contract_id ON vulnerability_labels(contract_id);
CREATE INDEX idx_labels_vuln_type ON vulnerability_labels(vulnerability_type);
CREATE INDEX idx_labels_is_vulnerable ON vulnerability_labels(is_vulnerable);

-- ============================================================================
-- NOTE: Views removed for initial setup - can be added later if needed
-- Reason: Column name mismatches need to be resolved
-- ============================================================================

-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

-- Function to update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at on contracts table
DROP TRIGGER IF EXISTS update_contracts_updated_at ON contracts;
CREATE TRIGGER update_contracts_updated_at
    BEFORE UPDATE ON contracts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS: Documentation for future reference
-- ============================================================================

COMMENT ON TABLE contracts IS 'Contract metadata and extraction information';
COMMENT ON TABLE contract_features IS '152 features across 3 tiers (comprehensive mode)';
COMMENT ON TABLE vulnerability_labels IS 'Ground truth vulnerability labels for ML training';

COMMENT ON COLUMN contract_features.cei_violations IS 'Tier 2: Checks-Effects-Interactions pattern violations';
COMMENT ON COLUMN contract_features.cfg_num_cycles IS 'Tier 2: Control flow graph cycles (complexity indicator)';
COMMENT ON COLUMN contract_features.ir_highlevelcall_count IS 'Tier 3: SlithIR high-level call operations';
COMMENT ON COLUMN contract_features.vulnerability_density IS 'Tier 3: Vulnerabilities per 1000 lines of code';

-- ============================================================================
-- GRANTS: Set permissions (adjust for your setup)
-- ============================================================================

-- Grant all privileges to chainguardian_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO chainguardian_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO chainguardian_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO chainguardian_user;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ ChainGuardian AI Database Schema V2 created successfully!';
    RAISE NOTICE '📊 Tables: contracts, contract_features (152 features), vulnerability_labels';
    RAISE NOTICE '🎯 Ready for tier-based feature extraction';
END $$;
