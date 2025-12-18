"""
Extract graph features for existing contracts.
Updates database with 25 new graph feature columns.
"""
from pathlib import Path
from chainguardian.database.manager import DatabaseManager
from chainguardian.feature_extraction.graph_extractor import GraphFeatureExtractor
from slither import Slither
import logging
from tqdm import tqdm
import subprocess
from threading import Lock

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GraphFeatureUpdater:
    """Update database with graph features for existing contracts."""
    
    def __init__(self):
        self.db = DatabaseManager()
        self._lock = Lock()  # Thread safety for solc version switching
        self._installed_versions = self._get_installed_versions()
        
        logger.info(f"Found {len(self._installed_versions)} Solidity versions")
    
    def _get_installed_versions(self):
        """Get installed Solidity versions."""
        try:
            result = subprocess.run(
                ["solc-select", "versions"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            versions = set()
            for line in result.stdout.split('\n'):
                if line.strip():
                    version = line.split()[0]
                    if version and version[0].isdigit():
                        versions.add(version)
            return versions
        except Exception as e:
            logger.error(f"Failed to get versions: {e}")
            return set()
    
    def _set_solc_version(self, version: str):
        """Switch Solidity compiler version."""
        try:
            subprocess.run(
                ["solc-select", "use", version],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            return True
        except:
            return False
    
    def _detect_compiler_version(self, file_path: Path) -> str:
        """Detect required Solidity version from file."""
        try:
            content = file_path.read_text(encoding='utf-8')
            import re
            pragma_match = re.search(r'pragma\s+solidity\s+([^;]+);', content)
            if pragma_match:
                pragma_text = pragma_match.group(1).strip()
                # Extract version number
                version_match = re.search(r'([\d.]+)', pragma_text)
                if version_match:
                    return version_match.group(1)
        except:
            pass
        return "0.8.20"  # Default
    
    def update_all(self):
        """Extract graph features for all successful contracts."""
        
        # Get all successful extractions
        df = self.db.get_all_features()
        successful = df[df['failure_reason'].isna()].copy()
        
        logger.info("="*70)
        logger.info("GRAPH FEATURE EXTRACTION")
        logger.info("="*70)
        logger.info(f"Total contracts: {len(df)}")
        logger.info(f"Successful extractions: {len(successful)}")
        logger.info(f"Will extract graph features for: {len(successful)} contracts")
        logger.info("="*70)
        
        success_count = 0
        fail_count = 0
        
        # Process each contract
        with tqdm(total=len(successful), desc="Extracting graph features") as pbar:
            for idx, row in successful.iterrows():
                contract_id = row['contract_id']
                contract_name = row['contract_name']
                file_path_str = row['file_path']
                
                try:
                    # Extract features
                    graph_features = self._extract_for_contract(
                        contract_id, contract_name, file_path_str
                    )
                    
                    if graph_features:
                        # Update database
                        self._update_database(contract_id, graph_features)
                        success_count += 1
                    else:
                        fail_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed {contract_name}: {e}")
                    fail_count += 1
                
                pbar.update(1)
                pbar.set_postfix({
                    'success': success_count,
                    'failed': fail_count
                })
        
        logger.info("="*70)
        logger.info("EXTRACTION COMPLETE")
        logger.info("="*70)
        logger.info(f"✅ Successful: {success_count}/{len(successful)}")
        logger.info(f"❌ Failed: {fail_count}/{len(successful)}")
        logger.info("="*70)
    
    def _extract_for_contract(self, contract_id: int, contract_name: str, 
                              file_path_str: str) -> dict:
        """Extract graph features for one contract."""
        
        file_path = Path(file_path_str)
        
        # Handle multi-file contracts
        if file_path.is_dir():
            # Find main contract file
            sol_files = list(file_path.glob("*.sol"))
            if not sol_files:
                logger.warning(f"No .sol files in {file_path}")
                return None
            analysis_target = sol_files[0]
        else:
            analysis_target = file_path
        
        if not analysis_target.exists():
            logger.warning(f"File not found: {analysis_target}")
            return None
        
        # Detect and set compiler version
        required_version = self._detect_compiler_version(analysis_target)
        
        with self._lock:
            if not self._set_solc_version(required_version):
                logger.warning(f"Version {required_version} not available")
                return None
            
            # Compile with Slither
            try:
                slither = Slither(
                    str(analysis_target),
                    solc="solc",
                    solc_disable_warnings=True,
                    solc_args="--optimize"
                )
            except Exception as e:
                logger.debug(f"Compilation failed for {contract_name}: {e}")
                return None
        
        # Extract graph features
        try:
            extractor = GraphFeatureExtractor(slither)
            features = extractor.extract_features(contract_name)
            return features
        except Exception as e:
            logger.error(f"Graph extraction failed: {e}")
            return None
    
    def _update_database(self, contract_id: int, graph_features: dict):
        """Update database with graph features."""
        
        # Build UPDATE query
        set_clauses = []
        values = {'contract_id': contract_id}
        
        for feature_name, feature_value in graph_features.items():
            set_clauses.append(f"{feature_name} = %({feature_name})s")
            values[feature_name] = feature_value
        
        query = f"""
            UPDATE features
            SET {', '.join(set_clauses)}
            WHERE contract_id = %(contract_id)s;
        """
        
        # Execute update
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="chainguardian",
            user="chainguardian_user",
            password="2220128"
        )
        
        cursor = conn.cursor()
        try:
            cursor.execute(query, values)
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database update failed: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    updater = GraphFeatureUpdater()
    updater.update_all()
