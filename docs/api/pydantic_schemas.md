# Pydantic Schema Designs

## Request Schemas

### ContractAnalysisRequest
from pydantic import BaseModel, Field, validator

class ContractAnalysisRequest(BaseModel):
"""Input for /api/v1/analyze endpoint"""

text
code: str = Field(
    ...,
    min_length=10,
    max_length=50000,
    description="Solidity contract source code"
)

include_features: bool = Field(
    default=False,
    description="Return raw 93 features in response"
)

@validator('code')
def validate_solidity(cls, v):
    if 'contract' not in v.lower():
        raise ValueError("Must contain 'contract' keyword")
    return v

class Config:
    json_schema_extra = {
        "example": {
            "code": "contract SimpleStorage { uint256 value; }",
            "include_features": False
        }
    }
text

---

## Response Schemas

### PredictionResponse
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime

class PredictionResponse(BaseModel):
"""Output for successful predictions"""

text
prediction: Literal["SAFE", "VULNERABLE"] = Field(
    ...,
    description="Binary classification"
)

confidence: float = Field(
    ...,
    ge=0.0,
    le=1.0,
    description="Model confidence (0-1)"
)

risk_score: float = Field(
    ...,
    ge=0.0,
    le=1.0,
    description="Combined ML + semantic risk score"
)

cei_violations: int = Field(
    ...,
    ge=0,
    description="Number of CEI pattern violations"
)

timestamp: datetime = Field(
    default_factory=datetime.utcnow,
    description="Analysis timestamp (UTC)"
)

model_version: str = Field(
    default="1.0",
    description="Hybrid model version"
)

features: Optional[dict] = Field(
    default=None,
    description="Raw features (if requested)"
)

class Config:
    json_schema_extra = {
        "example": {
            "prediction": "VULNERABLE",
            "confidence": 0.87,
            "risk_score": 0.82,
            "cei_violations": 3,
            "timestamp": "2024-12-21T14:30:00Z",
            "model_version": "1.0",
            "features": None
        }
    }
text

### ErrorResponse
class ErrorResponse(BaseModel):
"""Standard error format for all endpoints"""

text
error_code: str = Field(
    ...,
    description="Machine-readable error code",
    pattern="^ERR_[0-9]{3}$"
)

message: str = Field(
    ...,
    description="Human-readable error message"
)

details: Optional[dict] = Field(
    default=None,
    description="Additional context"
)

class Config:
    json_schema_extra = {
        "example": {
            "error_code": "ERR_004",
            "message": "Slither analysis failed",
            "details": {"reason": "Unsupported version"}
        }
    }
text

### HealthResponse
class HealthResponse(BaseModel):
"""Health check output"""

text
status: Literal["healthy", "unhealthy"]
model_version: str
model_loaded: bool
database_connected: bool
uptime_seconds: int = Field(ge=0)
text

---

## Mapping to Existing Code

**From `hybrid_predictor.py` output:**
Current predictor returns:
{
'prediction': 'VULNERABLE', # → PredictionResponse.prediction
'confidence': 0.8742, # → PredictionResponse.confidence
'ml_score': 0.9123, # → (ml_score + semantic_score) / 2
'semantic_score': 0.8, # → PredictionResponse.risk_score
'cei_violations': 3, # → PredictionResponse.cei_violations
'cei_details': {...}, # → Excluded in Week 3 (add Week 5)
'features': {...} # → PredictionResponse.features
}

text

**Conversion Function (Pseudocode):**
def convert_to_api_response(predictor_output: dict) -> PredictionResponse:
return PredictionResponse(
prediction=predictor_output['prediction'],
confidence=predictor_output['confidence'],
risk_score=(predictor_output['ml_score'] + predictor_output['semantic_score']) / 2,
cei_violations=predictor_output['cei_violations'],
features=predictor_output.get('features') if include_features else None
)

text

