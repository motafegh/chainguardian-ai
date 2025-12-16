"""
Create database tables for ChainGuardian AI

🎓 This is like deploying smart contracts
We're defining the data structure that will store our contracts and features
"""

import psycopg2
from psycopg2 import sql

# Database connection details
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'chainguardian',
    'user': 'chainguardian_user',
    'password': '2220128'
}

def create_tables():
    """
    Create three tables:
    1. contracts - Store smart contract metadata
    2. features - Store extracted features (linked to contracts)
    3. labels - Store vulnerability labels (linked to contracts)
    
    🎓 Relationships:
    contracts (1) ─→ (many) features
    contracts (1) ─→ (many) labels
    
    Similar to Solidity:
    mapping(uint256 contractId => Contract) contracts;
    mapping(uint256 contractId => Feature[]) features;
    """
    
    # Connect to database
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("📊 Creating tables...")
    
    # ================================================================
    # TABLE 1: CONTRACTS
    # ================================================================
    # Stores basic contract information
    # 🎓 This is your main "Contract" struct
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            id SERIAL PRIMARY KEY,
            address VARCHAR(42) UNIQUE NOT NULL,
            name TEXT NOT NULL,
            source_code TEXT,
            compiler_version VARCHAR(50),
            source VARCHAR(50),
            file_path TEXT,
            collected_at TIMESTAMP DEFAULT NOW()
        );
    """)
    print("✅ Created table: contracts")
    
    # ================================================================
    # TABLE 2: FEATURES
    # ================================================================
    # Stores extracted features for each contract
    # 🎓 One contract can have many features
    # This is your feature vector for ML
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS features (
            id SERIAL PRIMARY KEY,
            contract_id INTEGER REFERENCES contracts(id) ON DELETE CASCADE,
            
            -- Vulnerability indicators (from Slither)
            has_reentrancy BOOLEAN DEFAULT FALSE,
            has_access_control_issues BOOLEAN DEFAULT FALSE,
            has_timestamp_dependency BOOLEAN DEFAULT FALSE,
            has_unchecked_call BOOLEAN DEFAULT FALSE,
            high_severity_count INTEGER DEFAULT 0,
            medium_severity_count INTEGER DEFAULT 0,
            low_severity_count INTEGER DEFAULT 0,
            
            -- Code structure metrics (from AST)
            num_functions INTEGER DEFAULT 0,
            num_external_calls INTEGER DEFAULT 0,
            num_state_vars INTEGER DEFAULT 0,
            num_modifiers INTEGER DEFAULT 0,
            max_cyclomatic_complexity INTEGER DEFAULT 0,
            num_low_level_calls INTEGER DEFAULT 0,
            
            -- Extraction metadata
            extracted_at TIMESTAMP DEFAULT NOW(),
            failure_reason TEXT,
            error_message TEXT
        );
    """)
    print("✅ Created table: features")
    
    # ================================================================
    # TABLE 3: LABELS (for training)
    # ================================================================
    # Stores ground truth vulnerability labels
    # 🎓 Multi-label: one contract can have multiple vulnerability types
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS labels (
            id SERIAL PRIMARY KEY,
            contract_id INTEGER REFERENCES contracts(id) ON DELETE CASCADE,
            vulnerability_type VARCHAR(50) NOT NULL,
            has_vulnerability BOOLEAN NOT NULL,
            severity VARCHAR(20),
            source VARCHAR(50),
            labeled_at TIMESTAMP DEFAULT NOW(),
            
            UNIQUE(contract_id, vulnerability_type, source)
        );
    """)
    print("✅ Created table: labels")
    
    # ================================================================
    # CREATE INDEXES (for fast queries)
    # ================================================================
    # 🎓 Indexes are like book indexes - speed up searches
    # Similar to how Solidity mappings give O(1) lookup
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_contracts_address 
        ON contracts(address);
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_features_contract 
        ON features(contract_id);
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_labels_contract 
        ON labels(contract_id);
    """)
    
    print("✅ Created indexes for fast queries")
    
    # Commit changes (🎓 like transaction.wait() - makes changes permanent)
    conn.commit()
    
    # Close connections
    cursor.close()
    conn.close()
    
    print("\n🎉 All tables created successfully!")
    print("\n📊 Table Structure:")
    print("   contracts (id, address, name, source_code, ...)")
    print("   features (id, contract_id, has_reentrancy, num_functions, ...)")
    print("   labels (id, contract_id, vulnerability_type, has_vulnerability, ...)")
    print("\n✅ Database is ready to use!")

if __name__ == "__main__":
    create_tables()