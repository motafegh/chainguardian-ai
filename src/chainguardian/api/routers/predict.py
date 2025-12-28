"""
Prediction endpoints - SIMPLIFIED to use existing predictor output.
"""
from fastapi import APIRouter, Depends, HTTPException
import time
import tempfile
from pathlib import Path
from functools import lru_cache

from chainguardian.api.schemas.request import (
    ContractAnalysisRequest,
    DirectPredictionRequest
)
from chainguardian.api.schemas.response import (
    ContractAnalysisResponse,
    DirectPredictionResponse,
    VulnerabilitySummary,
    AnalysisSummary
)
from chainguardian.api.dependencies.model_loader import get_predictor
from chainguardian.monitoring.metrics import (
    predictions_total,
    feature_extraction_latency,
    model_confidence,
    vulnerabilities_detected,
    prediction_latency,
    active_predictions
)
from chainguardian.ml.models.hybrid_predictor_enhanced_v2 import EnhancedHybridPredictorV2
from chainguardian.feature_extraction.pipeline import FeaturePipeline


# Cache pipeline
@lru_cache()
def get_pipeline() -> FeaturePipeline:
    """Get feature extraction pipeline (cached)."""
    print("🔄 Loading feature extraction pipeline...")
    pipeline = FeaturePipeline()
    print("✅ Pipeline loaded")
    return pipeline


router = APIRouter(prefix="/api/v1", tags=["predictions"])


@router.post("/analyze", response_model=ContractAnalysisResponse)
async def analyze_contract(
    request: ContractAnalysisRequest,
    predictor: EnhancedHybridPredictorV2 = Depends(get_predictor)
):
    """
    Analyze smart contract - Full pipeline.
    
    Contract code → Feature extraction → ML prediction → Report
    """
    # Track active prediction
    active_predictions.inc()
    
    start_time = time.time()
    
    try:
        # STEP 1: Save contract code to temp file (your pipeline needs file path)
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.sol', delete=False, encoding='utf-8'
        ) as temp_file:
            temp_file.write(request.contract_code)
            temp_path = Path(temp_file.name)
        
        try:
            # STEP 2: Extract features using YOUR pipeline
            pipeline = get_pipeline()
            
            # Auto-detect contract name if not provided
            contract_name = request.contract_name
            if not contract_name:
                import re
                matches = re.findall(
                    r'\bcontract\s+([a-zA-Z_][a-zA-Z0-9_]*)', 
                    request.contract_code
                )
                contract_name = matches[0] if matches else "UnknownContract"
            
            features = pipeline.analyze_contract(
                contract_path=temp_path,
                contract_name=contract_name,
                metadata={"address": request.contract_address}
            )
            
            extraction_time_ms = int((time.time() - start_time) * 1000)
            
            # Track feature extraction latency in seconds
            feature_extraction_latency.observe(extraction_time_ms / 1000)
            
            # Check for extraction failures
            if features.get('failure_reason'):
                raise ValueError(f"Feature extraction failed: {features['failure_reason']}")
            
            # STEP 3: ML prediction using YOUR predictor
            prediction_start = time.time()
            
            ml_result = predictor.predict_single(
                features=features,
                return_details=True,
                explain=request.include_explanations
            )
            
            prediction_time_ms = int((time.time() - prediction_start) * 1000)
            
            # Track prediction latency
            prediction_latency.observe(prediction_time_ms / 1000)
            
            # STEP 4: Convert YOUR predictor output to API response
            is_safe = (ml_result["prediction_label"] == "SAFE")
            confidence = ml_result["calibrated_confidence"]
            
            # Track model confidence with prediction class label
            prediction_class = "vulnerable" if not is_safe else "safe"
            model_confidence.labels(prediction_class=prediction_class).observe(confidence)
            
            # Convert semantic_reasons to VulnerabilitySummary format
            vulnerabilities = []
            for reason in ml_result.get("semantic_reasons", []):
                # Your reasons are already descriptive strings
                # Map them to severity based on keywords
                severity = "high" if any(word in reason.lower() for word in ["reentrancy", "access"]) else "medium"
                vulnerabilities.append(
                    VulnerabilitySummary(
                        type="vulnerability",
                        severity=severity,
                        confidence=0.9,
                        description=reason  # Use YOUR description directly!
                    )
                )
                
                # Track vulnerabilities detected
                vulnerabilities_detected.labels(
                    vulnerability_type="general",
                    severity=severity
                ).inc()
            
            # Create analysis summary from YOUR features
            summary = AnalysisSummary(
                num_functions=int(features.get("num_functions", 0)),
                num_external_calls=int(features.get("num_external_calls", 0)),
                cyclomatic_complexity=float(features.get("max_cyclomatic_complexity", 0)),
                lines_of_code=int(features.get("lines_of_code", 0)),
                has_critical_issues=(features.get("high_severity_count", 0) > 0),
                complexity_rating=(
                    "low" if features.get("max_cyclomatic_complexity", 0) < 5
                    else "moderate" if features.get("max_cyclomatic_complexity", 0) < 10
                    else "high"
                )
            )
            
            # Track successful prediction
            predictions_total.labels(
                endpoint="/analyze",
                model_version="v1.0.7",
                status="success"
            ).inc()
            
            # Build response
            response = ContractAnalysisResponse(
                is_safe=is_safe,
                risk_score=round(1.0 - confidence if is_safe else confidence, 4),
                confidence=round(confidence, 4),
                vulnerabilities=vulnerabilities,
                summary=summary,
                contract_name=contract_name,
                contract_address=request.contract_address,
                model_version="v1.0.7",
                feature_extraction_time_ms=extraction_time_ms,
                prediction_time_ms=prediction_time_ms,
                total_time_ms=int((time.time() - start_time) * 1000),
                extracted_features=features if request.include_features else None,
                explanations=ml_result.get("shap_explanation") if request.include_explanations else None
            )
            
            return response
            
        finally:
            # Clean up temp file
            temp_path.unlink(missing_ok=True)
        
    except ValueError as e:
        # Track failed prediction
        predictions_total.labels(
            endpoint="/analyze",
            model_version="v1.0.7",
            status="failure"
        ).inc()
        raise HTTPException(status_code=400, detail={"error": str(e)})
    except Exception as e:
        # Track failed prediction
        predictions_total.labels(
            endpoint="/analyze",
            model_version="v1.0.7",
            status="failure"
        ).inc()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail={"error": str(e)})
    finally:
        # Decrement active predictions
        active_predictions.dec()


@router.post("/predict-from-features", response_model=DirectPredictionResponse)
async def predict_from_features(
    request: DirectPredictionRequest,
    predictor: EnhancedHybridPredictorV2 = Depends(get_predictor)
):
    """Direct prediction from pre-extracted features."""
    # Track active prediction
    active_predictions.inc()
    
    start_time = time.time()
    
    try:
        # Use YOUR predictor directly
        ml_result = predictor.predict_single(
            features=request.features,
            return_details=True,
            explain=request.include_explanations
        )
        
        prediction_time_ms = int((time.time() - start_time) * 1000)
        
        # Track prediction latency
        prediction_latency.observe(prediction_time_ms / 1000)
        
        # Track model confidence
        is_safe = ml_result["prediction_label"] == "SAFE"
        confidence = ml_result["calibrated_confidence"]
        prediction_class = "vulnerable" if not is_safe else "safe"
        model_confidence.labels(prediction_class=prediction_class).observe(confidence)
        
        # Track successful prediction
        predictions_total.labels(
            endpoint="/predict-from-features",
            model_version="v1.0.7",
            status="success"
        ).inc()
        
        # YOUR predictor already returns everything we need!
        response = DirectPredictionResponse(
            prediction=ml_result["prediction_label"],
            confidence=round(confidence, 4),
            probabilities={
                "safe": round(1.0 - ml_result["ml_score"] if ml_result["prediction"] == 1 else ml_result["ml_score"], 4),
                "vulnerable": round(ml_result["ml_score"] if ml_result["prediction"] == 1 else 1.0 - ml_result["ml_score"], 4)
            },
            model_version="v1.0.7",
            model_type="ensemble" if predictor.use_ensemble else "single",
            prediction_time_ms=prediction_time_ms,
            contract_address=request.contract_address,
            explanations=ml_result.get("shap_explanation") if request.include_explanations else None
        )
        
        return response
        
    except Exception as e:
        # Track failed prediction
        predictions_total.labels(
            endpoint="/predict-from-features",
            model_version="v1.0.7",
            status="failure"
        ).inc()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail={"error": str(e)})
    finally:
        # Decrement active predictions
        active_predictions.dec()


@router.get("/models/info")
async def get_model_info(predictor: EnhancedHybridPredictorV2 = Depends(get_predictor)):
    """Get model information."""
    return {
        "model_version": "v1.0.7",
        "model_type": "ensemble" if predictor.use_ensemble else "single",
        "performance_metrics": {
            "test_auc": 0.9978,
            "test_accuracy": 0.9832,
            "brier_score": 0.0146
        }
    }