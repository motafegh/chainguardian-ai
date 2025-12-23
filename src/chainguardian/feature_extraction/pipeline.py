"""
Unified Feature Extraction Pipeline - PRODUCTION VERSION WITH SEMANTIC ANALYSIS
================================================================================

Thread-safe multi-version Solidity compilation with comprehensive error handling.

KEY FEATURES:
- Handles caret (^), range (>=...<), and exact pragmas correctly
- Thread-safe parallel processing with compiler version locking
- Multi-file contract support with proper import resolution
- Comprehensive error categorization with full error messages
- 85+ Solidity compiler versions supported
- **NEW**: Semantic security pattern detection (CEI, reentrancy guards)

FEATURE EXTRACTION PIPELINE (7 STEPS):
1. Multi-file contract detection
2. Solidity version detection & compiler switching
3. Slither compilation & detector registration
4. Vulnerability feature extraction (23 flags + 3 severity + 9 stats + 4 risk)
5. AST feature extraction (17 code structure features)
6. Graph feature extraction (25 CFG/CG/DFG features)
7. **NEW**: Semantic security pattern analysis (8 semantic features)

TOTAL: 89 features (was 81)
"""

from pathlib import Path
from typing import Dict, Tuple
import pandas as pd
import logging
import re
import subprocess
from threading import Lock
from slither import Slither
import slither.detectors.all_detectors as detector_module

from chainguardian.feature_extraction.contract_analyzer import SlitherAnalyzer
from chainguardian.feature_extraction.ast_analyzer import ASTFeatureExtractor
from chainguardian.feature_extraction.semantic_analyzer import extract_semantic_features

logger = logging.getLogger(__name__)


class FeaturePipeline:
    """
    End-to-end pipeline: Contract → Feature Vector → ML-ready format
    
    Thread-safe for parallel feature extraction across multiple contracts.
    Caches installed Solidity versions for performance.
    
    Features extracted (89 total):
    - 23 vulnerability flags (reentrancy, access control, etc.)
    - 3 severity counts (high, medium, low)
    - 17 AST features (complexity, LOC, etc.)
    - 9 detector statistics (confidence, types, etc.)
    - 4 risk scores (simple, weighted, category)
    - 25 graph features (CFG, call graph, data flow)
    - 8 semantic features (CEI violations, reentrancy guards, etc.)
    """
    
    def __init__(self):
        """Initialize pipeline with version cache and thread safety."""
        from chainguardian.database.manager import DatabaseManager
        
        self.features = None  # Keep for backwards compatibility
        self.db = DatabaseManager()  # Database connection
        logger.info("✅ Database connection ready")
        
        self._lock = Lock()  # Protects version switching + compilation
        
        # Cache installed versions (call once, use many times)
        self._installed_versions = self._get_installed_versions()
        logger.info(f"✓ Found {len(self._installed_versions)} installed Solidity versions")
        
        if len(self._installed_versions) == 0:
            logger.error(
                "⚠️  NO Solidity versions detected!\n"
                "   Install with: poetry run solc-select install 0.8.20"
            )
    
    def _get_installed_versions(self) -> set:
        """
        Get list of installed Solidity compiler versions.
        Uses direct solc-select call for reliability.
        
        Returns:
            Set of version strings (e.g., {'0.4.26', '0.5.17', '0.8.20'})
        """
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
                    # Extract version (first token before space/paren)
                    version = line.split()[0]
                    if version and version[0].isdigit():
                        versions.add(version)
            
            return versions
        
        except Exception as e:
            logger.error(f"Failed to get installed versions: {e}")
            return set()
    
    def _detect_solidity_version(self, contract_path: Path) -> Tuple[str, bool]:
        """
        Extract Solidity version from pragma.
        
        HANDLES ALL PRAGMA TYPES:
        - pragma solidity 0.8.3;            → (0.8.3, False) exact
        - pragma solidity ^0.8.0;           → (0.8.0, True) caret
        - pragma solidity >=0.6.0 <0.8.0;   → (0.7.6, False) range (uses highest)
        - pragma solidity =0.8.17;          → (0.8.17, False) exact
        
        Args:
            contract_path: Path to Solidity file
            
        Returns:
            (version_to_use, has_caret) tuple
        """
        try:
            content = contract_path.read_text(encoding="utf-8")
            
            # Find pragma line
            pragma_match = re.search(r'pragma\s+solidity\s+([^;]+);', content)
            if not pragma_match:
                logger.warning(f"No pragma in {contract_path.name}")
                return "0.8.20", False
            
            pragma_text = pragma_match.group(1).strip()
            
            # ================================================================
            # CASE 1: CARET PRAGMA (^0.8.0)
            # ================================================================
            if '^' in pragma_text:
                version_match = re.search(r'([\d.]+)', pragma_text)
                if version_match:
                    version = version_match.group(1)
                    logger.debug(f"Caret pragma: ^{version}")
                    return version, True
            
            # ================================================================
            # CASE 2: RANGE PRAGMA (>=0.6.0 <0.8.0)
            # ================================================================
            elif '>=' in pragma_text or '<' in pragma_text:
                versions = re.findall(r'([\d.]+)', pragma_text)
                if not versions:
                    logger.warning(f"No versions in range pragma: {pragma_text}")
                    return "0.8.20", False
                
                # Find highest compatible version in installed versions
                try:
                    min_version = versions[0]
                    max_version = versions[1] if len(versions) > 1 else None
                    
                    min_parts = tuple(map(int, min_version.split('.')))
                    compatible = []
                    
                    for v in self._installed_versions:
                        v_parts = tuple(map(int, v.split('.')))
                        
                        # Check if >= min_version
                        if v_parts < min_parts:
                            continue
                        
                        # Check if < max_version (if specified)
                        if max_version:
                            max_parts = tuple(map(int, max_version.split('.')))
                            if v_parts >= max_parts:
                                continue
                        
                        compatible.append(v)
                    
                    if compatible:
                        best = max(compatible, key=lambda v: tuple(map(int, v.split('.'))))
                        logger.debug(f"Range pragma {pragma_text} → using {best}")
                        return best, False
                    else:
                        logger.warning(f"No compatible versions for {pragma_text}")
                        return min_version, False
                
                except Exception as e:
                    logger.error(f"Failed to parse range pragma: {e}")
                    return versions[0], False
            
            # ================================================================
            # CASE 3: EXACT VERSION (0.8.3 or =0.8.17)
            # ================================================================
            else:
                version_match = re.search(r'([\d.]+)', pragma_text)
                if version_match:
                    version = version_match.group(1)
                    logger.debug(f"Exact version: {version}")
                    return version, False
            
            # Fallback
            logger.warning(f"Could not parse pragma: {pragma_text}")
            return "0.8.20", False
        
        except Exception as e:
            logger.error(f"Version detection failed for {contract_path}: {e}")
            return "0.8.20", False
    
    def _find_best_version(self, required_version: str, has_caret: bool) -> str:
        """
        Find best installed version to use.
        
        Args:
            required_version: Version from pragma (e.g., "0.8.0")
            has_caret: Whether pragma had caret (^)
            
        Returns:
            Best version to use
        """
        try:
            major, minor, patch = map(int, required_version.split('.'))
        except ValueError:
            logger.warning(f"Invalid version format: {required_version}")
            return "0.8.20"
        
        if not has_caret:
            # No caret - use exact version if installed
            if required_version in self._installed_versions:
                return required_version
            
            # Not installed - find close match in same minor version
            compatible = [
                v for v in self._installed_versions
                if v.startswith(f"{major}.{minor}.")
            ]
            
            if compatible:
                best = max(compatible, key=lambda v: tuple(map(int, v.split('.'))))
                logger.info(f"Version {required_version} not installed, using {best}")
                return best
            
            logger.warning(f"No compatible version for {required_version}")
            return "0.8.20"
        
        else:
            # HAS CARET - find highest compatible version
            compatible = [
                v for v in self._installed_versions
                if self._is_caret_compatible(v, major, minor, patch)
            ]
            
            if compatible:
                best = max(compatible, key=lambda v: tuple(map(int, v.split('.'))))
                logger.info(f"Caret ^{required_version} → using {best}")
                return best
            
            if required_version in self._installed_versions:
                logger.warning(f"No higher versions for ^{required_version}")
                return required_version
            
            logger.warning(f"No compatible version for ^{required_version}")
            return "0.8.20"
    
    def _is_caret_compatible(self, version: str, req_major: int, req_minor: int, req_patch: int) -> bool:
        """
        Check if version is compatible with caret pragma.
        
        Caret rules (see semver.org):
        - ^1.2.3 means >=1.2.3 <2.0.0 (next major)
        - ^0.2.3 means >=0.2.3 <0.3.0 (next minor when major=0)
        - ^0.0.3 means >=0.0.3 <0.0.4 (next patch when major=0 and minor=0)
        
        Args:
            version: Version to check (e.g., "0.8.26")
            req_major, req_minor, req_patch: Required version components
            
        Returns:
            True if compatible
        """
        try:
            v_major, v_minor, v_patch = map(int, version.split('.'))
        except ValueError:
            return False
        
        # Must be same major version
        if v_major != req_major:
            return False
        
        # ================================================================
        # CASE 1: 0.0.x (major=0, minor=0)
        # ^0.0.3 means >=0.0.3 <0.0.4 (only same patch allowed)
        # ================================================================
        if req_major == 0 and req_minor == 0:
            return v_minor == 0 and v_patch == req_patch
        
        # ================================================================
        # CASE 2: 0.x.y (major=0, minor>0)
        # ^0.4.15 means >=0.4.15 <0.5.0 (next minor)
        # ================================================================
        if req_major == 0:
            # Must be same minor version
            if v_minor != req_minor:
                return False
            # Must be >= required patch
            return v_patch >= req_patch
        
        # ================================================================
        # CASE 3: x.y.z (major>0)
        # ^1.2.3 means >=1.2.3 <2.0.0 (next major)
        # ================================================================
        # Allow any minor >= required minor
        if v_minor < req_minor:
            return False
        # If same minor, check patch
        if v_minor == req_minor and v_patch < req_patch:
            return False
        
        return True
    
    def _set_solc_version(self, version: str) -> bool:
        """
        Switch to specific Solidity compiler version.
        Uses direct solc-select call for reliability.
        """
        try:
            result = subprocess.run(
                ["solc-select", "use", version],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            logger.debug(f"✓ Switched to Solidity {version}")
            return True
        except Exception as e:
            logger.error(f"Failed to switch to Solidity {version}: {e}")
            return False
    
    def analyze_contract(self, contract_path: Path, contract_name: str, metadata: Dict = None) -> Dict:
        """
        Extract ALL features from a single contract.
        
        🎓 COMPREHENSIVE VERSION: Extracts 89 features across 7 analysis stages
        
        THREAD-SAFE: Version switching + compilation are atomic.
        
        Args:
            contract_path: Path to .sol file OR directory with .sol files
            contract_name: Name of main contract to analyze
            metadata: Optional metadata to include (address, data_source, etc.)
            
        Returns:
            Dict with 89+ features:
            - 2 metadata (contract_name, file_path)
            - 23 vulnerability flags (has_reentrancy, etc.)
            - 3 severity counts (high, medium, low)
            - 9 detector statistics (confidence, types, etc.)
            - 4 risk scores (simple, weighted, category)
            - 17 AST features (complexity, LOC, etc.)
            - 25 graph features (CFG, call graph, data flow)
            - 8 semantic features (CEI violations, reentrancy guards)
            - 2 error tracking (failure_reason, error_message)
        """
        logger.info(f"Analyzing {contract_name}")
        
        combined_features = {
            'contract_name': contract_name,
            'file_path': str(contract_path),
        }
        
        # Add metadata early (before saving)
        if metadata:
            combined_features.update(metadata)
        
        try:
            # ================================================================
            # STEP 0: HANDLE MULTI-FILE CONTRACTS
            # ================================================================
            analysis_target = contract_path
            main_contract_file = None
            
            if contract_path.is_dir():
                logger.debug(f"{contract_name}: Multi-file contract detected")
                
                # Find main contract file
                main_candidates = list(contract_path.glob(f"{contract_name}.sol"))
                if not main_candidates:
                    main_candidates = [
                        f for f in contract_path.glob("*.sol")
                        if contract_name.lower() in f.stem.lower()
                    ]
                
                if not main_candidates:
                    main_candidates = list(contract_path.glob("*.sol"))
                
                if not main_candidates:
                    raise FileNotFoundError(f"No .sol files in {contract_path}")
                
                main_contract_file = main_candidates[0]
                
                # CRITICAL: Use absolute path to main file (not directory!)
                # Slither resolves imports relative to this file
                analysis_target = main_contract_file.resolve()
                
                logger.debug(
                    f"{contract_name}: Using {main_contract_file.name} "
                    f"({len(list(contract_path.glob('*.sol')))} files total)"
                )
            else:
                main_contract_file = contract_path
                analysis_target = contract_path.resolve()
            
            # ================================================================
            # STEP 1: DETECT VERSION + HANDLE PRAGMAS
            # ================================================================
            detected_version, has_caret = self._detect_solidity_version(main_contract_file)
            
            # ================================================================
            # STEP 2: FIND BEST INSTALLED VERSION
            # ================================================================
            required_version = self._find_best_version(detected_version, has_caret)
            
            # ================================================================
            # CRITICAL: LOCK AROUND VERSION SWITCH + COMPILATION
            # ================================================================
            with self._lock:
                if not self._set_solc_version(required_version):
                    raise EnvironmentError(
                        f"Solidity {required_version} not installed. "
                        f"Run: poetry run solc-select install {required_version}"
                    )
                
                # Compile with correct version
                try:
                    slither = Slither(
                        str(analysis_target),
                        solc="solc",
                        solc_disable_warnings=True,
                        solc_args="--optimize"
                    )
                
                except Exception as compile_error:
                    # Store full error (NO TRUNCATION!)
                    full_error = str(compile_error)
                    error_str = full_error.lower()
                    
                    # Categorize errors (preserve full message)
                    if any(kw in error_str for kw in [
                        '@openzeppelin', '@chainlink', 'node_modules',
                        'hardhat/console', 'file import callback not supported'
                    ]):
                        logger.warning(f"{contract_name}: Missing external libraries")
                        raise ImportError(f"External library imports: {full_error}")
                    
                    elif 'file not found' in error_str or 'source file not found' in error_str:
                        logger.warning(f"{contract_name}: File not found")
                        raise ImportError(f"File not found: {full_error}")
                    
                    elif any(kw in error_str for kw in [
                        'requires different compiler',
                        'source file requires different',
                        'version mismatch',
                        'does not satisfy the version pragma'
                    ]):
                        logger.warning(f"{contract_name}: Version mismatch")
                        raise ValueError(f"Version mismatch: {full_error}")
                    
                    elif any(kw in error_str for kw in [
                        'invalid option to --combined-json',
                        'unrecognised option',
                        'unknown option'
                    ]):
                        logger.warning(f"{contract_name}: Slither incompatible")
                        raise RuntimeError(f"Slither incompatibility: {full_error}")
                    
                    else:
                        logger.error(f"{contract_name}: Compilation error")
                        raise SyntaxError(f"Compilation error: {full_error}")
            
            # Lock released
            
            # ================================================================
            # STEP 3: REGISTER DETECTORS
            # ================================================================
            detector_classes = [
                getattr(detector_module, name)
                for name in dir(detector_module)
                if name[0].isupper()
            ]
            
            for detector_class in detector_classes:
                slither.register_detector(detector_class)
            
            logger.debug(f"✓ Registered {len(slither.detectors)} detectors")
            
            # ================================================================
            # STEP 4: EXTRACT VULNERABILITY FEATURES (39 features)
            # ================================================================
            vuln_analyzer = SlitherAnalyzer(slither)
            vuln_features = vuln_analyzer.extract_features(contract_name)
            
            combined_features.update({
                # ============================================================
                # ORIGINAL VULNERABILITY FLAGS (4)
                # ============================================================
                'has_reentrancy': vuln_features.has_reentrancy,
                'has_access_control_issues': vuln_features.has_access_control_issues,
                'has_timestamp_dependency': vuln_features.has_timestamp_dependency,
                'has_unchecked_call': vuln_features.has_unchecked_call,
                
                # ============================================================
                # ADDITIONAL VULNERABILITY FLAGS (19)
                # ============================================================
                'has_reentrancy_unlimited': vuln_features.has_reentrancy_unlimited,
                'has_reentrancy_benign': vuln_features.has_reentrancy_benign,
                'has_reentrancy_events': vuln_features.has_reentrancy_events,
                'has_unchecked_transfer': vuln_features.has_unchecked_transfer,
                'has_controlled_delegatecall': vuln_features.has_controlled_delegatecall,
                'has_delegatecall_loop': vuln_features.has_delegatecall_loop,
                'has_uninitialized_state': vuln_features.has_uninitialized_state,
                'has_uninitialized_storage': vuln_features.has_uninitialized_storage,
                'has_uninitialized_local': vuln_features.has_uninitialized_local,
                'has_tx_origin': vuln_features.has_tx_origin,
                'has_inline_assembly': vuln_features.has_inline_assembly,
                'has_locked_ether': vuln_features.has_locked_ether,
                'has_msg_value_loop': vuln_features.has_msg_value_loop,
                'has_shadowing_state': vuln_features.has_shadowing_state,
                'has_shadowing_builtin': vuln_features.has_shadowing_builtin,
                'has_shadowing_abstract': vuln_features.has_shadowing_abstract,
                'has_unused_state_vars': vuln_features.has_unused_state_vars,
                'has_unused_return_values': vuln_features.has_unused_return_values,
                'has_incorrect_solc_version': vuln_features.has_incorrect_solc_version,
                'has_floating_pragma': vuln_features.has_floating_pragma,
                'has_outdated_compiler': vuln_features.has_outdated_compiler,
                
                # ============================================================
                # SEVERITY COUNTS (3)
                # ============================================================
                'high_severity_count': vuln_features.high_severity_count,
                'medium_severity_count': vuln_features.medium_severity_count,
                'low_severity_count': vuln_features.low_severity_count,
                
                # ============================================================
                # DETECTOR STATISTICS (9)
                # ============================================================
                'high_confidence_detectors': vuln_features.high_confidence_detectors,
                'medium_confidence_detectors': vuln_features.medium_confidence_detectors,
                'low_confidence_detectors': vuln_features.low_confidence_detectors,
                'security_detectors_triggered': vuln_features.security_detectors_triggered,
                'optimization_detectors_triggered': vuln_features.optimization_detectors_triggered,
                'total_detector_hits': vuln_features.total_detector_hits,
                'unique_vulnerability_types': vuln_features.unique_vulnerability_types,
                'detectors_per_function': vuln_features.detectors_per_function,
                'detectors_per_loc': vuln_features.detectors_per_loc,
                
                # ============================================================
                # COMPOSITE RISK SCORES (4)
                # ============================================================
                'risk_score_simple': vuln_features.risk_score_simple,
                'risk_score_weighted': vuln_features.risk_score_weighted,
                'is_high_risk': vuln_features.is_high_risk,
                'contract_complexity_category': vuln_features.contract_complexity_category,
            })
            
            # ================================================================
            # STEP 5: EXTRACT AST FEATURES (17 features)
            # ================================================================
            # CRITICAL: Pass pre-compiled Slither object (no re-compilation!)
            ast_extractor = ASTFeatureExtractor(main_contract_file, slither_obj=slither)
            ast_features = ast_extractor.extract_features(contract_name)
            combined_features.update(ast_features)
            
            # ================================================================
            # STEP 6: EXTRACT GRAPH FEATURES (25 features)
            # ================================================================
            try:
                from chainguardian.feature_extraction.graph_extractor import GraphFeatureExtractor
                
                graph_extractor = GraphFeatureExtractor(slither)
                graph_features = graph_extractor.extract_features(contract_name)
                combined_features.update(graph_features)
                
                logger.debug(
                    f"{contract_name}: Graph features - "
                    f"{graph_features['cfg_num_cycles']} cycles, "
                    f"{graph_features['cg_num_external_calls']} ext calls"
                )
            
            except Exception as e:
                logger.warning(f"{contract_name}: Graph extraction failed - {e}")
                # Add default graph features
                combined_features.update({
                    # CFG features (8)
                    'cfg_num_nodes': 0, 'cfg_num_edges': 0, 'cfg_num_cycles': 0,
                    'cfg_max_depth': 0, 'cfg_avg_branching': 0.0, 'cfg_has_complex_loops': False,
                    'cfg_num_exit_points': 0, 'cfg_cyclomatic_total': 0,
                    # Call Graph features (10)
                    'cg_num_nodes': 0, 'cg_num_edges': 0, 'cg_max_call_depth': 0,
                    'cg_num_external_calls': 0, 'cg_external_call_ratio': 0.0,
                    'cg_has_cyclic_calls': False, 'cg_num_public_entry_points': 0,
                    'cg_num_internal_functions': 0, 'cg_avg_calls_per_function': 0.0,
                    'cg_num_leaf_functions': 0,
                    # Data Flow features (7)
                    'dfg_num_state_vars': 0, 'dfg_num_tainted_flows': 0,
                    'dfg_has_cross_function_flow': False, 'dfg_num_sensitive_sinks': 0,
                    'dfg_num_external_sources': 0, 'dfg_taint_to_sink_ratio': 0.0,
                    'dfg_num_unvalidated_inputs': 0
                })
            
            # ================================================================
            # STEP 7: EXTRACT SEMANTIC SECURITY FEATURES (8 features) - NEW!
            # ================================================================
            # WHY: Detect CEI violations, reentrancy guards, and safe patterns
            # that pure syntactic analysis misses
            try:
                # Find the contract object in Slither's compilation
                target_contract = None
                for contract in slither.contracts:
                    if contract.name == contract_name:
                        target_contract = contract
                        break
                
                if target_contract:
                    semantic_features = extract_semantic_features(target_contract)
                    combined_features.update(semantic_features)
                    
                    logger.debug(
                        f"{contract_name}: Semantic features - "
                        f"CEI score: {semantic_features['cei_pattern_score']:.2f}, "
                        f"Violations: {semantic_features['cei_violations']}, "
                        f"Guard: {semantic_features['has_reentrancy_guard']}"
                    )
                else:
                    logger.warning(f"{contract_name}: Contract not found in compilation")
                    raise ValueError(f"Contract {contract_name} not found")
            
            except Exception as e:
                logger.warning(f"{contract_name}: Semantic feature extraction failed - {e}")
                # Add default semantic features
                combined_features.update({
                    'cei_violations': 0,
                    'cei_safe_functions': 0,
                    'cei_pattern_score': 1.0,
                    'has_reentrancy_guard': False,
                    'functions_with_reentrancy_guard': 0,
                    'state_before_call_count': 0,
                    'state_after_call_count': 0,
                    'unchecked_calls_in_critical_context': 0,
                })
            
            logger.info(f"✓ {contract_name}: {len(combined_features)} features extracted")
            
            # ================================================================
            # ERROR HANDLING: EXPECTED FAILURES
            # ================================================================
        except (ImportError, ValueError, RuntimeError, SyntaxError, FileNotFoundError, EnvironmentError) as e:
            # Categorize expected failures
            if isinstance(e, ImportError):
                failure_reason = "IMPORT_ERROR"
            elif isinstance(e, ValueError):
                failure_reason = "VERSION_MISMATCH"
            elif isinstance(e, RuntimeError):
                failure_reason = "SLITHER_INCOMPATIBILITY"
            elif isinstance(e, SyntaxError):
                failure_reason = "COMPILATION_ERROR"
            elif isinstance(e, FileNotFoundError):
                failure_reason = "NO_SOURCE_FILES"
            elif isinstance(e, EnvironmentError):
                failure_reason = "COMPILER_NOT_INSTALLED"
            else:
                failure_reason = "UNKNOWN_ERROR"
            
            logger.debug(f"{contract_name}: {failure_reason}")
            
            # ============================================================
            # POPULATE ALL 89 FEATURES WITH DEFAULTS
            # ============================================================
            combined_features.update(self._get_default_features(failure_reason, str(e)))
        
        # ================================================================
        # ERROR HANDLING: UNEXPECTED FAILURES
        # ================================================================
        except Exception as e:
            # Unexpected errors
            logger.error(
                f"{contract_name}: UNEXPECTED ERROR - {type(e).__name__}: {e}",
                exc_info=True
            )
            combined_features.update(self._get_default_features("UNEXPECTED_ERROR", str(e)))
        
        # ================================================================
        # SAVE TO DATABASE (Thread-safe)
        # ================================================================
        with self._lock:
            #self.features.append(combined_features)
            try:
                contract_id = self.db.save_contract_and_features(combined_features)
                logger.debug(f"Saved to database: contract_id={contract_id}")
            except Exception as e:
                logger.error(f"Failed to save to database: {e}")
        
        return combined_features
    
    def _get_default_features(self, failure_reason: str, error_message: str) -> Dict:
        """
        Get default feature values for failed extractions.
        
        Args:
            failure_reason: Categorized failure type
            error_message: Full error message
            
        Returns:
            Dict with all 89 features set to safe defaults
        """
        return {
            # VULNERABILITY FLAGS (23) - All False
            'has_reentrancy': False,
            'has_access_control_issues': False,
            'has_timestamp_dependency': False,
            'has_unchecked_call': False,
            'has_reentrancy_unlimited': False,
            'has_reentrancy_benign': False,
            'has_reentrancy_events': False,
            'has_unchecked_transfer': False,
            'has_controlled_delegatecall': False,
            'has_delegatecall_loop': False,
            'has_uninitialized_state': False,
            'has_uninitialized_storage': False,
            'has_uninitialized_local': False,
            'has_tx_origin': False,
            'has_inline_assembly': False,
            'has_locked_ether': False,
            'has_msg_value_loop': False,
            'has_shadowing_state': False,
            'has_shadowing_builtin': False,
            'has_shadowing_abstract': False,
            'has_unused_state_vars': False,
            'has_unused_return_values': False,
            'has_incorrect_solc_version': False,
            'has_floating_pragma': False,
            'has_outdated_compiler': False,
            
            # SEVERITY COUNTS (3) - All 0
            'high_severity_count': 0,
            'medium_severity_count': 0,
            'low_severity_count': 0,
            
            # AST FEATURES (17) - All 0
            'num_functions': 0,
            'num_external_calls': 0,
            'num_state_vars': 0,
            'num_modifiers': 0,
            'max_cyclomatic_complexity': 0,
            'num_low_level_calls': 0,
            'lines_of_code': 0,
            'num_contracts_in_file': 1,
            'num_dependencies': 0,
            'avg_function_complexity': 0.0,
            'num_functions_high_complexity': 0,
            'num_comments': 0,
            'comment_to_code_ratio': 0.0,
            'num_payable_functions': 0,
            'num_library_calls': 0,
            'inheritance_depth': 0,
            'num_unused_functions': 0,
            
            # DETECTOR STATISTICS (9) - All 0
            'high_confidence_detectors': 0,
            'medium_confidence_detectors': 0,
            'low_confidence_detectors': 0,
            'security_detectors_triggered': 0,
            'optimization_detectors_triggered': 0,
            'total_detector_hits': 0,
            'unique_vulnerability_types': 0,
            'detectors_per_function': 0.0,
            'detectors_per_loc': 0.0,
            
            # RISK SCORES (4) - Defaults
            'risk_score_simple': 0.0,
            'risk_score_weighted': 0.0,
            'is_high_risk': False,
            'contract_complexity_category': 'simple',
            
            # GRAPH FEATURES (25) - All 0
            'cfg_num_nodes': 0, 'cfg_num_edges': 0, 'cfg_num_cycles': 0,
            'cfg_max_depth': 0, 'cfg_avg_branching': 0.0, 'cfg_has_complex_loops': False,
            'cfg_num_exit_points': 0, 'cfg_cyclomatic_total': 0,
            'cg_num_nodes': 0, 'cg_num_edges': 0, 'cg_max_call_depth': 0,
            'cg_num_external_calls': 0, 'cg_external_call_ratio': 0.0,
            'cg_has_cyclic_calls': False, 'cg_num_public_entry_points': 0,
            'cg_num_internal_functions': 0, 'cg_avg_calls_per_function': 0.0,
            'cg_num_leaf_functions': 0,
            'dfg_num_state_vars': 0, 'dfg_num_tainted_flows': 0,
            'dfg_has_cross_function_flow': False, 'dfg_num_sensitive_sinks': 0,
            'dfg_num_external_sources': 0, 'dfg_taint_to_sink_ratio': 0.0,
            'dfg_num_unvalidated_inputs': 0,
            
            # SEMANTIC FEATURES (8) - Safe defaults
            'cei_violations': 0,
            'cei_safe_functions': 0,
            'cei_pattern_score': 1.0,
            'has_reentrancy_guard': False,
            'functions_with_reentrancy_guard': 0,
            'state_before_call_count': 0,
            'state_after_call_count': 0,
            'unchecked_calls_in_critical_context': 0,
            
            # ERROR TRACKING (2)
            'failure_reason': failure_reason,
            'error_message': error_message[:2000],  # Store full error (up to 2000 chars)
        }
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert collected features to pandas DataFrame."""
        if not self.features:
            logger.warning("No features collected yet")
            return pd.DataFrame()
        
        df = pd.DataFrame(self.features)
        logger.info(f"DataFrame: {len(df)} contracts × {len(df.columns)} features")
        return df
    
    def print_diagnostic_summary(self):
        """Print detailed diagnostic summary."""
        if not self.features:
            logger.warning("No features collected yet")
            return
        
        print("\n" + "="*70)
        print("FEATURE EXTRACTION DIAGNOSTIC SUMMARY")
        print("="*70)
        
        total = len(self.features)
        failures = {}
        successes = 0
        zero_feature_clean = 0
        
        for feature_dict in self.features:
            failure_reason = feature_dict.get('failure_reason', None)
            if failure_reason:
                failures[failure_reason] = failures.get(failure_reason, 0) + 1
            else:
                has_features = any([
                    feature_dict.get('high_severity_count', 0) > 0,
                    feature_dict.get('medium_severity_count', 0) > 0,
                    feature_dict.get('low_severity_count', 0) > 0,
                    feature_dict.get('num_functions', 0) > 0,
                    feature_dict.get('num_external_calls', 0) > 0,
                ])
                
                if has_features:
                    successes += 1
                else:
                    zero_feature_clean += 1
        
        print(f"\n📊 Overall Results:")
        print(f"   Total: {total}")
        print(f"   ✅ Features: {successes} ({successes/total*100:.1f}%)")
        print(f"   ⚪ Clean: {zero_feature_clean} ({zero_feature_clean/total*100:.1f}%)")
        print(f"   ❌ Failed: {sum(failures.values())} ({sum(failures.values())/total*100:.1f}%)")
        
        if failures:
            print(f"\n🔍 Failure Breakdown:")
            status_map = {
                "IMPORT_ERROR": ("EXPECTED ✓", "External libraries (@openzeppelin, etc.)"),
                "VERSION_MISMATCH": ("INVESTIGATE ⚠️", "Check pragma handling"),
                "SLITHER_INCOMPATIBILITY": ("EXPECTED ✓", "Contract too old (< 0.4.11)"),
                "COMPILATION_ERROR": ("INVESTIGATE ❓", "Real syntax errors"),
                "NO_SOURCE_FILES": ("CHECK DATA 📁", "Download issue"),
                "COMPILER_NOT_INSTALLED": ("FIXABLE 🔧", "Install compiler version"),
            }
            
            for reason, count in sorted(failures.items(), key=lambda x: x[1], reverse=True):
                percentage = count / total * 100
                status, description = status_map.get(reason, ("INVESTIGATE ❓", "Check logs"))
                print(f"\n   {reason}: {count} ({percentage:.1f}%)")
                print(f"      Status: {status}")
                print(f"      Fix: {description}")
        
        print(f"\n" + "="*70)
        print("🎯 RECOMMENDATIONS")
        print("="*70)
        
        expected = sum([
            failures.get('IMPORT_ERROR', 0),
            failures.get('SLITHER_INCOMPATIBILITY', 0)
        ])
        
        if expected > 0:
            usable = successes + zero_feature_clean
            total_usable = total - expected
            rate = (usable / total_usable * 100) if total_usable > 0 else 0
            
            print(f"\n✅ EXPECTED FAILURES: {expected} contracts")
            print(f"   Cannot be analyzed without infrastructure changes")
            print(f"   Usable contracts: {usable}/{total_usable} ({rate:.0f}%)")
        
        if successes > 0:
            print(f"\n✅ READY FOR ML: {successes} contracts with features")
        
        if zero_feature_clean > 0:
            print(f"\n⚪ CLEAN CONTRACTS: {zero_feature_clean} (keep as negatives)")
        
        if failures.get('VERSION_MISMATCH', 0) > 10:
            print(f"\n⚠️  WARNING: {failures['VERSION_MISMATCH']} VERSION_MISMATCH errors")
            print(f"   Check error_message column in CSV for details")
        
        print("="*70 + "\n")
    
    def save_dataset(self, output_path: Path):
        """
        Save features as CSV and print diagnostics.
        
        🎓 NEW: Now exports from database instead of memory list
        This means data is preserved even if script crashes
        """
        # Get data from database
        df = self.db.get_all_features()
        
        if df.empty:
            logger.warning("No data in database to export")
            return
        
        # Save to CSV (for backwards compatibility)
        df.to_csv(output_path, index=False)
        logger.info(f"✅ Exported {len(df)} contracts from database to {output_path}")
        
        # Print stats from database
        stats = self.db.get_stats()
        logger.info(f"📊 Database stats: {stats}")
        
        self.print_diagnostic_summary()
