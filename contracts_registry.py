"""
Centralized Contract Registry
Single source of truth for all known contracts
"""

from typing import Dict, Any

# ===== CANONICAL CONTRACT REGISTRY =====
# All contract addresses in one place
# Format: address -> metadata dict

CANONICAL_CONTRACTS: Dict[str, Dict[str, Any]] = {
    # Top DeFi Tokens
    "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984": {
        "name": "Uniswap",
        "symbol": "UNI",
        "category": "defi",
        "verified": True,
        "source": "github",
    },
    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": {
        "name": "USD Coin",
        "symbol": "USDC",
        "category": "stablecoin",
        "verified": True,
        "source": "github",
    },
    "0xdAC17F958D2ee523a2206206994597C13D831ec7": {
        "name": "Tether USD",
        "symbol": "USDT",
        "category": "stablecoin",
        "verified": True,
        "source": "github",
    },
    # Add more contracts here...
}


def get_contract_by_address(address: str) -> Dict[str, Any]:
    """Get contract metadata by address"""
    return CANONICAL_CONTRACTS.get(address.lower())


def get_contracts_by_category(category: str) -> Dict[str, Dict[str, Any]]:
    """Get all contracts in a category"""
    return {
        addr: data
        for addr, data in CANONICAL_CONTRACTS.items()
        if data.get("category") == category
    }


def get_verified_contracts() -> Dict[str, Dict[str, Any]]:
    """Get only verified contracts"""
    return {
        addr: data
        for addr, data in CANONICAL_CONTRACTS.items()
        if data.get("verified", False)
    }
