"""
Aggressive Feature Expansion - Add 40+ new columns to features table.

🎯 PURPOSE: Expand from 15 → 55+ features for state-of-art ML accuracy

🎓 LEARNING: Database migrations in production
- Always check if column exists before adding (idempotent)
- Always use DEFAULT values (so existing rows don't break)
- Always commit incrementally (rollback on failure)
- Always log every change (audit trail)

Run once:
    poetry run python scripts/database/expand_features_aggressive.py

Author: Ali - ChainGuardian AI Project
Day: 4
"""

import psycopg2
import logging
from typing import List, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_new_columns() -> List[Tuple[str, str, str]]:
    """
    Define all new columns to add.
    
    Returns:
        List of (column_name, data_type, description) tuples
    """
    
    columns = []
    
    # ================================================================
    # GROUP 1: REENTRANCY VARIANTS (3 new columns)
    # ================================================================
    # 🎓 WHY SEPARATE: Different ML signal strength
    # - reentrancy-eth: CRITICAL (steals Ether)
    # - reentrancy-events: MEDIUM (out-of-order events)
    
    columns.extend([
        ('has_reentrancy_unlimited', 'BOOLEAN DEFAULT FALSE', 
         'Reentrancy with unlimited gas forwarding'),
        ('has_reentrancy_benign', 'BOOLEAN DEFAULT FALSE',
         'Benign reentrancy (read-only)'),
        ('has_reentrancy_events', 'BOOLEAN DEFAULT FALSE',
         'Reentrancy affecting event ordering'),
    ])
    
    # ================================================================
    # GROUP 2: DELEGATECALL ISSUES (2 new columns)
    # ================================================================
    # 🎓 DELEGATECALL: Most dangerous Solidity feature
    # Executes code in caller's context (can hijack storage!)
    
    columns.extend([
        ('has_controlled_delegatecall', 'BOOLEAN DEFAULT FALSE',
         'User-controlled delegatecall target'),
        ('has_delegatecall_loop', 'BOOLEAN DEFAULT FALSE',
         'Delegatecall inside loop (gas + reentrancy risk)'),
    ])
    
    # ================================================================
    # GROUP 3: UNINITIALIZED VARIABLES (3 new columns)
    # ================================================================
    # 🎓 SOLIDITY GOTCHA: Uninitialized vars default to 0
    # Can lead to unexpected behavior (address(0), empty strings)
    
    columns.extend([
        ('has_uninitialized_state', 'BOOLEAN DEFAULT FALSE',
         'Uninitialized state variable used'),
        ('has_uninitialized_storage', 'BOOLEAN DEFAULT FALSE',
         'Uninitialized storage pointer'),
        ('has_uninitialized_local', 'BOOLEAN DEFAULT FALSE',
         'Uninitialized local variable'),
    ])
    
    # ================================================================
    # GROUP 4: DANGEROUS LOW-LEVEL OPERATIONS (5 new columns)
    # ================================================================
    
    columns.extend([
        ('has_unchecked_transfer', 'BOOLEAN DEFAULT FALSE',
         'ERC20 transfer return value not checked'),
        ('has_msg_value_loop', 'BOOLEAN DEFAULT FALSE',
         'msg.value used in loop (dangerous!)'),
        ('has_tx_origin', 'BOOLEAN DEFAULT FALSE',
         'Uses tx.origin for authentication'),
        ('has_inline_assembly', 'BOOLEAN DEFAULT FALSE',
         'Contains inline assembly'),
        ('has_locked_ether', 'BOOLEAN DEFAULT FALSE',
         'Contract can receive but not withdraw Ether'),
    ])
    
    # ================================================================
    # GROUP 5: SHADOWING & NAMING ISSUES (3 new columns)
    # ================================================================
    # 🎓 SHADOWING: Local var has same name as state var (confusing!)
    
    columns.extend([
        ('has_shadowing_state', 'BOOLEAN DEFAULT FALSE',
         'Local variable shadows state variable'),
        ('has_shadowing_builtin', 'BOOLEAN DEFAULT FALSE',
         'Variable shadows built-in (e.g., "now", "assert")'),
        ('has_shadowing_abstract', 'BOOLEAN DEFAULT FALSE',
         'Function shadows inherited function'),
    ])
    
    # ================================================================
    # GROUP 6: COMPILER & PRAGMA ISSUES (3 new columns)
    # ================================================================
    
    columns.extend([
        ('has_incorrect_solc_version', 'BOOLEAN DEFAULT FALSE',
         'Using old/buggy compiler version'),
        ('has_floating_pragma', 'BOOLEAN DEFAULT FALSE',
         'Pragma allows multiple versions (^0.8.0)'),
        ('has_outdated_compiler', 'BOOLEAN DEFAULT FALSE',
         'Compiler version < 0.8.0 (missing safety features)'),
    ])
    
    # ================================================================
    # GROUP 7: UNUSED CODE (3 new columns)
    # ================================================================
    # 🎓 UNUSED CODE: Dead code increases complexity, no security value
    
    columns.extend([
        ('has_unused_state_vars', 'BOOLEAN DEFAULT FALSE',
         'State variables never used'),
        ('has_unused_return_values', 'BOOLEAN DEFAULT FALSE',
         'Function return values ignored'),
        ('num_unused_functions', 'INTEGER DEFAULT 0',
         'Count of unused internal functions'),
    ])
    
    # ================================================================
    # GROUP 8: CODE QUALITY METRICS (10 new columns)
    # ================================================================
    # 🎓 RESEARCH INSIGHT: Code metrics correlate with vulnerabilities
    # Study: "Contracts with >500 LOC have 3x more bugs"
    
    columns.extend([
        # Size metrics
        ('lines_of_code', 'INTEGER DEFAULT 0',
         'Total lines of Solidity code'),
        ('num_contracts_in_file', 'INTEGER DEFAULT 1',
         'Number of contracts in .sol file'),
        ('num_dependencies', 'INTEGER DEFAULT 0',
         'Number of import statements'),
        
        # Complexity metrics (beyond what we have)
        ('avg_function_complexity', 'REAL DEFAULT 0',
         'Average cyclomatic complexity across functions'),
        ('num_functions_high_complexity', 'INTEGER DEFAULT 0',
         'Functions with complexity > 10'),
        
        # Documentation metrics
        ('num_comments', 'INTEGER DEFAULT 0',
         'Count of comment lines'),
        ('comment_to_code_ratio', 'REAL DEFAULT 0',
         'Comments / Code lines ratio'),
        
        # Advanced AST metrics
        ('num_payable_functions', 'INTEGER DEFAULT 0',
         'Functions that accept Ether'),
        ('num_library_calls', 'INTEGER DEFAULT 0',
         'Calls to external libraries'),
        ('inheritance_depth', 'INTEGER DEFAULT 0',
         'How many levels of inheritance'),
    ])
    
    # ================================================================
    # GROUP 9: DETECTOR STATISTICS (9 new columns)
    # ================================================================
    # 🎓 AGGREGATE FEATURES: Combine detector outputs for ML signal
    
    columns.extend([
        # Detector counts by confidence
        ('high_confidence_detectors', 'INTEGER DEFAULT 0',
         'Detectors with high confidence'),
        ('medium_confidence_detectors', 'INTEGER DEFAULT 0',
         'Detectors with medium confidence'),
        ('low_confidence_detectors', 'INTEGER DEFAULT 0',
         'Detectors with low confidence'),
        
        # Detector counts by category
        ('security_detectors_triggered', 'INTEGER DEFAULT 0',
         'Count of security-critical detectors'),
        ('optimization_detectors_triggered', 'INTEGER DEFAULT 0',
         'Count of gas optimization detectors'),
        
        # Total counts
        ('total_detector_hits', 'INTEGER DEFAULT 0',
         'Total number of detectors triggered'),
        ('unique_vulnerability_types', 'INTEGER DEFAULT 0',
         'Count of unique vulnerability categories'),
        
        # Ratios (normalized by contract size)
        ('detectors_per_function', 'REAL DEFAULT 0',
         'Total detectors / Number of functions'),
        ('detectors_per_loc', 'REAL DEFAULT 0',
         'Total detectors / Lines of code'),
    ])
    
    # ================================================================
    # GROUP 10: COMPOSITE RISK SCORES (4 new columns)
    # ================================================================
    # 🎓 PRE-COMPUTED FEATURES: Help ML model learn faster
    
    columns.extend([
        ('risk_score_simple', 'REAL DEFAULT 0',
         'Simple: high*10 + medium*5 + low'),
        ('risk_score_weighted', 'REAL DEFAULT 0',
         'Weighted by confidence and severity'),
        ('is_high_risk', 'BOOLEAN DEFAULT FALSE',
         'True if risk_score > threshold'),
        ('contract_complexity_category', 'VARCHAR(20) DEFAULT \'simple\'',
         'simple/moderate/complex/critical'),
    ])
    
    return columns


def expand_features_table():
    """
    Execute database migration to add 40+ new columns.
    
    🎓 PRODUCTION PATTERN: Transactional migration
    - All changes in one transaction
    - Rollback if any failure
    - Log every step
    """
    
    conn = psycopg2.connect(
        host="localhost",
        database="chainguardian",
        user="chainguardian_user",
        password="2220128"
    )
    
    cursor = conn.cursor()
    
    try:
        logger.info("=" * 70)
        logger.info("STARTING AGGRESSIVE FEATURE EXPANSION")
        logger.info("=" * 70)
        
        # Get all new columns
        new_columns = get_new_columns()
        
        added_count = 0
        skipped_count = 0
        
        for column_name, data_type, description in new_columns:
            # ============================================================
            # CHECK IF COLUMN EXISTS (Idempotent operation)
            # ============================================================
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='features' AND column_name=%s;
            """, (column_name,))
            
            if cursor.fetchone():
                logger.info(f"⏭️  {column_name}: already exists")
                skipped_count += 1
                continue
            
            # ============================================================
            # ADD COLUMN
            # ============================================================
            sql = f"ALTER TABLE features ADD COLUMN {column_name} {data_type};"
            
            logger.info(f"➕ Adding: {column_name}")
            logger.debug(f"   Type: {data_type}")
            logger.debug(f"   Purpose: {description}")
            
            cursor.execute(sql)
            added_count += 1
        
        # ============================================================
        # COMMIT ALL CHANGES
        # ============================================================
        conn.commit()
        
        logger.info("=" * 70)
        logger.info(f"✅ MIGRATION COMPLETE")
        logger.info(f"   Added: {added_count} columns")
        logger.info(f"   Skipped: {skipped_count} columns (already exist)")
        logger.info(f"   Total features now: {15 + added_count}")
        logger.info("=" * 70)
        
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ MIGRATION FAILED: {e}")
        logger.error("All changes rolled back")
        raise
    
    finally:
        cursor.close()
        conn.close()


def print_schema_summary():
    """Print current schema for verification."""
    
    conn = psycopg2.connect(
        host="localhost",
        database="chainguardian",
        user="chainguardian_user",
        password="2220128"
    )
    
    cursor = conn.cursor()
    
    try:
        # Get all columns from features table
        cursor.execute("""
            SELECT 
                column_name, 
                data_type,
                column_default
            FROM information_schema.columns 
            WHERE table_name = 'features'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        
        logger.info("\n" + "=" * 70)
        logger.info("CURRENT FEATURES TABLE SCHEMA")
        logger.info("=" * 70)
        
        # Group by category
        vulnerability_flags = []
        counts = []
        metrics = []
        errors = []
        other = []
        
        for col_name, col_type, col_default in columns:
            if col_name.startswith('has_'):
                vulnerability_flags.append(col_name)
            elif col_name.endswith('_count') or col_name.startswith('num_'):
                counts.append(col_name)
            elif col_type in ['double precision', 'real']:
                metrics.append(col_name)
            elif 'error' in col_name or 'failure' in col_name:
                errors.append(col_name)
            else:
                other.append(col_name)
        
        logger.info(f"\n📊 SUMMARY:")
        logger.info(f"   Vulnerability Flags (boolean): {len(vulnerability_flags)}")
        logger.info(f"   Count Features (integer): {len(counts)}")
        logger.info(f"   Metric Features (float): {len(metrics)}")
        logger.info(f"   Error Tracking: {len(errors)}")
        logger.info(f"   Other: {len(other)}")
        logger.info(f"   ───────────────────────────")
        logger.info(f"   TOTAL FEATURES: {len(columns)}")
        
        logger.info(f"\n🎯 VULNERABILITY FLAGS ({len(vulnerability_flags)}):")
        for flag in sorted(vulnerability_flags):
            logger.info(f"   ✓ {flag}")
        
        logger.info(f"\n📈 COUNT FEATURES ({len(counts)}):")
        for count in sorted(counts):
            logger.info(f"   ✓ {count}")
        
        logger.info(f"\n📊 METRIC FEATURES ({len(metrics)}):")
        for metric in sorted(metrics):
            logger.info(f"   ✓ {metric}")
        
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    """
    Main execution.
    
    🎓 USAGE:
        poetry run python scripts/database/expand_features_aggressive.py
    
    🎓 SAFETY:
        - Idempotent: Safe to run multiple times
        - Transactional: Rolls back on failure
        - Non-destructive: Only adds columns, never removes
    """
    
    try:
        expand_features_table()
        print_schema_summary()
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ NEXT STEPS:")
        logger.info("=" * 70)
        logger.info("1. Update contract_analyzer.py (expand DETECTOR_MAPPING)")
        logger.info("2. Update ContractFeatures dataclass (add fields)")
        logger.info("3. Update DatabaseManager (expand save/get methods)")
        logger.info("4. Re-analyze all contracts with new features")
        logger.info("=" * 70 + "\n")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        exit(1)
