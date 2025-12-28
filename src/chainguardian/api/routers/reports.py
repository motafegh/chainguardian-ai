"""
Report generation endpoints for ChainGuardian AI.
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
import time
import json
import httpx

from pydantic import BaseModel, Field
from chainguardian.api.dependencies.model_loader import get_predictor
from chainguardian.ml.models.hybrid_predictor_enhanced_v2 import EnhancedHybridPredictorV2
from chainguardian.monitoring.llm_metrics import (
    llm_requests_total,
    llm_tokens_total,
    llm_latency_seconds,
    llm_cost_estimated,
    active_llm_requests,
    estimate_llm_cost,
    rate_limit_exceeded_total
)

router = APIRouter(prefix="/api/v1", tags=["reports"])


class ReportFormat(str, Enum):
    """Available report formats."""
    PDF = "pdf"
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"


class TechnicalDepth(str, Enum):
    """Technical depth levels."""
    BEGINNER = "beginner"  # Simple, non-technical
    INTERMEDIATE = "intermediate"  # Some technical details
    ADVANCED = "advanced"  Full technical details
    EXPERT = "expert"  # Includes code snippets and deep analysis


class GenerateReportRequest(BaseModel):
    """Request model for generating reports."""
    
    contract_code: str = Field(
        ...,
        description="Solidity smart contract source code",
        min_length=10
    )
    
    contract_name: Optional[str] = Field(
        None,
        description="Name of the contract"
    )
    
    contract_address: Optional[str] = Field(
        None,
        description="Ethereum contract address"
    )
    
    format: ReportFormat = Field(
        default=ReportFormat.MARKDOWN,
        description="Output format for the report"
    )
    
    depth: TechnicalDepth = Field(
        default=TechnicalDepth.INTERMEDIATE,
        description="Technical depth of the report"
    )
    
    include_recommendations: bool = Field(
        default=True,
        description="Include security recommendations"
    )
    
    include_code_snippets: bool = Field(
        default=False,
        description="Include relevant code snippets"
    )
    
    llm_model: str = Field(
        default="llama3.1",
        description="LLM model to use for report generation"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "contract_code": "pragma solidity ^0.8.0;\ncontract Example {\n    function withdraw() public {\n        // vulnerable code\n    }\n}",
                "contract_name": "VulnerableContract",
                "contract_address": "0x1234567890abcdef1234567890abcdef12345678",
                "format": "markdown",
                "depth": "intermediate",
                "include_recommendations": True,
                "include_code_snippets": False,
                "llm_model": "llama3.1"
            }
        }


class ReportResponse(BaseModel):
    """Response model for generated reports."""
    
    report_id: str = Field(
        ...,
        description="Unique ID for the generated report"
    )
    
    content: str = Field(
        ...,
        description="Generated report content"
    )
    
    format: ReportFormat = Field(
        ...,
        description="Format of the report"
    )
    
    model_used: str = Field(
        ...,
        description="LLM model used for generation"
    )
    
    generation_time_ms: int = Field(
        ...,
        description="Time taken to generate report in milliseconds"
    )
    
    token_count: Dict[str, int] = Field(
        ...,
        description="Number of tokens used"
    )
    
    estimated_cost_usd: float = Field(
        ...,
        description="Estimated cost in USD"
    )
    
    contract_name: Optional[str] = None
    contract_address: Optional[str] = None
    timestamp: str = Field(
        default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    )
    
    class Config:
        schema_extra = {
            "example": {
                "report_id": "rep_1234567890",
                "content": "# Security Audit Report\n\n## Contract: VulnerableContract\n\n### Findings...",
                "format": "markdown",
                "model_used": "llama3.1",
                "generation_time_ms": 2450,
                "token_count": {"input": 1200, "output": 850},
                "estimated_cost_usd": 0.0000012,
                "contract_name": "VulnerableContract",
                "contract_address": "0x1234567890abcdef1234567890abcdef12345678",
                "timestamp": "2025-12-29T10:30:00Z"
            }
        }


class OllamaClient:
    """Client for communicating with Ollama API."""
    
    def __init__(self, base_url: str = "http://ollama:11434"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=120.0)
    
    async def generate(self, model: str, prompt: str, system: Optional[str] = None) -> Dict[str, Any]:
        """Generate text using Ollama."""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9,
                "num_predict": 4000
            }
        }
        
        if system:
            payload["system"] = system
        
        response = await self.client.post(
            f"{self.base_url}/api/generate",
            json=payload
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Ollama API error: {response.text}"
            )
        
        return response.json()


# Dependency for Ollama client
async def get_ollama_client() -> OllamaClient:
    """Get Ollama client instance."""
    return OllamaClient()


@router.post("/reports/generate", response_model=ReportResponse)
async def generate_report(
    request: GenerateReportRequest,
    predictor: EnhancedHybridPredictorV2 = Depends(get_predictor),
    ollama: OllamaClient = Depends(get_ollama_client)
):
    """
    Generate comprehensive security audit report using LLM.
    
    Analyzes contract code and generates human-readable report.
    """
    # Track active LLM request
    active_llm_requests.inc()
    
    start_time = time.time()
    
    try:
        # Step 1: Analyze contract with ML model
        prediction_result = predictor.predict_single(
            features={"dummy": 1.0},  # Will be replaced with actual features
            return_details=True
        )
        
        # Step 2: Prepare prompt for LLM
        system_prompt = f"""You are a senior smart contract security auditor.
            Generate a security report with {request.depth.value} technical depth.
            Format the report in {request.format.value} format.
            """
            
        user_prompt = f"""
            Contract Name: {request.contract_name or "Unknown"}
            Contract Address: {request.contract_address or "Not provided"}

            Contract Code:

            {request.contract_code[:2000]}  # Limit to first 2000 chars


            ML Analysis Results:
            - Safety Status: {prediction_result.get('prediction_label', 'UNKNOWN')}
            - Confidence: {prediction_result.get('calibrated_confidence', 0) * 100:.1f}%
            - Detected Issues: {len(prediction_result.get('semantic_reasons', []))}

            Please generate a comprehensive security audit report with the following sections:
            1. Executive Summary
            2. Vulnerability Analysis
            3. Risk Assessment
            4. Recommendations
            5. Technical Details

            Make sure the report is {request.depth.value}-friendly.
        """
        
        # Step 3: Generate report with Ollama
        llm_start_time = time.time()
        
        llm_requests_total.labels(
            model=request.llm_model,
            endpoint="/reports/generate",
            status="started"
        ).inc()
        
        try:
            llm_response = await ollama.generate(
                model=request.llm_model,
                prompt=user_prompt,
                system=system_prompt
            )
            
            llm_latency = time.time() - llm_start_time
            llm_latency_seconds.labels(model=request.llm_model).observe(llm_latency)
            
            # Step 4: Track metrics
            input_tokens = len(user_prompt.split())  # Approximate
            output_tokens = len(llm_response.get("response", "").split())
            
            llm_tokens_total.labels(
                model=request.llm_model,
                direction="input"
            ).inc(input_tokens)
            
            llm_tokens_total.labels(
                model=request.llm_model,
                direction="output"
            ).inc(output_tokens)
            
            # Calculate cost
            cost = estimate_llm_cost(input_tokens, output_tokens, request.llm_model)
            llm_cost_estimated.labels(
                model=request.llm_model,
                provider="ollama-local"
            ).set(cost)
            
            # Track successful request
            llm_requests_total.labels(
                model=request.llm_model,
                endpoint="/reports/generate",
                status="success"
            ).inc()
            
            # Step 5: Prepare response
            report_id = f"rep_{int(time.time())}_{hash(request.contract_code[:50]) % 10000}"
            
            response = ReportResponse(
                report_id=report_id,
                content=llm_response.get("response", "# Error generating report"),
                format=request.format,
                model_used=request.llm_model,
                generation_time_ms=int((time.time() - start_time) * 1000),
                token_count={
                    "input": input_tokens,
                    "output": output_tokens
                },
                estimated_cost_usd=cost,
                contract_name=request.contract_name,
                contract_address=request.contract_address
            )
            
            return response
            
        except Exception as e:
            # Track failed LLM request
            llm_requests_total.labels(
                model=request.llm_model,
                endpoint="/reports/generate",
                status="failure"
            ).inc()
            
            raise HTTPException(
                status_code=500,
                detail=f"LLM generation failed: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}"
        )
    finally:
        # Decrement active LLM requests
        active_llm_requests.dec()


@router.get("/reports/formats")
async def get_available_formats():
    """Get available report formats."""
    return {
        "formats": [fmt.value for fmt in ReportFormat],
        "depths": [depth.value for depth in TechnicalDepth],
        "available_models": ["llama3.1", "mistral", "codellama", "phi3"]
    }