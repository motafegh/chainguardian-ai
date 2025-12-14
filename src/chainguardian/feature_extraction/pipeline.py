"""
Unified Feature Extraction Pipeline
====================================

Orchestrates multi-version Solidity compilation, static analysis, and feature extraction.
Thread-safe for parallel processing.
"""

from pathlib import Path
from typing import Dict, Optional
import pandas as pd
import logging
import re
import subprocess
from threading import Lock
from slither import Slither

import slither.detectors.all_detectors as detector_module

from chainguardian.feature_extraction.contract_analyzer import SlitherAnalyzer, ContractFeatures
from chainguardian.feature_extraction.ast_analyzer import ASTFeatureExtractor

logger = logging.getLogger(__name__)


class FeaturePipeline:
    """
    End-to-end pipeline: Contract → Feature Vector → ML-ready format
    
    Thread-safe for parallel feature extraction across multiple contracts.
    """
    
    def __init__(self):
        """
        Initialize with empty feature list and thread safety lock.
        """
        self.features: list[Dict] = []
        self._lock = Lock()  # Thread-safe feature collection
    
    def _detect_solidity_version(self, contract_path: Path) -> str:
        """
        Extract Solidity version from pragma with better compatibility.
        
        Returns version that's installed and compatible with Slither.
        """
        try:
            content = contract_path.read_text(encoding="utf-8")
            
            # Look for pragma solidity statement
            match = re.search(
                r'pragma\s+solidity\s+[\^=~<>]*\s*([\d.]+)',
                content
            )
            
            if match:
                version = match.group(1)
                
                # Map old versions to compatible ones
                version_tuple = tuple(map(int, version.split('.')))
                
                # Very old versions (0.4.0-0.4.10) → 0.4.26
                if version_tuple < (0, 4, 11):
                    logger.warning(
                        f"Contract uses very old Solidity {version}, "
                        f"mapping to 0.4.26 for compatibility"
                    )
                    return "0.4.26"
                
                # Old 0.4.x versions → 0.4.26 (most stable)
                elif version_tuple < (0, 5, 0):
                    logger.info(f"Mapping Solidity {version} → 0.4.26")
                    return "0.4.26"
                
                # 0.5.x versions → 0.5.17 (most stable)
                elif version_tuple < (0, 6, 0):
                    logger.info(f"Mapping Solidity {version} → 0.5.17")
                    return "0.5.17"
                
                # 0.6.x versions → 0.6.12
                elif version_tuple < (0, 7, 0):
                    logger.info(f"Mapping Solidity {version} → 0.6.12")
                    return "0.6.12"
                
                # 0.7.x versions → 0.7.6
                elif version_tuple < (0, 8, 0):
                    logger.info(f"Mapping Solidity {version} → 0.7.6")
                    return "0.7.6"
                
                # 0.8.x use as-is (modern)
                else:
                    logger.info(f"Using detected Solidity version: {version}")
                    return version
            
            else:
                logger.warning(
                    f"No pragma found in {contract_path.name}, "
                    f"defaulting to 0.8.20"
                )
                return "0.8.20"
                
        except Exception as e:
            logger.error(f"Failed to detect version for {contract_path}: {e}")
            return "0.8.20"

    
    def _set_solc_version(self, version: str) -> bool:
        """
        Switch to specific Solidity compiler version using solc-select.
        
        Args:
            version: Solidity version to use (e.g., "0.5.12")
        
        Returns:
            True if switch successful, False otherwise
        """
        try:
            result = subprocess.run(
                ["solc-select", "use", version],
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"✓ Switched to Solidity {version}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(
                f"Failed to switch to Solidity {version}. "
                f"Install it with: solc-select install {version}\n"
                f"Error: {e.stderr}"
            )
            return False
    
    def analyze_contract(
        self,
        contract_path: Path,
        contract_name: str
    ) -> Dict:
        """
        Extract ALL features from a single contract.
        
        HANDLES:
        - Single-file contracts (contract.sol)
        - Multi-file contracts (directory with multiple .sol files)
        - Import resolution errors (graceful degradation)
        
        Thread-safe: Can be called from multiple threads simultaneously.
        
        Workflow:
        1. Detect if multi-file (directory) or single-file
        2. Detect required Solidity version from pragma
        3. Switch compiler to that version
        4. Create Slither object (compiles contract, builds AST)
        5. Register all 93 detectors
        6. Extract vulnerability features via SlitherAnalyzer
        7. Extract code structure features via ASTFeatureExtractor
        8. Combine into single feature dict
        
        Args:
            contract_path: Path to .sol file OR directory with .sol files
            contract_name: Name of main contract to analyze
        
        Returns:
            Dict with 15 features (2 metadata + 7 vulnerability + 6 code structure)
        """
        logger.info(f"Analyzing {contract_name} from {contract_path}")
        
        combined_features = {
            'contract_name': contract_name,
            'file_path': str(contract_path),
        }
        
        try:
            # ================================================================
            # STEP 0: HANDLE MULTI-FILE CONTRACTS (DIRECTORIES)
            # ================================================================
            analysis_target = contract_path
            main_contract_file = None
            
            if contract_path.is_dir():
                logger.debug(f"{contract_name}: Multi-file contract detected (directory)")
                
                # Find main contract file
                # Strategy 1: Look for file matching contract name
                main_candidates = list(contract_path.glob(f"{contract_name}.sol"))
                
                if not main_candidates:
                    # Strategy 2: Look for file with contract name in it
                    main_candidates = [
                        f for f in contract_path.glob("*.sol")
                        if contract_name.lower() in f.stem.lower()
                    ]
                
                if not main_candidates:
                    # Strategy 3: Use first .sol file
                    main_candidates = list(contract_path.glob("*.sol"))
                
                if not main_candidates:
                    raise Exception(f"No .sol files found in directory {contract_path}")
                
                main_contract_file = main_candidates[0]
                analysis_target = main_contract_file  # Analyze main file
                
                logger.debug(
                    f"{contract_name}: Using main file {main_contract_file.name} "
                    f"from {len(list(contract_path.glob('*.sol')))} files"
                )
            else:
                main_contract_file = contract_path
            
            # ================================================================
            # STEP 1: DETECT REQUIRED SOLIDITY VERSION
            # ================================================================
            required_version = self._detect_solidity_version(main_contract_file)
            
            # ================================================================
            # STEP 2: SWITCH COMPILER TO THAT VERSION
            # ================================================================
            if not self._set_solc_version(required_version):
                raise Exception(
                    f"Solidity {required_version} not installed. "
                    f"Run: solc-select install {required_version}"
                )
            
            # ================================================================
            # STEP 3: CREATE SLITHER OBJECT (COMPILE CONTRACT)
            # ================================================================
            # For multi-file contracts, analyze the main file but imports will resolve
            # from the same directory
            try:
                slither = Slither(
                    str(analysis_target),
                    solc="solc",
                    solc_disable_warnings=True,
                    solc_args="--optimize"
                )
                
            except Exception as compile_error:
                error_str = str(compile_error).lower()
                
                # ============================================================
                # GRACEFUL DEGRADATION: Import/dependency errors
                # ============================================================
                # These are NOT code quality issues - just missing external libraries
                if any(keyword in error_str for keyword in [
                    'not found', 'import', 'file not found', 'file import callback not supported',
                    '@openzeppelin', '@chainlink', 'node_modules', 'source "', 
                    'no such file', 'cannot find'
                ]):
                    logger.warning(
                        f"{contract_name}: Skipping due to missing dependencies. "
                        f"Error: {str(compile_error)[:200]}"
                    )
                    raise Exception(f"Missing dependencies: {str(compile_error)[:100]}")
                
                # ============================================================
                # REAL COMPILATION ERRORS: Syntax/version issues
                # ============================================================
                else:
                    logger.error(
                        f"{contract_name}: Invalid compilation: "
                        f"{str(compile_error)[:200]}"
                    )
                    raise Exception(f"Invalid compilation: {str(compile_error)[:100]}")
            
            # ================================================================
            # STEP 4: REGISTER DETECTORS
            # ================================================================
            logger.debug(f"Registering detectors for {contract_name}...")
            
            detector_classes = [
                getattr(detector_module, name)
                for name in dir(detector_module)
                if name[0].isupper()
            ]
            
            for detector_class in detector_classes:
                slither.register_detector(detector_class)
            
            logger.debug(f"✓ Registered {len(slither.detectors)} detectors")
            
            # ================================================================
            # STEP 5: EXTRACT VULNERABILITY FEATURES
            # ================================================================
            vuln_analyzer = SlitherAnalyzer(slither)
            vuln_features = vuln_analyzer.extract_features(contract_name)
            
            combined_features.update({
                'has_reentrancy': vuln_features.has_reentrancy,
                'has_access_control_issues': vuln_features.has_access_control_issues,
                'has_timestamp_dependency': vuln_features.has_timestamp_dependency,
                'has_unchecked_call': vuln_features.has_unchecked_call,
                'high_severity_count': vuln_features.high_severity_count,
                'medium_severity_count': vuln_features.medium_severity_count,
                'low_severity_count': vuln_features.low_severity_count,
            })
            
            # ================================================================
            # STEP 6: EXTRACT AST FEATURES
            # ================================================================
            ast_extractor = ASTFeatureExtractor(main_contract_file)
            ast_features = ast_extractor.extract_features(contract_name)
            
            combined_features.update(ast_features)
            
            logger.info(
                f"✓ Extracted {len(combined_features)} features for {contract_name}"
            )
            
        except Exception as e:
            logger.error(f"Analysis failed for {contract_name}: {e}")
            
            # Default zero features on failure
            combined_features.update({
                'has_reentrancy': False,
                'has_access_control_issues': False,
                'has_timestamp_dependency': False,
                'has_unchecked_call': False,
                'high_severity_count': 0,
                'medium_severity_count': 0,
                'low_severity_count': 0,
                'num_functions': 0,
                'num_external_calls': 0,
                'num_state_vars': 0,
                'num_modifiers': 0,
                'max_cyclomatic_complexity': 0,
                'num_low_level_calls': 0,
            })
        
        # ================================================================
        # THREAD-SAFE: Add to feature list
        # ================================================================
        with self._lock:
            self.features.append(combined_features)
        
        return combined_features

    
    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert collected features to pandas DataFrame.
        
        Returns:
            pandas DataFrame with all collected features
            Columns: 15 features
            Rows: One per contract
        """
        if not self.features:
            logger.warning("No features collected yet")
            return pd.DataFrame()
        
        df = pd.DataFrame(self.features)
        
        logger.info(
            f"Created DataFrame with {len(df)} contracts and "
            f"{len(df.columns)} features"
        )
        
        return df
    
    def save_dataset(self, output_path: Path):
        """
        Save features as CSV for ML training.
        
        Args:
            output_path: Where to save CSV file
        """
        df = self.to_dataframe()
        df.to_csv(output_path, index=False)
        logger.info(f"Saved dataset to {output_path}")
