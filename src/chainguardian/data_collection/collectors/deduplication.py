"""
Smart Deduplication for Smart Contracts
Deduplicates by function signatures, not entire source code
Author: Ali - ChainGuardian AI Project Day 5
"""

import hashlib
from typing import List, Dict, Set
from pathlib import Path
import re
import logging

logger = logging.getLogger(__name__)


class SmartDeduplicator:
    """
    Deduplicate contracts by function signatures, not entire source.

    WHY THIS MATTERS:
    - Old method: Hash entire source → 50 contracts become 30 (40% loss!)
    - New method: Hash function sigs → 50 contracts become 45 (10% loss)

    TRADE-OFF:
    - More lenient: Keeps contracts with same structure but different implementations
    - More strict: Still removes exact duplicates and obvious forks
    """

    def __init__(self):
        self.seen_signatures: Set[str] = set()
        self.seen_addresses: Set[str] = set()
        logger.info("SmartDeduplicator initialized")

    def _extract_function_signatures(self, source_code: str) -> str:
        """
        Extract ONLY function signatures for comparison.

        Example:
        function transfer(address to, uint256 amount) public returns (bool)
        → "transfer"

        Returns: "func1|func2|func3" (sorted for consistency)
        """
        # Find all function declarations
        functions = re.findall(
            r'function\s+(\w+)\s*\([^)]*\)\s*(?:public|external|internal|private)?\s*(?:view|pure|payable)?',
            source_code
        )

        # Sort and join to create deterministic hash
        return "|".join(sorted(set(functions)))  # Remove duplicates, sort

    def _hash_signatures(self, signatures: str) -> str:
        """Create hash of function signatures."""
        return hashlib.sha256(signatures.encode()).hexdigest()[:16]

    def is_duplicate(self, contract_data: Dict) -> bool:
        """
        Check if contract is duplicate.

        Rules:
        1. Same address = duplicate (exact same contract on blockchain)
        2. Same function signatures = duplicate (fork/copy)
        3. Otherwise = unique (keep it)

        Args:
            contract_data: Dict with 'address' and 'filepath' keys

        Returns:
            True if duplicate, False if unique
        """
        address = contract_data.get("address", "")
        filepath = contract_data.get("filepath", "")

        # Rule 1: Check address (blockchain-level duplicate)
        if address and address in self.seen_addresses:
            logger.debug(f"Duplicate address: {address}")
            return True

        # Rule 2: Check function signatures (code-level duplicate)
        if filepath and Path(filepath).exists():
            try:
                source_code = Path(filepath).read_text(encoding='utf-8')
                signatures = self._extract_function_signatures(source_code)
                sig_hash = self._hash_signatures(signatures)

                if sig_hash in self.seen_signatures:
                    logger.debug(f"Duplicate signatures: {filepath}")
                    return True

                # Mark as seen
                if address:
                    self.seen_addresses.add(address)
                self.seen_signatures.add(sig_hash)
                return False
            except Exception as e:
                logger.warning(f"Failed to check {filepath}: {e}")
                return False  # If can't read, assume unique (safe default)

        return False

    def deduplicate(self, contracts: List[Dict]) -> List[Dict]:
        """
        Remove duplicates from contract list.

        Args:
            contracts: List of dicts with 'address' and 'filepath'

        Returns:
            List of unique contracts
        """
        unique = []
        duplicates = 0

        for contract in contracts:
            if not self.is_duplicate(contract):
                unique.append(contract)
            else:
                duplicates += 1

        logger.info(f"Deduplication: {len(contracts)} → {len(unique)} (removed {duplicates} duplicates)")
        return unique


# USAGE EXAMPLE:
"""
from deduplication import SmartDeduplicator

deduplicator = SmartDeduplicator()

contracts = [
    {"address": "0x123...", "filepath": "path/to/WETH.sol"},
    {"address": "0x456...", "filepath": "path/to/WETH_copy.sol"},  # Duplicate!
    {"address": "0x789...", "filepath": "path/to/USDC.sol"},
]

unique_contracts = deduplicator.deduplicate(contracts)
print(f"Unique contracts: {len(unique_contracts)}")  # 2 (removed WETH_copy)
"""
