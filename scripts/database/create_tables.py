"""
Create database tables for ChainGuardian AI - PRODUCTION VERSION

🎓 This defines the complete schema for 85 features + ground truth labels
"""

import psycopg2
from psycopg2 import sql

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'chainguardian',
    'user': 'chainguardian_user',
    'password': '2220128'
}

def create_tables():
    """
    Create three tables with complete schema:
    1. contracts - Smart contract metadata
    2. features - 85 extracted features
    3. labels - Ground truth vulnerability labels
    """
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("📊 Creating tables...")
    
    # ================================================================
    # TABLE 1: CONTRACTS (Fixed - no 'source' column)
    # ================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            id SERIAL PRIMARY KEY,
            address VARCHAR(42),  -- Nullable for undeployed contracts
            name TEXT NOT NULL,
            source_code TEXT,
            compiler_version VARCHAR(50),
            data_source VARCHAR(50),  -- 'smartbugs_curated', 'openzeppelin'
            file_path TEXT,
            collected_at TIMESTAMP DEFAULT NOW()
        );
    """)
    print("✅ Created table: contracts")
    
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_contracts_address_not_null 
        ON contracts(address) WHERE address IS NOT NULL;
    """)
    
    # ================================================================
    # TABLE 2: FEATURES (Complete 85 features!)
    # ================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS features (
            id SERIAL PRIMARY KEY,
            contract_id INTEGER REFERENCES contracts(id) ON DELETE CASCADE,
            
            -- Vulnerability flags (23)
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
            
            -- Severity counts (3)
            high_severity_count INTEGER DEFAULT 0,
            medium_severity_count INTEGER DEFAULT 0,
            low_severity_count INTEGER DEFAULT 0,
            
            -- AST features (17)
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
            
            -- Detector statistics (9)
            high_confidence_detectors INTEGER DEFAULT 0,
            medium_confidence_detectors INTEGER DEFAULT 0,
            low_confidence_detectors INTEGER DEFAULT 0,
            security_detectors_triggered INTEGER DEFAULT 0,
            optimization_detectors_triggered INTEGER DEFAULT 0,
            total_detector_hits INTEGER DEFAULT 0,
            unique_vulnerability_types INTEGER DEFAULT 0,
            detectors_per_function FLOAT DEFAULT 0.0,
            detectors_per_loc FLOAT DEFAULT 0.0,
            
            -- Risk scores (4)
            risk_score_simple FLOAT DEFAULT 0.0,
            risk_score_weighted FLOAT DEFAULT 0.0,
            is_high_risk BOOLEAN DEFAULT FALSE,
            contract_complexity_category VARCHAR(20) DEFAULT 'simple',
            
            -- Graph features: CFG (8)
            cfg_num_nodes INTEGER DEFAULT 0,
            cfg_num_edges INTEGER DEFAULT 0,
            cfg_num_cycles INTEGER DEFAULT 0,
            cfg_max_depth INTEGER DEFAULT 0,
            cfg_avg_branching FLOAT DEFAULT 0.0,
            cfg_has_complex_loops BOOLEAN DEFAULT FALSE,
            cfg_num_exit_points INTEGER DEFAULT 0,
            cfg_cyclomatic_total INTEGER DEFAULT 0,
            
            -- Graph features: Call Graph (10)
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
            
            -- Graph features: Data Flow (7)
            dfg_num_state_vars INTEGER DEFAULT 0,
            dfg_num_tainted_flows INTEGER DEFAULT 0,
            dfg_has_cross_function_flow BOOLEAN DEFAULT FALSE,
            dfg_num_sensitive_sinks INTEGER DEFAULT 0,
            dfg_num_external_sources INTEGER DEFAULT 0,
            dfg_taint_to_sink_ratio FLOAT DEFAULT 0.0,
            dfg_num_unvalidated_inputs INTEGER DEFAULT 0,
            
            -- Error tracking (2)
            failure_reason TEXT,
            error_message TEXT,
            
            extracted_at TIMESTAMP DEFAULT NOW()
        );
    """)
    print("✅ Created table: features (85 columns)")
    
    # ================================================================
    # TABLE 3: LABELS
    # ================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS labels (
            id SERIAL PRIMARY KEY,
            contract_id INTEGER REFERENCES contracts(id) ON DELETE CASCADE,
            vulnerability_type VARCHAR(100) NOT NULL,
            has_vulnerability BOOLEAN NOT NULL,
            confidence FLOAT DEFAULT 1.0,
            source VARCHAR(50),  -- 'smartbugs_curated', 'openzeppelin'
            labeled_at TIMESTAMP DEFAULT NOW()
        );
    """)
    print("✅ Created table: labels")
    
    # ================================================================
    # INDEXES
    # ================================================================
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_contracts_address ON contracts(address);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_features_contract ON features(contract_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_labels_contract ON labels(contract_id);")
    
    print("✅ Created indexes for fast queries")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n🎉 All tables created successfully!")
    print("\n📊 Table Structure:")
    print("   contracts: 8 columns")
    print("   features: 87 columns (85 features + id + contract_id)")
    print("   labels: 7 columns")
    print("\n✅ Database is ready to use!")

if __name__ == "__main__":
    create_tables()
