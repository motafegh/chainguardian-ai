# Paste the full response schemas code
"""
Response schemas for ChainGuardian AI API.
Defines output format for both endpoints.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class VulnerabilitySummary(BaseModel):
    """Summary of detected vulnerabilities."""
    
    type: str = Field(..., description="Vulnerability type", example="reentrancy")
    severity: str = Field(..., description="Severity level", example="high")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    description: str = Field(..., description="Human-readable description")


class AnalysisSummary(BaseModel):
    """High-level contract metrics for non-technical users."""
    
    num_functions: int = Field(..., description="Total functions in contract")
    num_external_calls: int = Field(..., description="Number of external calls")
    cyclomatic_complexity: float = Field(..., description="Code complexity score")
    lines_of_code: int = Field(..., description="Total lines of code")
    has_critical_issues: bool = Field(..., description="Whether critical vulnerabilities found")
    complexity_rating: str = Field(..., description="Human rating", example="moderate")


class ContractAnalysisResponse(BaseModel):
    """
    Response for full contract analysis endpoint.
    
    User-friendly format that non-technical users can understand.
    """
    
    # Simple verdict (what user cares about most)
    is_safe: bool = Field(
        ...,
        description="Overall safety verdict (true = safe, false = vulnerable)"
    )
    
    # Risk score (0.0 = safe, 1.0 = very risky)
    risk_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall risk score (0.0 = safe, 1.0 = maximum risk)"
    )
    
    # Model confidence
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model confidence in the prediction"
    )
    
    # Detected vulnerabilities (empty list if safe)
    vulnerabilities: List[VulnerabilitySummary] = Field(
        default_factory=list,
        description="List of detected vulnerabilities"
    )
    
    # High-level summary
    summary: AnalysisSummary = Field(
        ...,
        description="Contract analysis summary"
    )
    
    # Metadata
    contract_name: Optional[str] = None
    contract_address: Optional[str] = None
    model_version: str = Field(..., example="v1.0.7")
    
    # Performance metrics
    feature_extraction_time_ms: int = Field(
        ...,
        description="Time spent extracting features"
    )
    prediction_time_ms: int = Field(
        ...,
        description="Time spent on ML prediction"
    )
    total_time_ms: int = Field(
        ...,
        description="Total analysis time"
    )
    
    # Timestamp
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
    
    # Optional detailed data
    extracted_features: Optional[Dict[str, float]] = Field(
        None,
        description="Raw features (if requested via include_features=true)"
    )
    
    explanations: Optional[Dict[str, Any]] = Field(
        None,
        description="SHAP explanations (if requested)"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "is_safe": True,
                "risk_score": 0.05,
                "confidence": 0.95,
                "vulnerabilities": [],
                "summary": {
                    "num_functions": 15,
                    "num_external_calls": 3,
                    "cyclomatic_complexity": 5.2,
                    "lines_of_code": 120,
                    "has_critical_issues": False,
                    "complexity_rating": "low"
                },
                "contract_name": "SimpleToken",
                "model_version": "v1.0.7",
                "feature_extraction_time_ms": 850,
                "prediction_time_ms": 66,
                "total_time_ms": 916,
                "timestamp": "2025-12-24T19:36:00.000Z"
            }
        }


class DirectPredictionResponse(BaseModel):
    """
    Response for direct prediction endpoint (advanced users).
    
    More technical format with raw ML output.
    """
    
    prediction: str = Field(
        ...,
        description="Classification result",
        example="safe"
    )
    
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model confidence"
    )
    
    probabilities: Dict[str, float] = Field(
        ...,
        description="Class probabilities",
        example={"safe": 0.95, "vulnerable": 0.05}
    )
    
    model_version: str = Field(..., example="v1.0.7")
    model_type: str = Field(..., example="ensemble")
    
    prediction_time_ms: int = Field(
        ...,
        description="Prediction latency in milliseconds"
    )
    
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
    
    contract_address: Optional[str] = None
    
    explanations: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "prediction": "safe",
                "confidence": 0.98,
                "probabilities": {"safe": 0.98, "vulnerable": 0.02},
                "model_version": "v1.0.7",
                "model_type": "ensemble",
                "prediction_time_ms": 66,
                "timestamp": "2025-12-24T19:36:00.000Z"
            }
        }
