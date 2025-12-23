# scripts/setup_database.py
"""
Database Setup & Migration Script

🎓 WHAT THIS DOES:
1. Creates database if not exists
2. Creates tables with proper schema
3. Creates indexes for performance
4. Can be run multiple times safely (idempotent)

USAGE:
poetry run python scripts/setup_database.py
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseSetup:
    """
    Production-ready database setup with migrations.
    
    🎓 Think of this like a Solidity constructor that runs once
    but can be upgraded with new schema versions
    """
    
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 5432,
                 database: str = "chainguardian",
                 user: str = "chainguardian_user",
                 password: str = "2220128"):
        self.config = {
            'host': host,
            'port': port,
            'user': user,
            'password': password
        }
        self.database = database
        
    def create_database(self):
        """Create database if it doesn't exist."""
        try:
            # Connect to postgres default database first
            conn = psycopg2.connect(**self.config, database='postgres')
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            cursor.execute(f"""
                SELECT 1 FROM pg_database WHERE datname = '{self.database}'
            """)
            exists = cursor.fetchone()
            
            if not exists:
                cursor.execute(f"CREATE DATABASE {self.database}")
                logger.info(f"✅ Created database: {self.database}")
            else:
                logger.info(f"✓ Database {self.database} already exists")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            raise
    
    def create_tables(self):
        """Create tables with full schema (93 features + semantic)."""
        conn = psycopg2.connect(**self.config, database=self.database)
        
        try:
            cursor = conn.cursor()
            
            # ============================================================
            # CONTRACTS TABLE (metadata)
            # ============================================================
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contracts (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    address VARCHAR(42),  -- Ethereum address (0x + 40 chars)
                    source_code TEXT,     -- Full source (optional, can be large)
                    compiler_version VARCHAR(20),
                    data_source VARCHAR(100),
                    file_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            logger.info("✓ Created contracts table")
            
            # ============================================================
            # FEATURES TABLE (89 features + semantic = 93 total)
            # ============================================================
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS features (
                    contract_id INTEGER PRIMARY KEY REFERENCES contracts(id) ON DELETE CASCADE,
                    
                    -- VULNERABILITY FLAGS (23)
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
                    
                    -- SEVERITY COUNTS (3)
                    high_severity_count INTEGER DEFAULT 0,
                    medium_severity_count INTEGER DEFAULT 0,
                    low_severity_count INTEGER DEFAULT 0,
                    
                    -- AST FEATURES (17)
                    num_functions INTEGER DEFAULT 0,
                    num_external_calls INTEGER DEFAULT 0,
                    num_state_vars INTEGER DEFAULT 0,
                    num_modifiers INTEGER DEFAULT 0,
                    max_cyclomatic_complexity INTEGER DEFAULT 0,
                    num_low_level_calls INTEGER DEFAULT 0,
                    lines_of_code INTEGER DEFAULT 0,
                    num_contracts_in_file INTEGER DEFAULT 1,
                    num_dependencies INTEGER DEFAULT 0,
                    avg_function_complexity REAL DEFAULT 0.0,
                    num_functions_high_complexity INTEGER DEFAULT 0,
                    num_comments INTEGER DEFAULT 0,
                    comment_to_code_ratio REAL DEFAULT 0.0,
                    num_payable_functions INTEGER DEFAULT 0,
                    num_library_calls INTEGER DEFAULT 0,
                    inheritance_depth INTEGER DEFAULT 0,
                    num_unused_functions INTEGER DEFAULT 0,
                    
                    -- DETECTOR STATISTICS (9)
                    high_confidence_detectors INTEGER DEFAULT 0,
                    medium_confidence_detectors INTEGER DEFAULT 0,
                    low_confidence_detectors INTEGER DEFAULT 0,
                    security_detectors_triggered INTEGER DEFAULT 0,
                    optimization_detectors_triggered INTEGER DEFAULT 0,
                    total_detector_hits INTEGER DEFAULT 0,
                    unique_vulnerability_types INTEGER DEFAULT 0,
                    detectors_per_function REAL DEFAULT 0.0,
                    detectors_per_loc REAL DEFAULT 0.0,
                    
                    -- RISK SCORES (4)
                    risk_score_simple REAL DEFAULT 0.0,
                    risk_score_weighted REAL DEFAULT 0.0,
                    is_high_risk BOOLEAN DEFAULT FALSE,
                    contract_complexity_category VARCHAR(20) DEFAULT 'simple',
                    complexity_level INTEGER DEFAULT 0,
                    
                    -- ERROR TRACKING (2)
                    failure_reason VARCHAR(50),
                    error_message TEXT,
                    
                    -- GRAPH FEATURES (25)
                    cfg_num_nodes INTEGER DEFAULT 0,
                    cfg_num_edges INTEGER DEFAULT 0,
                    cfg_num_cycles INTEGER DEFAULT 0,
                    cfg_max_depth INTEGER DEFAULT 0,
                    cfg_avg_branching REAL DEFAULT 0.0,
                    cfg_has_complex_loops BOOLEAN DEFAULT FALSE,
                    cfg_num_exit_points INTEGER DEFAULT 0,
                    cfg_cyclomatic_total INTEGER DEFAULT 0,
                    cg_num_nodes INTEGER DEFAULT 0,
                    cg_num_edges INTEGER DEFAULT 0,
                    cg_max_call_depth INTEGER DEFAULT 0,
                    cg_num_external_calls INTEGER DEFAULT 0,
                    cg_external_call_ratio REAL DEFAULT 0.0,
                    cg_has_cyclic_calls BOOLEAN DEFAULT FALSE,
                    cg_num_public_entry_points INTEGER DEFAULT 0,
                    cg_num_internal_functions INTEGER DEFAULT 0,
                    cg_avg_calls_per_function REAL DEFAULT 0.0,
                    cg_num_leaf_functions INTEGER DEFAULT 0,
                    dfg_num_state_vars INTEGER DEFAULT 0,
                    dfg_num_tainted_flows INTEGER DEFAULT 0,
                    dfg_has_cross_function_flow BOOLEAN DEFAULT FALSE,
                    dfg_num_sensitive_sinks INTEGER DEFAULT 0,
                    dfg_num_external_sources INTEGER DEFAULT 0,
                    dfg_taint_to_sink_ratio REAL DEFAULT 0.0,
                    dfg_num_unvalidated_inputs INTEGER DEFAULT 0,
                    
                    -- SEMANTIC SECURITY FEATURES (8)
                    cei_violations INTEGER DEFAULT 0,
                    cei_safe_functions INTEGER DEFAULT 0,
                    cei_pattern_score REAL DEFAULT 1.0,
                    has_reentrancy_guard BOOLEAN DEFAULT FALSE,
                    functions_with_reentrancy_guard INTEGER DEFAULT 0,
                    state_before_call_count INTEGER DEFAULT 0,
                    state_after_call_count INTEGER DEFAULT 0,
                    unchecked_calls_in_critical_context INTEGER DEFAULT 0,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            logger.info("✓ Created features table (93 fields)")
            
            # ============================================================
            # LABELS TABLE (ground truth)
            # ============================================================
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS labels (
                    id SERIAL PRIMARY KEY,
                    contract_id INTEGER REFERENCES contracts(id) ON DELETE CASCADE,
                    vulnerability_type VARCHAR(100),
                    has_vulnerability BOOLEAN,
                    confidence REAL DEFAULT 1.0,
                    severity VARCHAR(20),
                    source VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(contract_id, vulnerability_type, source)
                );
            """)
            logger.info("✓ Created labels table")
            
            # ============================================================
            # INDEXES FOR PERFORMANCE
            # ============================================================
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_contracts_name ON contracts(name);
                CREATE INDEX IF NOT EXISTS idx_contracts_address ON contracts(address);
                CREATE INDEX IF NOT EXISTS idx_contracts_data_source ON contracts(data_source);
                CREATE INDEX IF NOT EXISTS idx_features_contract_id ON features(contract_id);
                CREATE INDEX IF NOT EXISTS idx_features_has_reentrancy ON features(has_reentrancy) WHERE has_reentrancy = TRUE;
                CREATE INDEX IF NOT EXISTS idx_features_cei_violations ON features(cei_violations) WHERE cei_violations > 0;
                CREATE INDEX IF NOT EXISTS idx_labels_contract_id ON labels(contract_id);
                CREATE INDEX IF NOT EXISTS idx_labels_vulnerability_type ON labels(vulnerability_type);
            """)
            logger.info("✓ Created performance indexes")
            
            conn.commit()
            logger.info("✅ Database setup complete!")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Setup failed: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

def main():
    """Run full database setup."""
    setup = DatabaseSetup()
    
    print("🔧 DATABASE SETUP & MIGRATION")
    print("="*50)
    
    setup.create_database()
    setup.create_tables()
    
    print("\n✅ Setup complete! Database ready for production.")

if __name__ == "__main__":
    main()
