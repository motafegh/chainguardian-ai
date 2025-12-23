-- ============================================================================
-- ChainGuardian Database Schema - December 22, 2025
-- Complete schema for ML-ready smart contract security analysis
-- ============================================================================

-- Drop existing tables (CASCADE removes dependent data)
DROP TABLE IF EXISTS labels CASCADE;
DROP TABLE IF EXISTS features CASCADE;
DROP TABLE IF EXISTS contracts CASCADE;

-- ============================================================================
-- CONTRACTS TABLE (7 columns)
-- ============================================================================
CREATE TABLE contracts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address VARCHAR(42),  -- Ethereum address (0x + 40 hex chars)
    source_code TEXT,     -- Optional: full source code
    compiler_version VARCHAR(20),
    data_source VARCHAR(50) NOT NULL,  -- openzeppelin, smartbugs, etc.
    file_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- FEATURES TABLE (93 columns: 90 features + 3 metadata)
-- ============================================================================
CREATE TABLE features (
    id SERIAL PRIMARY KEY,
    contract_id INTEGER NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    
    -- ========================================================================
    -- VULNERABILITY FLAGS (25 boolean columns)
    -- ========================================================================
    has_reentrancy BOOLEAN DEFAULT FALSE,
    has_access_control_issues BOOLEAN DEFAULT FALSE,
    has_timestamp_dependency BOOLEAN DEFAULT FALSE,
    has_unchecked_call BOOLEAN DEFAULT FALSE,
    has_reentrancy_unlimited BOOLEAN DEFAULT FALSE,
    has_reentrancy_benign BOOLEAN DEFAULT FALSE,
    has_reentrancy_events BOOLEAN DEFAULT FALSE,
    has_unchecked_transfer BOOLEAN DEFAULT FALSE,
    has_controlled_delegatecall BOOLEAN DEFAULT FALSE,
    has_delegatecall_loop BOOLEAN DEFAULT FALSE,
    has_uninitialized_state BOOLEAN DEFAULT FALSE,
    has_uninitialized_storage BOOLEAN DEFAULT FALSE,
    has_uninitialized_local BOOLEAN DEFAULT FALSE,
    has_tx_origin BOOLEAN DEFAULT FALSE,
    has_inline_assembly BOOLEAN DEFAULT FALSE,
    has_locked_ether BOOLEAN DEFAULT FALSE,
    has_msg_value_loop BOOLEAN DEFAULT FALSE,
    has_shadowing_state BOOLEAN DEFAULT FALSE,
    has_shadowing_builtin BOOLEAN DEFAULT FALSE,
    has_shadowing_abstract BOOLEAN DEFAULT FALSE,
    has_unused_state_vars BOOLEAN DEFAULT FALSE,
    has_unused_return_values BOOLEAN DEFAULT FALSE,
    has_incorrect_solc_version BOOLEAN DEFAULT FALSE,
    has_floating_pragma BOOLEAN DEFAULT FALSE,
    has_outdated_compiler BOOLEAN DEFAULT FALSE,
    
    -- ========================================================================
    -- SEVERITY COUNTS (3 integer columns)
    -- ========================================================================
    high_severity_count INTEGER DEFAULT 0,
    medium_severity_count INTEGER DEFAULT 0,
    low_severity_count INTEGER DEFAULT 0,
    
    -- ========================================================================
    -- AST FEATURES (17 numeric columns)
    -- ========================================================================
    num_functions INTEGER DEFAULT 0,
    num_external_calls INTEGER DEFAULT 0,
    num_state_vars INTEGER DEFAULT 0,
    num_modifiers INTEGER DEFAULT 0,
    max_cyclomatic_complexity INTEGER DEFAULT 0,
    num_low_level_calls INTEGER DEFAULT 0,
    lines_of_code INTEGER DEFAULT 0,
    num_contracts_in_file INTEGER DEFAULT 1,
    num_dependencies INTEGER DEFAULT 0,
    avg_function_complexity FLOAT DEFAULT 0.0,
    num_functions_high_complexity INTEGER DEFAULT 0,
    num_comments INTEGER DEFAULT 0,
    comment_to_code_ratio FLOAT DEFAULT 0.0,
    num_payable_functions INTEGER DEFAULT 0,
    num_library_calls INTEGER DEFAULT 0,
    inheritance_depth INTEGER DEFAULT 0,
    num_unused_functions INTEGER DEFAULT 0,
    
    -- ========================================================================
    -- DETECTOR STATISTICS (9 numeric columns)
    -- ========================================================================
    high_confidence_detectors INTEGER DEFAULT 0,
    medium_confidence_detectors INTEGER DEFAULT 0,
    low_confidence_detectors INTEGER DEFAULT 0,
    security_detectors_triggered INTEGER DEFAULT 0,
    optimization_detectors_triggered INTEGER DEFAULT 0,
    total_detector_hits INTEGER DEFAULT 0,
    unique_vulnerability_types INTEGER DEFAULT 0,
    detectors_per_function FLOAT DEFAULT 0.0,
    detectors_per_loc FLOAT DEFAULT 0.0,
    
    -- ========================================================================
    -- RISK SCORES (5 columns: 2 float, 1 boolean, 2 text)
    -- ========================================================================
    risk_score_simple FLOAT DEFAULT 0.0,
    risk_score_weighted FLOAT DEFAULT 0.0,
    is_high_risk BOOLEAN DEFAULT FALSE,
    contract_complexity_category VARCHAR(20) DEFAULT 'simple',
    complexity_level INTEGER DEFAULT 0,
    
    -- ========================================================================
    -- ERROR TRACKING (2 text columns)
    -- ========================================================================
    failure_reason VARCHAR(50),
    error_message TEXT,
    
    -- ========================================================================
    -- GRAPH FEATURES - CFG (8 columns)
    -- ========================================================================
    cfg_num_nodes INTEGER DEFAULT 0,
    cfg_num_edges INTEGER DEFAULT 0,
    cfg_num_cycles INTEGER DEFAULT 0,
    cfg_max_depth INTEGER DEFAULT 0,
    cfg_avg_branching FLOAT DEFAULT 0.0,
    cfg_has_complex_loops BOOLEAN DEFAULT FALSE,
    cfg_num_exit_points INTEGER DEFAULT 0,
    cfg_cyclomatic_total INTEGER DEFAULT 0,
    
    -- ========================================================================
    -- GRAPH FEATURES - CALL GRAPH (10 columns)
    -- ========================================================================
    cg_num_nodes INTEGER DEFAULT 0,
    cg_num_edges INTEGER DEFAULT 0,
    cg_max_call_depth INTEGER DEFAULT 0,
    cg_num_external_calls INTEGER DEFAULT 0,
    cg_external_call_ratio FLOAT DEFAULT 0.0,
    cg_has_cyclic_calls BOOLEAN DEFAULT FALSE,
    cg_num_public_entry_points INTEGER DEFAULT 0,
    cg_num_internal_functions INTEGER DEFAULT 0,
    cg_avg_calls_per_function FLOAT DEFAULT 0.0,
    cg_num_leaf_functions INTEGER DEFAULT 0,
    
    -- ========================================================================
    -- GRAPH FEATURES - DATA FLOW (7 columns)
    -- ========================================================================
    dfg_num_state_vars INTEGER DEFAULT 0,
    dfg_num_tainted_flows INTEGER DEFAULT 0,
    dfg_has_cross_function_flow BOOLEAN DEFAULT FALSE,
    dfg_num_sensitive_sinks INTEGER DEFAULT 0,
    dfg_num_external_sources INTEGER DEFAULT 0,
    dfg_taint_to_sink_ratio FLOAT DEFAULT 0.0,
    dfg_num_unvalidated_inputs INTEGER DEFAULT 0,
    
    -- ========================================================================
    -- SEMANTIC SECURITY FEATURES (8 columns)
    -- ========================================================================
    cei_violations INTEGER DEFAULT 0,
    cei_safe_functions INTEGER DEFAULT 0,
    cei_pattern_score FLOAT DEFAULT 1.0,
    has_reentrancy_guard BOOLEAN DEFAULT FALSE,
    functions_with_reentrancy_guard INTEGER DEFAULT 0,
    state_before_call_count INTEGER DEFAULT 0,
    state_after_call_count INTEGER DEFAULT 0,
    unchecked_calls_in_critical_context INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- LABELS TABLE (for ground truth)
-- ============================================================================
CREATE TABLE labels (
    id SERIAL PRIMARY KEY,
    contract_id INTEGER NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    vulnerability_type VARCHAR(100) NOT NULL,
    has_vulnerability BOOLEAN DEFAULT TRUE,
    severity VARCHAR(20),  -- high, medium, low
    confidence FLOAT DEFAULT 1.0,
    source VARCHAR(50) NOT NULL,  -- smartbugs_curated, manual, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(contract_id, vulnerability_type, source)
);

-- ============================================================================
-- INDEXES (for query performance)
-- ============================================================================
CREATE INDEX idx_contracts_data_source ON contracts(data_source);
CREATE INDEX idx_contracts_name ON contracts(name);
CREATE INDEX idx_features_contract_id ON features(contract_id);
CREATE INDEX idx_features_has_reentrancy ON features(has_reentrancy);
CREATE INDEX idx_features_cei_violations ON features(cei_violations);
CREATE INDEX idx_labels_contract_id ON labels(contract_id);
CREATE INDEX idx_labels_has_vulnerability ON labels(has_vulnerability);

-- ============================================================================
-- VERIFICATION: Count columns
-- ============================================================================
-- Expected:
--   contracts: 8 columns (including id, created_at)
--   features: 95 columns (including id, contract_id, created_at)
--   labels: 8 columns (including id, created_at)
