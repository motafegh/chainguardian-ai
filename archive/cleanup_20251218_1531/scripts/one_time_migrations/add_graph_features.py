"""
Add 25 graph feature columns to existing features table.
Safe migration - preserves existing data.
"""
import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_graph_feature_columns():
    """Add 25 new columns for graph features."""
    
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="chainguardian",
        user="chainguardian_user",
        password="2220128"
    )
    
    cursor = conn.cursor()
    
    try:
        logger.info("Adding graph feature columns...")
        
        # ============================================================
        # CFG FEATURES (8 columns)
        # ============================================================
        cursor.execute("""
            ALTER TABLE features
            ADD COLUMN IF NOT EXISTS cfg_num_nodes INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS cfg_num_edges INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS cfg_num_cycles INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS cfg_max_depth INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS cfg_avg_branching FLOAT DEFAULT 0.0,
            ADD COLUMN IF NOT EXISTS cfg_has_complex_loops BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS cfg_num_exit_points INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS cfg_cyclomatic_total INTEGER DEFAULT 0;
        """)
        
        # ============================================================
        # CALL GRAPH FEATURES (10 columns)
        # ============================================================
        cursor.execute("""
            ALTER TABLE features
            ADD COLUMN IF NOT EXISTS cg_num_nodes INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS cg_num_edges INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS cg_max_call_depth INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS cg_num_external_calls INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS cg_external_call_ratio FLOAT DEFAULT 0.0,
            ADD COLUMN IF NOT EXISTS cg_has_cyclic_calls BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS cg_num_public_entry_points INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS cg_num_internal_functions INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS cg_avg_calls_per_function FLOAT DEFAULT 0.0,
            ADD COLUMN IF NOT EXISTS cg_num_leaf_functions INTEGER DEFAULT 0;
        """)
        
        # ============================================================
        # DATA FLOW FEATURES (7 columns)
        # ============================================================
        cursor.execute("""
            ALTER TABLE features
            ADD COLUMN IF NOT EXISTS dfg_num_state_vars INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS dfg_num_tainted_flows INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS dfg_has_cross_function_flow BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS dfg_num_sensitive_sinks INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS dfg_num_external_sources INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS dfg_taint_to_sink_ratio FLOAT DEFAULT 0.0,
            ADD COLUMN IF NOT EXISTS dfg_num_unvalidated_inputs INTEGER DEFAULT 0;
        """)
        
        conn.commit()
        logger.info("✅ Successfully added 25 graph feature columns")
        
        # Verify columns were added
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'features' 
            AND column_name LIKE 'cfg_%' 
               OR column_name LIKE 'cg_%' 
               OR column_name LIKE 'dfg_%'
            ORDER BY column_name;
        """)
        
        new_columns = cursor.fetchall()
        logger.info(f"Added columns: {len(new_columns)}")
        for col in new_columns:
            logger.info(f"  - {col[0]}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_graph_feature_columns()
