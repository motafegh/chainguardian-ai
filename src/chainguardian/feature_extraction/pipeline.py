"""
Unified Feature Extraction Pipeline - REFACTORED WITH TIER-BASED ARCHITECTURE
===============================================================================

Thread-safe multi-version Solidity compilation with tier-based feature extraction.

KEY FEATURES:
- Tier-based modular architecture (Tier 1-4)
- Mode-based extraction (comprehensive/maximum/optimized)
- Auto-discovery of Slither detectors (future-proof)
- Direct Slither API usage (no redundancy)
- Single-pass extraction per tier
- Thread-safe parallel processing

TIER ARCHITECTURE:
- Tier 1: Core Features (56) - Detectors + API + Complexity + LOC + Risk
- Tier 2: Semantic + Graph (33) - CEI + CFG + Call Graph + Data Flow
- Tier 3: Advanced (68) - SlithIR + Extended API + Aggregations
- Tier 4: Individual Detectors (69) - One boolean per detector

EXTRACTION MODES:
- comprehensive: Tiers 1+2+3 (157 features, 8-10 sec)
- maximum: Tiers 1+2+3+4 (226 features, 14-16 sec)
- optimized: Tier 1+2 (89 features, 6-8 sec)

TOTAL: Up to 226 features (mode-dependent)
"""

from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import logging
import re
import subprocess
from threading import Lock
from slither import Slither

# Import new tier modules
from .tier1_core import extract_tier1_features
from .tier2_semantic_graph import extract_tier2_features
from .tier3_advanced import extract_tier3_features, compute_tier3_aggregations
from .tier4_detectors import extract_tier4_features
from .utils import resolve_contract, categorize_error
from .feature_spec import (
    get_default_feature_dict,
    get_features_for_mode,
    MODE_TIER_MAPPING
)

logger = logging.getLogger(__name__)


class FeaturePipeline:
    """
    End-to-end pipeline: Contract → Feature Vector → ML-ready format

    Thread-safe for parallel feature extraction across multiple contracts.
    Tier-based architecture for modular, efficient extraction.

    Args:
        mode: Extraction mode ('comprehensive', 'maximum', 'optimized')
            - comprehensive: 157 features (Tiers 1+2+3)
            - maximum: 226 features (Tiers 1+2+3+4)
            - optimized: 89 features (Tiers 1+2)
    """

    def __init__(self, mode: str = "comprehensive"):
        """Initialize pipeline with mode selection and version cache."""
        from chainguardian.database.manager import DatabaseManager

        # Validate mode
        if mode not in MODE_TIER_MAPPING:
            logger.warning(f"Invalid mode '{mode}', defaulting to 'comprehensive'")
            mode = "comprehensive"

        self.mode = mode
        self.enabled_tiers = MODE_TIER_MAPPING[mode]

        self.db = DatabaseManager()
        logger.info(f"✅ Database connection ready")
        logger.info(f"🎯 Extraction mode: {mode} ({len(get_features_for_mode(mode))} features)")

        self._lock = Lock()  # Protects version switching + compilation

        # Cache installed versions
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
                    # Parse version from output (e.g., "0.8.20 (current)" or "0.4.26")
                    match = re.search(r'(\d+\.\d+\.\d+)', line)
                    if match:
                        versions.add(match.group(1))

            return versions

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"Failed to get installed Solidity versions: {e}")
            return set()

    def _detect_solidity_version(self, contract_path: Path) -> Optional[str]:
        """
        Detect required Solidity version from pragma statement.

        Handles:
        - Exact: pragma solidity 0.8.0;
        - Caret: pragma solidity ^0.8.0;
        - Range: pragma solidity >=0.4.22 <0.9.0;

        Args:
            contract_path: Path to .sol file

        Returns:
            Required version string (e.g., '0.8.20') or None if not found
        """
        try:
            source_code = contract_path.read_text(encoding='utf-8')

            # Find pragma solidity statement (get first occurrence)
            pragma_pattern = r'pragma\s+solidity\s+([^;]+);'
            match = re.search(pragma_pattern, source_code, re.IGNORECASE | re.MULTILINE)

            if not match:
                logger.warning(f"No pragma found in {contract_path.name}")
                return None

            pragma_value = match.group(1).strip()
            logger.debug(f"Found pragma: pragma solidity {pragma_value};")

            # Parse pragma
            if pragma_value.startswith('^'):
                # Caret: ^0.8.0 -> use 0.8.x
                base_version = pragma_value[1:].strip()
                # Extract version number (with or without patch)
                version_match = re.match(r'(\d+\.\d+\.\d+)', base_version)
                if version_match:
                    return self._find_best_version(version_match.group(1), caret=True)
                # Try without patch version (e.g., ^0.8)
                version_match = re.match(r'(\d+\.\d+)', base_version)
                if version_match:
                    return self._find_best_version(version_match.group(1) + '.0', caret=True)

            elif '>=' in pragma_value:
                # Range: >=0.4.22 <0.9.0 or >=0.4.22
                lower_match = re.search(r'>=\s*(\d+\.\d+\.\d+)', pragma_value)
                upper_match = re.search(r'<\s*(\d+\.\d+\.\d+)', pragma_value)

                if lower_match:
                    lower_ver = lower_match.group(1)
                    upper_ver = upper_match.group(1) if upper_match else None
                    return self._find_best_version_in_range(lower_ver, upper_ver)

                # Also try without patch version
                lower_match = re.search(r'>=\s*(\d+\.\d+)', pragma_value)
                upper_match = re.search(r'<\s*(\d+\.\d+)', pragma_value)

                if lower_match:
                    lower_ver = lower_match.group(1) + '.0'
                    upper_ver = upper_match.group(1) + '.0' if upper_match else None
                    return self._find_best_version_in_range(lower_ver, upper_ver)

            else:
                # Exact or simple version: 0.8.0 or 0.8.20
                version_match = re.match(r'(\d+\.\d+\.\d+)', pragma_value)
                if version_match:
                    return self._find_best_version(version_match.group(1), caret=False)
                # Try without patch version (e.g., "0.8")
                version_match = re.match(r'(\d+\.\d+)', pragma_value)
                if version_match:
                    return self._find_best_version(version_match.group(1) + '.0', caret=True)

            logger.warning(f"Could not parse pragma value: {pragma_value}")
            return None

        except Exception as e:
            logger.error(f"Failed to detect version for {contract_path.name}: {e}")
            return None

    def _find_best_version_in_range(self, lower_version: str, upper_version: Optional[str] = None) -> Optional[str]:
        """
        Find best installed version within a range.

        Args:
            lower_version: Minimum version (inclusive, e.g., '0.4.22')
            upper_version: Maximum version (exclusive, e.g., '0.6.0') or None for no upper limit

        Returns:
            Best matching installed version or None
        """
        try:
            lower_parts = lower_version.split('.')
            if len(lower_parts) < 3:
                return None

            lower_maj, lower_min, lower_patch = int(lower_parts[0]), int(lower_parts[1]), int(lower_parts[2])

            upper_maj, upper_min, upper_patch = None, None, None
            if upper_version:
                upper_parts = upper_version.split('.')
                if len(upper_parts) >= 3:
                    upper_maj, upper_min, upper_patch = int(upper_parts[0]), int(upper_parts[1]), int(upper_parts[2])

            # Find matching versions
            candidates = []
            for installed in self._installed_versions:
                inst_parts = installed.split('.')
                if len(inst_parts) < 3:
                    continue

                try:
                    inst_maj, inst_min, inst_patch = int(inst_parts[0]), int(inst_parts[1]), int(inst_parts[2])
                except ValueError:
                    continue

                # Check lower bound (inclusive)
                if (inst_maj, inst_min, inst_patch) < (lower_maj, lower_min, lower_patch):
                    continue

                # Check upper bound (exclusive)
                if upper_maj is not None:
                    if (inst_maj, inst_min, inst_patch) >= (upper_maj, upper_min, upper_patch):
                        continue

                candidates.append((installed, inst_maj, inst_min, inst_patch))

            if not candidates:
                range_str = f">={lower_version}"
                if upper_version:
                    range_str += f" <{upper_version}"
                logger.warning(f"No matching version for range {range_str}")
                return None

            # Return highest matching version within range
            candidates.sort(key=lambda x: (x[1], x[2], x[3]), reverse=True)
            best_version = candidates[0][0]
            logger.debug(f"Selected version {best_version} for range >={lower_version} <{upper_version or 'inf'}")
            return best_version

        except Exception as e:
            logger.error(f"Failed to find version in range {lower_version}-{upper_version}: {e}")
            return None

    def _find_best_version(self, requested_version: str, caret: bool = False) -> Optional[str]:
        """
        Find best installed version matching requested version.

        Args:
            requested_version: Version string (e.g., '0.8.0')
            caret: If True, match same major.minor (e.g., 0.8.x)

        Returns:
            Best matching installed version or None
        """
        try:
            req_parts = requested_version.split('.')
            if len(req_parts) < 3:
                logger.warning(f"Invalid version format: {requested_version}")
                return None

            req_major, req_minor, req_patch = int(req_parts[0]), int(req_parts[1]), int(req_parts[2])

            # Find matching versions
            candidates = []
            for installed in self._installed_versions:
                inst_parts = installed.split('.')
                if len(inst_parts) < 3:
                    continue

                try:
                    inst_major, inst_minor, inst_patch = int(inst_parts[0]), int(inst_parts[1]), int(inst_parts[2])
                except ValueError:
                    continue

                if caret:
                    # Caret: same major.minor, any patch >= requested
                    if inst_major == req_major and inst_minor == req_minor and inst_patch >= req_patch:
                        candidates.append((installed, inst_major, inst_minor, inst_patch))
                else:
                    # Exact or range: any version >= requested
                    if (inst_major, inst_minor, inst_patch) >= (req_major, req_minor, req_patch):
                        candidates.append((installed, inst_major, inst_minor, inst_patch))

            if not candidates:
                logger.warning(
                    f"No matching version for {requested_version} (caret={caret}). "
                    f"Need: {req_major}.{req_minor}.{req_patch}+"
                )
                return None

            # Return highest matching version (sort by major, minor, patch)
            candidates.sort(key=lambda x: (x[1], x[2], x[3]), reverse=True)
            best_version = candidates[0][0]
            logger.debug(f"Selected version {best_version} for requirement {requested_version} (caret={caret})")
            return best_version

        except Exception as e:
            logger.error(f"Failed to find best version for {requested_version}: {e}")
            return None

    def _compile_contract(self, contract_path: Path) -> Slither:
        """
        Compile contract with appropriate Solidity version.

        Thread-safe version switching with compilation lock.
        Handles external dependencies with common remappings.

        Args:
            contract_path: Path to .sol file

        Returns:
            Slither object

        Raises:
            Various exceptions for compilation failures
        """
        with self._lock:
            # Detect required version
            required_version = self._detect_solidity_version(contract_path)

            if required_version:
                logger.debug(f"Switching to Solidity {required_version}")
                try:
                    subprocess.run(
                        ["solc-select", "use", required_version],
                        capture_output=True,
                        text=True,
                        check=True,
                        timeout=10
                    )
                except Exception as e:
                    logger.warning(f"Failed to switch version to {required_version}: {e}")
                    # Don't fail here, let Slither try anyway

            # Strategy: Try multiple compilation approaches
            compilation_strategies = []

            # Strategy 1: Direct compilation
            compilation_strategies.append(("direct", {}))

            # Strategy 2: With remappings
            remappings = self._get_dependency_remappings(contract_path)
            if remappings:
                compilation_strategies.append(("with_remappings", {"solc_remaps": remappings}))

            # Strategy 3: With solc_working_dir set to contract directory
            compilation_strategies.append((
                "with_working_dir",
                {"solc_working_dir": str(contract_path.parent)}
            ))

            # Strategy 4: Combined remappings + working dir
            if remappings:
                compilation_strategies.append((
                    "combined",
                    {"solc_remaps": remappings, "solc_working_dir": str(contract_path.parent)}
                ))

            # Try each strategy
            last_error = None
            for strategy_name, kwargs in compilation_strategies:
                try:
                    logger.debug(f"Trying compilation strategy: {strategy_name}")
                    slither = Slither(str(contract_path), **kwargs)
                    logger.debug(f"✓ Compiled successfully with strategy: {strategy_name}")
                    return slither
                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()

                    # If it's a version error, don't try other strategies
                    if any(kw in error_str for kw in ['version', 'pragma', 'requires different']):
                        logger.debug(f"Version mismatch detected, skipping remaining strategies")
                        break

                    logger.debug(f"Strategy {strategy_name} failed: {str(e)[:100]}")
                    continue

            # All strategies failed
            if last_error:
                logger.error(f"All compilation strategies failed for {contract_path.name}")
                raise last_error
            else:
                raise RuntimeError(f"Compilation failed for {contract_path.name}")

    def _get_dependency_remappings(self, contract_path: Path) -> list:
        """
        Auto-detect common dependency remappings for the contract.

        Looks for node_modules, lib, or common dependency directories
        relative to the contract location.

        Args:
            contract_path: Path to .sol file

        Returns:
            List of remapping strings (e.g., '@openzeppelin/=node_modules/@openzeppelin/')
        """
        remappings = []
        contract_dir = contract_path.parent

        # Common dependency locations to search
        search_paths = [
            contract_dir / "node_modules",
            contract_dir.parent / "node_modules",
            contract_dir.parent.parent / "node_modules",
            contract_dir.parent.parent.parent / "node_modules",  # Go up more levels
            contract_dir / "lib",
            contract_dir.parent / "lib",
        ]

        # Also check if there's a parent "contracts" directory
        # This helps with structures like: contracts/subfolder/Contract.sol importing ../Other.sol
        current = contract_dir
        for _ in range(5):  # Check up to 5 levels up
            if current.name == "contracts":
                search_paths.append(current.parent / "node_modules")
                break
            if current.parent == current:  # Reached root
                break
            current = current.parent

        # Common remapping patterns
        # Note: OpenZeppelin v3.x has structure: @openzeppelin/contracts/contracts/...
        # So we need to map @openzeppelin/contracts/ to .../contracts/contracts/
        common_deps = {
            "@openzeppelin/contracts": ["contracts/contracts", "contracts"],  # Try nested structure first
            "@chainlink/contracts": ["contracts"],
            "@uniswap": [""],
            "@aave": [""],
            "hardhat": [""],  # For hardhat/console.sol
        }

        for dep, subpaths in common_deps.items():
            for search_path in search_paths:
                if not search_path.exists():
                    continue

                # Extract base dependency name (e.g., "@openzeppelin" from "@openzeppelin/contracts")
                base_dep = dep.split("/")[0]
                base_path = search_path / base_dep

                if not base_path.exists():
                    continue

                # Try different subpath variations
                for subpath in subpaths:
                    if subpath:
                        full_dep_path = base_path / subpath
                    else:
                        full_dep_path = base_path

                    if full_dep_path.exists() and full_dep_path.is_dir():
                        # Create remapping with absolute path
                        # Format: @openzeppelin/contracts/=/absolute/path/to/@openzeppelin/contracts/contracts/
                        remapping = f"{dep}/={full_dep_path.absolute()}/"
                        if remapping not in remappings:
                            remappings.append(remapping)
                            logger.debug(f"Found dependency remapping: {remapping}")
                        break  # Use first found location

        return remappings

    def analyze_contract(self, contract_path: Path, contract_name: str,
                        metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Extract features from contract using tier-based architecture.

        Args:
            contract_path: Path to .sol file
            contract_name: Name of contract to analyze
            metadata: Optional metadata (dataset, address, etc.)

        Returns:
            Dictionary with all extracted features + metadata
        """
        logger.info(f"📊 Analyzing {contract_name} in {self.mode} mode...")

        try:
            # Ensure absolute path for compilation
            if not isinstance(contract_path, Path):
                contract_path = Path(contract_path)
            contract_path = contract_path.resolve()

            # STEP 1: Compile contract
            slither = self._compile_contract(contract_path)

            # STEP 2: Resolve target contract
            contract = resolve_contract(slither, contract_name)
            if not contract:
                reason, msg = "CONTRACT_NOT_FOUND", f"No contract named {contract_name}"
                return get_default_feature_dict(reason, msg, contract_name, str(contract_path))

            # STEP 3: Run detectors once (shared across tiers)
            logger.debug("Running Slither detectors...")
            detector_results = slither.run_detectors()

            # STEP 4: Extract features tier-by-tier
            features = self._extract_all_features(slither, contract, detector_results)

            # STEP 5: Add metadata
            features['contract_name'] = contract_name
            features['file_path'] = str(contract_path)
            features['extraction_status'] = 'success'
            features['extraction_mode'] = self.mode

            if metadata:
                features.update(metadata)

            # STEP 6: Save to database (using V2 schema with 152-feature support)
            logger.debug("Saving features to database...")
            self.db.save_contract_and_features_v2(features)

            logger.info(f"✓ {contract_name}: Extracted {len(features)} features successfully")
            return features

        except Exception as e:
            # Categorize error and return defaults
            reason, msg = categorize_error(e)
            logger.error(f"✗ {contract_name}: {reason} - {msg}")
            return get_default_feature_dict(reason, msg, contract_name, str(contract_path))

    def _extract_all_features(self, slither: Slither, contract,
                             detector_results: list) -> Dict[str, Any]:
        """
        Coordinate tier-based feature extraction.

        Graceful degradation: Continue on partial failures.

        Args:
            slither: Slither object
            contract: Contract object
            detector_results: Pre-run detector results

        Returns:
            Dictionary with all features from enabled tiers
        """
        all_features = {}

        # TIER 1: Core Features (always enabled)
        try:
            tier1 = extract_tier1_features(slither, contract, detector_results)
            all_features.update(tier1)
            logger.debug(f"✓ Tier 1: {len(tier1)} features")
        except Exception as e:
            logger.warning(f"Tier 1 extraction failed: {e}")

        # TIER 2: Semantic + Graph
        if 'tier2' in self.enabled_tiers:
            try:
                tier2 = extract_tier2_features(contract)
                all_features.update(tier2)
                logger.debug(f"✓ Tier 2: {len(tier2)} features")
            except Exception as e:
                logger.warning(f"Tier 2 extraction failed: {e}")
        else:
            tier2 = {}

        # TIER 3: Advanced (SlithIR + Aggregations)
        if 'tier3' in self.enabled_tiers:
            try:
                tier3 = extract_tier3_features(slither, contract)
                all_features.update(tier3)

                # Recompute aggregations with full context
                aggregations = compute_tier3_aggregations(
                    tier1_features=tier1 if 'tier1' in locals() else {},
                    tier2_features=tier2 if 'tier2' in locals() else {},
                    tier3_features=tier3
                )
                all_features.update(aggregations)

                logger.debug(f"✓ Tier 3: {len(tier3)} features")
            except Exception as e:
                logger.warning(f"Tier 3 extraction failed: {e}")

        # TIER 4: Individual Detectors
        if 'tier4' in self.enabled_tiers:
            try:
                tier4 = extract_tier4_features(slither, contract, detector_results)
                all_features.update(tier4)
                logger.debug(f"✓ Tier 4: {len(tier4)} features")
            except Exception as e:
                logger.warning(f"Tier 4 extraction failed: {e}")

        return all_features

    def batch_extract(self, contracts: list, output_csv: Optional[Path] = None) -> pd.DataFrame:
        """
        Extract features from multiple contracts.

        Args:
            contracts: List of (contract_path, contract_name, metadata) tuples
            output_csv: Optional path to save CSV

        Returns:
            DataFrame with all extracted features
        """
        logger.info(f"🚀 Starting batch extraction: {len(contracts)} contracts in {self.mode} mode")

        results = []
        for i, contract_info in enumerate(contracts, 1):
            if len(contract_info) == 2:
                contract_path, contract_name = contract_info
                metadata = {}
            else:
                contract_path, contract_name, metadata = contract_info

            logger.info(f"[{i}/{len(contracts)}] Processing {contract_name}...")

            features = self.analyze_contract(
                Path(contract_path),
                contract_name,
                metadata
            )
            results.append(features)

        # Create DataFrame
        df = pd.DataFrame(results)

        if output_csv:
            df.to_csv(output_csv, index=False)
            logger.info(f"✅ Saved {len(df)} contracts to {output_csv}")

        logger.info(f"✅ Batch extraction complete: {len(df)} contracts processed")
        return df
