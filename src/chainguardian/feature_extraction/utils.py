"""
Utility functions for feature extraction.
Centralized contract resolution and error handling.
"""

from typing import Optional, Tuple
from slither import Slither
from slither.core.declarations import Contract
import logging

logger = logging.getLogger(__name__)


def resolve_contract(slither: Slither, contract_name: str) -> Optional[Contract]:
    """
    3-stage contract lookup with fuzzy matching fallback.

    Stage 1: Exact name match
    Stage 2: Fuzzy match (case-insensitive, ignore underscores/dashes)
    Stage 3: First non-interface, non-library contract

    Args:
        slither: Slither analysis object
        contract_name: Target contract name

    Returns:
        Contract object if found, None otherwise
    """
    if not slither.contracts:
        logger.warning(f"No contracts found in Slither analysis")
        return None

    # Stage 1: Exact match
    for contract in slither.contracts:
        if contract.name == contract_name:
            logger.debug(f"Exact match found: '{contract_name}'")
            return contract

    # Stage 2: Fuzzy match (case-insensitive, ignore underscores/dashes)
    name_clean = contract_name.lower().replace('_', '').replace('-', '')
    for contract in slither.contracts:
        contract_clean = contract.name.lower().replace('_', '').replace('-', '')
        if contract_clean in name_clean or name_clean in contract_clean:
            logger.info(f"Fuzzy matched '{contract_name}' -> '{contract.name}'")
            return contract

    # Stage 3: First non-interface, non-library contract
    for contract in slither.contracts:
        if not contract.is_interface and not contract.is_library:
            logger.info(f"Using first contract '{contract.name}' for '{contract_name}'")
            return contract

    logger.warning(f"No suitable contract found for '{contract_name}'")
    return None


def categorize_error(error: Exception) -> Tuple[str, str]:
    """
    Categorize compilation/analysis errors into standard failure reasons.

    Args:
        error: The exception that occurred

    Returns:
        Tuple of (failure_reason, error_message)

    Failure Reasons:
        - COMPILATION_ERROR: General compilation failure
        - IMPORT_ERROR: Missing external libraries
        - FILE_NOT_FOUND: Source file not found
        - VERSION_MISMATCH: Solidity version incompatibility
        - SLITHER_INCOMPATIBLE: Slither version incompatibility
        - ANALYSIS_ERROR: Slither analysis failure
        - UNKNOWN_ERROR: Uncategorized error
    """
    error_str = str(error).lower()
    error_type = type(error).__name__

    # Check for file not found FIRST (more specific)
    # Pattern: "file.sol" is not found, source file not found, etc.
    if any(kw in error_str for kw in [
        '" is not found',  # Slither: "file.sol" is not found
        'source file not found',
        'no such file',
        'cannot open'
    ]):
        return "FILE_NOT_FOUND", f"Source file not found: {error}"

    # Check for import/dependency errors
    if any(kw in error_str for kw in [
        '@openzeppelin', '@chainlink', 'node_modules',
        'hardhat/console', 'file import callback not supported',
        'import'  # General import-related errors (file not found already handled)
    ]):
        return "IMPORT_ERROR", f"Missing external libraries: {error}"

    # Check for version mismatch (expanded patterns)
    if any(kw in error_str for kw in [
        'requires different compiler',
        'source file requires different',
        'version mismatch',
        'does not satisfy the version pragma',
        'solidityversion',  # Slither version checks
        'solc-select',  # Version selection errors
        'error: no matching version',
        'incompatible solc version',
        'requires solc version',
    ]):
        return "VERSION_MISMATCH", f"Solidity version incompatibility: {error}"

    # Check for Slither incompatibility
    if any(kw in error_str for kw in [
        'invalid option to --combined-json',
        'unrecognised option',
        'unknown option',
        'unsupported solc',
        'slither error'
    ]):
        return "SLITHER_INCOMPATIBLE", f"Slither version incompatibility: {error}"

    # Check for analysis errors
    if error_type in ['AttributeError', 'KeyError', 'IndexError', 'NoneType']:
        return "ANALYSIS_ERROR", f"Slither analysis failed: {error}"

    # Check for compilation errors (general)
    if any(kw in error_str for kw in [
        'compilation', 'syntax error', 'parsererror',
        'declarationerror', 'typeerror', 'undeclaredidentifier'
    ]):
        return "COMPILATION_ERROR", f"Compilation failed: {error}"

    # Default: unknown error
    return "UNKNOWN_ERROR", f"Unexpected error ({error_type}): {error}"
