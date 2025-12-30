# Paste the ContractAnalysisRequest + DirectPredictionRequest code
"""
Request schemas for ChainGuardian AI API.
Defines input validation for both endpoints.
"""
from typing import Optional, Dict
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re


class ContractAnalysisRequest(BaseModel):
    """
    PRIMARY ENDPOINT: Full analysis (contract code → features → prediction).
    
    User sends Solidity code, we handle everything internally.
    This is what 95% of users will use.
    """
    
    contract_code: str = Field(
        ...,
        description="Solidity smart contract source code",
        min_length=10,
        example=(
            "pragma solidity ^0.8.0;\n\n"
            "contract SimpleToken {\n"
            "    mapping(address => uint256) public balances;\n"
            "    \n"
            "    function transfer(address to, uint256 amount) public {\n"
            "        require(balances[msg.sender] >= amount, 'Insufficient balance');\n"
            "        balances[msg.sender] -= amount;\n"
            "        balances[to] += amount;\n"
            "    }\n"
            "}"
        )
    )
    
    contract_name: Optional[str] = Field(
        None,
        description="Name of the main contract to analyze (auto-detected if not provided)",
        example="SimpleToken"
    )
    
    contract_address: Optional[str] = Field(
        None,
        description="Ethereum address for tracking/logging",
        pattern=r"^0x[a-fA-F0-9]{40}$",  # Validate Ethereum address format
        example="0x1234567890abcdef1234567890abcdef12345678"
    )
    
    include_features: bool = Field(
        False,
        description="Include extracted features in response (for debugging/research)"
    )
    
    include_explanations: bool = Field(
        False,
        description="Include SHAP explanations (adds ~2s latency)"
    )
    
    @field_validator('contract_code')
    @classmethod
    def validate_solidity_code(cls, v: str) -> str:
        """Validate that it looks like Solidity code."""
        v = v.strip()

        # Must contain either pragma or contract keyword
        if 'pragma' not in v.lower() and 'contract' not in v.lower():
            raise ValueError(
                "Invalid Solidity code: must contain 'pragma' or 'contract' keyword"
            )

        # Size limit to prevent abuse
        if len(v) > 100_000:  # 100KB
            raise ValueError("Contract code too large (max 100KB)")

        # Must have at least some structure
        if v.count('{') != v.count('}'):
            raise ValueError("Unbalanced braces in contract code")

        return v
    
    @field_validator('contract_name')
    @classmethod
    def validate_contract_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate contract name format."""
        if v is not None:
            # Must be valid Solidity identifier
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', v):
                raise ValueError(
                    "Invalid contract name: must be a valid Solidity identifier"
                )
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "contract_code": "pragma solidity ^0.8.0;\n\ncontract Example {\n    uint256 public value;\n}",
                "contract_name": "Example",
                "contract_address": "0x1234567890abcdef1234567890abcdef12345678",
                "include_features": False,
                "include_explanations": False
            }
        }
    )


class DirectPredictionRequest(BaseModel):
    """
    ADVANCED ENDPOINT: Direct prediction from pre-extracted features.
    
    For ML researchers, A/B testing, or users with custom feature extraction.
    Expects exactly 70 features that your model was trained on.
    """
    
    features: Dict[str, float] = Field(
        ...,
        description="Dictionary of 70 pre-extracted contract features",
        example={
            "num_functions": 15.0,
            "cyclomatic_complexity": 8.5,
            "cei_violations": 2.0,
            "has_reentrancy": 0.0,
            "num_external_calls": 5.0
        }
    )
    
    contract_address: Optional[str] = Field(
        None,
        pattern=r"^0x[a-fA-F0-9]{40}$"
    )
    
    include_explanations: bool = Field(
        False,
        description="Include SHAP explanations"
    )
    
    @field_validator('features')
    @classmethod
    def validate_features(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Validate features dictionary."""
        if not v:
            raise ValueError("features dict cannot be empty")

        # All values must be numeric
        for key, value in v.items():
            if not isinstance(value, (int, float)):
                raise ValueError(
                    f"Feature '{key}' must be numeric, got {type(value).__name__}"
                )

            # Check for NaN/Inf
            if value != value or abs(value) == float('inf'):
                raise ValueError(f"Feature '{key}' contains NaN or Inf")

        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "features": {
                    "num_functions": 15.0,
                    "max_cyclomatic_complexity": 8.0,
                    "cei_violations": 0.0
                },
                "contract_address": "0x1234567890abcdef1234567890abcdef12345678",
                "include_explanations": False
            }
        }
    )
