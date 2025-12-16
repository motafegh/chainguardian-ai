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
            # STEP 2: INSERT FEATURES
            # ============================================================
            # 🎓 Extract feature values from features_dict
            feature_data = {
                'contract_id': contract_id,
                'has_reentrancy': features_dict.get('has_reentrancy', False),
                'has_access_control_issues': features_dict.get('has_access_control_issues', False),
                'has_timestamp_dependency': features_dict.get('has_timestamp_dependency', False),
                'has_unchecked_call': features_dict.get('has_unchecked_call', False),
                'high_severity_count': features_dict.get('high_severity_count', 0),
                'medium_severity_count': features_dict.get('medium_severity_count', 0),
                'low_severity_count': features_dict.get('low_severity_count', 0),
                'num_functions': features_dict.get('num_functions', 0),
                'num_external_calls': features_dict.get('num_external_calls', 0),
                'num_state_vars': features_dict.get('num_state_vars', 0),
                'num_modifiers': features_dict.get('num_modifiers', 0),
                'max_cyclomatic_complexity': features_dict.get('max_cyclomatic_complexity', 0),
                'num_low_level_calls': features_dict.get('num_low_level_calls', 0),
                'failure_reason': features_dict.get('failure_reason'),
                'error_message': features_dict.get('error_message')
            }
            
            cursor.execute("""
                INSERT INTO features (
                    contract_id,
                    has_reentrancy, has_access_control_issues, has_timestamp_dependency, has_unchecked_call,
                    high_severity_count, medium_severity_count, low_severity_count,
                    num_functions, num_external_calls, num_state_vars, num_modifiers,
                    max_cyclomatic_complexity, num_low_level_calls,
                    failure_reason, error_message
                )
                VALUES (
                    %(contract_id)s,
                    %(has_reentrancy)s, %(has_access_control_issues)s, %(has_timestamp_dependency)s, %(has_unchecked_call)s,
                    %(high_severity_count)s, %(medium_severity_count)s, %(low_severity_count)s,
                    %(num_functions)s, %(num_external_calls)s, %(num_state_vars)s, %(num_modifiers)s,
                    %(max_cyclomatic_complexity)s, %(num_low_level_calls)s,
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
                    f.has_reentrancy,
                    f.has_access_control_issues,
                    f.has_timestamp_dependency,
                    f.has_unchecked_call,
                    f.high_severity_count,
                    f.medium_severity_count,
                    f.low_severity_count,
                    f.num_functions,
                    f.num_external_calls,
                    f.num_state_vars,
                    f.num_modifiers,
                    f.max_cyclomatic_complexity,
                    f.num_low_level_calls,
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
            # 🎓 RealDictCursor gives us list of dicts, perfect for pandas
            df = pd.DataFrame(rows)
            logger.info(f"Loaded {len(df)} contracts from database")
            
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