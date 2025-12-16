"""
Database Manager - handles all PostgreSQL operations

🎓 This is like a contract interface in Solidity
It wraps all database operations so pipeline.py doesn't need to know SQL
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Optional, List
import logging
from contextlib import contextmanager
import pandas as pd

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages all database operations for ChainGuardian.
    
    🎓 Think of this like a Web3 provider wrapper:
    - Handles connections (like provider.connect())
    - Executes queries (like contract.functions.xxx().call())
    - Manages transactions (like tx.wait())
    
    Usage:
        db = DatabaseManager()
        db.save_contract_and_features(features_dict)
        df = db.get_all_features()
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "chainguardian",
        user: str = "chainguardian_user",
        password: str = "2220128"
    ):
        """
        Initialize database connection.
        
        🎓 Similar to:
        web3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
        """
        self.config = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
        
        # Test connection on init
        try:
            conn = self._get_connection()
            conn.close()
            logger.info("✅ Database connection established")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    def _get_connection(self):
        """
        Create database connection.
        
        🎓 Like opening a websocket to Ethereum node
        Each query needs a connection
        """
        return psycopg2.connect(**self.config)
    
    @contextmanager
    def _get_cursor(self, dict_cursor: bool = False):
        """
        Context manager for database cursor.
        
        🎓 This pattern ensures connection is always closed
        Similar to:
        async with web3.provider as provider:
            # do stuff
        # provider automatically closed
        
        Usage:
            with self._get_cursor() as cursor:
                cursor.execute("SELECT ...")
                # cursor automatically closed after block
        """
        conn = self._get_connection()
        cursor_factory = RealDictCursor if dict_cursor else None
        cursor = conn.cursor(cursor_factory=cursor_factory)
        
        try:
            yield cursor
            conn.commit()  # 🎓 Like transaction.wait() - make changes permanent
        except Exception as e:
            conn.rollback()  # 🎓 Like transaction revert - undo changes
            logger.error(f"Database error: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def save_contract_and_features(self, features_dict: Dict) -> int:
        """
        Save contract and its features to database.
        
        🎓 This is atomic - either both save or neither saves
        Similar to Solidity: either entire transaction succeeds or reverts
        
        Args:
            features_dict: Dictionary with contract info and features
                Must contain: contract_name, file_path
                Optional: address, compiler_version, source
                Features: has_reentrancy, num_functions, etc.
        
        Returns:
            contract_id: Database ID of saved contract
        
        Example:
            features = {
                'contract_name': 'Token',
                'file_path': '/path/to/Token.sol',
                'address': '0x123...',
                'has_reentrancy': False,
                'num_functions': 5
            }
            contract_id = db.save_contract_and_features(features)
        """
        with self._get_cursor() as cursor:
            # ============================================================
            # STEP 1: INSERT CONTRACT
            # ============================================================
            # 🎓 Extract contract metadata from features_dict
            # Extract address from file_path if not provided
            # Filenames like: BetProtocolToken_0xcf3c8be2.sol
            address = features_dict.get('address')
            if not address:
                file_path = features_dict.get('file_path', '')
                # Try to extract 0x pattern from filename
                import re
                match = re.search(r'_0x[a-fA-F0-9]+', file_path)
                if match:
                    # Extract just the 0x part
                    address = match.group(0)[1:]  # Remove leading underscore
                    # Pad to full address (42 chars) if needed
                    if len(address) < 42:
                        address = address + '0' * (42 - len(address))
                else :
                    # No address pattern found
                    # 🎓 For SmartBugs contracts, this is expected
                    # Address will be NULL in database (which is fine!)
                    address = None
            contract_data = {
                'name': features_dict.get('contract_name', 'Unknown'),
                'address': address,
                'source_code': None,  # We don't store full source in DB (too large)
                'compiler_version': features_dict.get('compiler_version'),
                'source': features_dict.get('source', 'manual'),
                'file_path': features_dict.get('file_path')
            }
            
            cursor.execute("""
                INSERT INTO contracts (name, address, source_code, compiler_version, source, file_path)
                VALUES (%(name)s, %(address)s, %(source_code)s, %(compiler_version)s, %(source)s, %(file_path)s)
                RETURNING id;
            """, contract_data)
            
            # Get the contract ID that was just inserted
            # 🎓 Like getting transaction receipt to see deployed contract address
            contract_id = cursor.fetchone()[0]
            
            logger.debug(f"Saved contract: {contract_data['name']} (id={contract_id})")
            
            # ============================================================
            # STEP 2: INSERT FEATURES (EXPANDED: 15 → 58 fields)
            # ============================================================
            feature_data = {
                'contract_id': contract_id,
                
                # ========================================================
                # ORIGINAL VULNERABILITY FLAGS (4)
                # ========================================================
                'has_reentrancy': features_dict.get('has_reentrancy', False),
                'has_access_control_issues': features_dict.get('has_access_control_issues', False),
                'has_timestamp_dependency': features_dict.get('has_timestamp_dependency', False),
                'has_unchecked_call': features_dict.get('has_unchecked_call', False),
                
                # ========================================================
                # NEW: ADDITIONAL VULNERABILITY FLAGS (19)
                # ========================================================
                # Reentrancy variants
                'has_reentrancy_unlimited': features_dict.get('has_reentrancy_unlimited', False),
                'has_reentrancy_benign': features_dict.get('has_reentrancy_benign', False),
                'has_reentrancy_events': features_dict.get('has_reentrancy_events', False),
                
                # Unchecked operations
                'has_unchecked_transfer': features_dict.get('has_unchecked_transfer', False),
                
                # Delegatecall issues
                'has_controlled_delegatecall': features_dict.get('has_controlled_delegatecall', False),
                'has_delegatecall_loop': features_dict.get('has_delegatecall_loop', False),
                
                # Uninitialized variables
                'has_uninitialized_state': features_dict.get('has_uninitialized_state', False),
                'has_uninitialized_storage': features_dict.get('has_uninitialized_storage', False),
                'has_uninitialized_local': features_dict.get('has_uninitialized_local', False),
                
                # Dangerous patterns
                'has_tx_origin': features_dict.get('has_tx_origin', False),
                'has_inline_assembly': features_dict.get('has_inline_assembly', False),
                'has_locked_ether': features_dict.get('has_locked_ether', False),
                'has_msg_value_loop': features_dict.get('has_msg_value_loop', False),
                
                # Code quality issues
                'has_shadowing_state': features_dict.get('has_shadowing_state', False),
                'has_shadowing_builtin': features_dict.get('has_shadowing_builtin', False),
                'has_shadowing_abstract': features_dict.get('has_shadowing_abstract', False),
                'has_unused_state_vars': features_dict.get('has_unused_state_vars', False),
                'has_unused_return_values': features_dict.get('has_unused_return_values', False),
                
                # Compiler issues
                'has_incorrect_solc_version': features_dict.get('has_incorrect_solc_version', False),
                'has_floating_pragma': features_dict.get('has_floating_pragma', False),
                'has_outdated_compiler': features_dict.get('has_outdated_compiler', False),
                
                # ========================================================
                # ORIGINAL SEVERITY COUNTS (3)
                # ========================================================
                'high_severity_count': features_dict.get('high_severity_count', 0),
                'medium_severity_count': features_dict.get('medium_severity_count', 0),
                'low_severity_count': features_dict.get('low_severity_count', 0),
                
                # ========================================================
                # ORIGINAL AST FEATURES (6)
                # ========================================================
                'num_functions': features_dict.get('num_functions', 0),
                'num_external_calls': features_dict.get('num_external_calls', 0),
                'num_state_vars': features_dict.get('num_state_vars', 0),
                'num_modifiers': features_dict.get('num_modifiers', 0),
                'max_cyclomatic_complexity': features_dict.get('max_cyclomatic_complexity', 0),
                'num_low_level_calls': features_dict.get('num_low_level_calls', 0),
                
                # ========================================================
                # NEW: CODE QUALITY METRICS (11)
                # ========================================================
                'lines_of_code': features_dict.get('lines_of_code', 0),
                'num_contracts_in_file': features_dict.get('num_contracts_in_file', 1),
                'num_dependencies': features_dict.get('num_dependencies', 0),
                'avg_function_complexity': features_dict.get('avg_function_complexity', 0.0),
                'num_functions_high_complexity': features_dict.get('num_functions_high_complexity', 0),
                'num_comments': features_dict.get('num_comments', 0),
                'comment_to_code_ratio': features_dict.get('comment_to_code_ratio', 0.0),
                'num_payable_functions': features_dict.get('num_payable_functions', 0),
                'num_library_calls': features_dict.get('num_library_calls', 0),
                'inheritance_depth': features_dict.get('inheritance_depth', 0),
                'num_unused_functions': features_dict.get('num_unused_functions', 0),
                
                # ========================================================
                # NEW: DETECTOR STATISTICS (9)
                # ========================================================
                'high_confidence_detectors': features_dict.get('high_confidence_detectors', 0),
                'medium_confidence_detectors': features_dict.get('medium_confidence_detectors', 0),
                'low_confidence_detectors': features_dict.get('low_confidence_detectors', 0),
                'security_detectors_triggered': features_dict.get('security_detectors_triggered', 0),
                'optimization_detectors_triggered': features_dict.get('optimization_detectors_triggered', 0),
                'total_detector_hits': features_dict.get('total_detector_hits', 0),
                'unique_vulnerability_types': features_dict.get('unique_vulnerability_types', 0),
                'detectors_per_function': features_dict.get('detectors_per_function', 0.0),
                'detectors_per_loc': features_dict.get('detectors_per_loc', 0.0),
                
                # ========================================================
                # NEW: COMPOSITE RISK SCORES (4)
                # ========================================================
                'risk_score_simple': features_dict.get('risk_score_simple', 0.0),
                'risk_score_weighted': features_dict.get('risk_score_weighted', 0.0),
                'is_high_risk': features_dict.get('is_high_risk', False),
                'contract_complexity_category': features_dict.get('contract_complexity_category', 'simple'),
                
                # ========================================================
                # ORIGINAL ERROR TRACKING (2)
                # ========================================================
                'failure_reason': features_dict.get('failure_reason'),
                'error_message': features_dict.get('error_message')
            }

            
            cursor.execute("""
                INSERT INTO features (
                    contract_id,
                    -- Original vulnerability flags
                    has_reentrancy, has_access_control_issues, has_timestamp_dependency, has_unchecked_call,
                    -- New vulnerability flags
                    has_reentrancy_unlimited, has_reentrancy_benign, has_reentrancy_events,
                    has_unchecked_transfer,
                    has_controlled_delegatecall, has_delegatecall_loop,
                    has_uninitialized_state, has_uninitialized_storage, has_uninitialized_local,
                    has_tx_origin, has_inline_assembly, has_locked_ether, has_msg_value_loop,
                    has_shadowing_state, has_shadowing_builtin, has_shadowing_abstract,
                    has_unused_state_vars, has_unused_return_values,
                    has_incorrect_solc_version, has_floating_pragma, has_outdated_compiler,
                    -- Severity counts
                    high_severity_count, medium_severity_count, low_severity_count,
                    -- Original AST features
                    num_functions, num_external_calls, num_state_vars, num_modifiers,
                    max_cyclomatic_complexity, num_low_level_calls,
                    -- New code quality metrics
                    lines_of_code, num_contracts_in_file, num_dependencies,
                    avg_function_complexity, num_functions_high_complexity,
                    num_comments, comment_to_code_ratio,
                    num_payable_functions, num_library_calls, inheritance_depth, num_unused_functions,
                    -- Detector statistics
                    high_confidence_detectors, medium_confidence_detectors, low_confidence_detectors,
                    security_detectors_triggered, optimization_detectors_triggered,
                    total_detector_hits, unique_vulnerability_types,
                    detectors_per_function, detectors_per_loc,
                    -- Risk scores
                    risk_score_simple, risk_score_weighted, is_high_risk, contract_complexity_category,
                    -- Error tracking
                    failure_reason, error_message
                )
                VALUES (
                    %(contract_id)s,
                    -- Original vulnerability flags
                    %(has_reentrancy)s, %(has_access_control_issues)s, %(has_timestamp_dependency)s, %(has_unchecked_call)s,
                    -- New vulnerability flags
                    %(has_reentrancy_unlimited)s, %(has_reentrancy_benign)s, %(has_reentrancy_events)s,
                    %(has_unchecked_transfer)s,
                    %(has_controlled_delegatecall)s, %(has_delegatecall_loop)s,
                    %(has_uninitialized_state)s, %(has_uninitialized_storage)s, %(has_uninitialized_local)s,
                    %(has_tx_origin)s, %(has_inline_assembly)s, %(has_locked_ether)s, %(has_msg_value_loop)s,
                    %(has_shadowing_state)s, %(has_shadowing_builtin)s, %(has_shadowing_abstract)s,
                    %(has_unused_state_vars)s, %(has_unused_return_values)s,
                    %(has_incorrect_solc_version)s, %(has_floating_pragma)s, %(has_outdated_compiler)s,
                    -- Severity counts
                    %(high_severity_count)s, %(medium_severity_count)s, %(low_severity_count)s,
                    -- Original AST features
                    %(num_functions)s, %(num_external_calls)s, %(num_state_vars)s, %(num_modifiers)s,
                    %(max_cyclomatic_complexity)s, %(num_low_level_calls)s,
                    -- New code quality metrics
                    %(lines_of_code)s, %(num_contracts_in_file)s, %(num_dependencies)s,
                    %(avg_function_complexity)s, %(num_functions_high_complexity)s,
                    %(num_comments)s, %(comment_to_code_ratio)s,
                    %(num_payable_functions)s, %(num_library_calls)s, %(inheritance_depth)s, %(num_unused_functions)s,
                    -- Detector statistics
                    %(high_confidence_detectors)s, %(medium_confidence_detectors)s, %(low_confidence_detectors)s,
                    %(security_detectors_triggered)s, %(optimization_detectors_triggered)s,
                    %(total_detector_hits)s, %(unique_vulnerability_types)s,
                    %(detectors_per_function)s, %(detectors_per_loc)s,
                    -- Risk scores
                    %(risk_score_simple)s, %(risk_score_weighted)s, %(is_high_risk)s, %(contract_complexity_category)s,
                    -- Error tracking
                    %(failure_reason)s, %(error_message)s
                );
            """, feature_data)

            
            logger.debug(f"Saved features for contract {contract_id}")
            
            return contract_id
    
    def get_all_features(self) -> pd.DataFrame:
        """
        Get all contracts with their features as DataFrame.
        
        🎓 This is like querying events or reading contract state
        Returns data ready for ML training
        
        Returns:
            DataFrame with columns:
            - contract_id, name, address, file_path
            - has_reentrancy, num_functions, etc.
        """
        with self._get_cursor(dict_cursor=True) as cursor:
            # JOIN contracts and features tables
            # 🎓 This combines related data from two tables
            cursor.execute("""
                SELECT
                    c.id as contract_id,
                    c.name as contract_name,
                    c.address,
                    c.file_path,
                    c.compiler_version,
                    -- Original vulnerability flags
                    f.has_reentrancy,
                    f.has_access_control_issues,
                    f.has_timestamp_dependency,
                    f.has_unchecked_call,
                    -- New vulnerability flags
                    f.has_reentrancy_unlimited,
                    f.has_reentrancy_benign,
                    f.has_reentrancy_events,
                    f.has_unchecked_transfer,
                    f.has_controlled_delegatecall,
                    f.has_delegatecall_loop,
                    f.has_uninitialized_state,
                    f.has_uninitialized_storage,
                    f.has_uninitialized_local,
                    f.has_tx_origin,
                    f.has_inline_assembly,
                    f.has_locked_ether,
                    f.has_msg_value_loop,
                    f.has_shadowing_state,
                    f.has_shadowing_builtin,
                    f.has_shadowing_abstract,
                    f.has_unused_state_vars,
                    f.has_unused_return_values,
                    f.has_incorrect_solc_version,
                    f.has_floating_pragma,
                    f.has_outdated_compiler,
                    -- Severity counts
                    f.high_severity_count,
                    f.medium_severity_count,
                    f.low_severity_count,
                    -- Original AST features
                    f.num_functions,
                    f.num_external_calls,
                    f.num_state_vars,
                    f.num_modifiers,
                    f.max_cyclomatic_complexity,
                    f.num_low_level_calls,
                    -- New code quality metrics
                    f.lines_of_code,
                    f.num_contracts_in_file,
                    f.num_dependencies,
                    f.avg_function_complexity,
                    f.num_functions_high_complexity,
                    f.num_comments,
                    f.comment_to_code_ratio,
                    f.num_payable_functions,
                    f.num_library_calls,
                    f.inheritance_depth,
                    f.num_unused_functions,
                    -- Detector statistics
                    f.high_confidence_detectors,
                    f.medium_confidence_detectors,
                    f.low_confidence_detectors,
                    f.security_detectors_triggered,
                    f.optimization_detectors_triggered,
                    f.total_detector_hits,
                    f.unique_vulnerability_types,
                    f.detectors_per_function,
                    f.detectors_per_loc,
                    -- Risk scores
                    f.risk_score_simple,
                    f.risk_score_weighted,
                    f.is_high_risk,
                    f.contract_complexity_category,
                    -- Error tracking
                    f.failure_reason,
                    f.error_message
                FROM contracts c
                LEFT JOIN features f ON c.id = f.contract_id
                ORDER BY c.id;
            """)
        
            rows = cursor.fetchall()
            
            if not rows:
                logger.warning("No data in database yet")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(rows)
            logger.info(f"Loaded {len(df)} contracts with {len(df.columns)} features from database")
            
            return df
    
    def get_contract_count(self) -> int:
        """Get total number of contracts in database."""
        with self._get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM contracts;")
            count = cursor.fetchone()[0]
            return count
    
    def get_stats(self) -> Dict:
        """
        Get database statistics.
        
        Returns:
            Dict with counts and percentages
        """
        with self._get_cursor(dict_cursor=True) as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_contracts,
                    COUNT(CASE WHEN f.failure_reason IS NULL THEN 1 END) as successful_extractions,
                    COUNT(CASE WHEN f.failure_reason IS NOT NULL THEN 1 END) as failed_extractions,
                    COUNT(CASE WHEN f.has_reentrancy = TRUE THEN 1 END) as contracts_with_reentrancy
                FROM contracts c
                LEFT JOIN features f ON c.id = f.contract_id;
            """)
            
            stats = cursor.fetchone()
            return dict(stats) if stats else {}
    def add_vulnerability_label(
        self,
        contract_id: int,
        vulnerability_type: str,
        has_vulnerability: bool = True,
        severity: str = None,
        source: str = "smartbugs_curated"
    ) -> int:
        """
        Add vulnerability label for a contract.
        
        🎓 This populates the labels table
        Used for training data - tells model which contracts are vulnerable
        
        Args:
            contract_id: Database ID of contract
            vulnerability_type: Type of vulnerability (e.g., "reentrancy")
            has_vulnerability: True if vulnerable, False if safe
            severity: Optional severity level
            source: Where label came from
        
        Returns:
            label_id: Database ID of inserted label
        """
        with self._get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO labels (
                    contract_id,
                    vulnerability_type,
                    has_vulnerability,
                    severity,
                    source
                )
                VALUES (
                    %(contract_id)s,
                    %(vulnerability_type)s,
                    %(has_vulnerability)s,
                    %(severity)s,
                    %(source)s
                )
                ON CONFLICT (contract_id, vulnerability_type, source)
                DO UPDATE SET
                    has_vulnerability = EXCLUDED.has_vulnerability,
                    severity = EXCLUDED.severity
                RETURNING id;
            """, {
                'contract_id': contract_id,
                'vulnerability_type': vulnerability_type,
                'has_vulnerability': has_vulnerability,
                'severity': severity,
                'source': source
            })
            
            label_id = cursor.fetchone()[0]
            logger.debug(f"Added label: contract={contract_id}, type={vulnerability_type}")
            
            return label_id