# Integration Plan: Existing Code → FastAPI

## Current Architecture (CLI)
scripts/3_training/predict.py (CLI entry point)
↓
src/chainguardian/feature_extraction/pipeline.py
↓ (extracts 93 features)
src/chainguardian/ml/models/hybrid_predictor.py
↓ (predicts SAFE/VULNERABLE)
Print to terminal

text

## Target Architecture (API)
FastAPI POST /api/v1/analyze (HTTP entry point)
↓
app/services/predictor.py (NEW - wrapper service)
↓
src/chainguardian/feature_extraction/pipeline.py (REUSE - no changes)
↓
src/chainguardian/ml/models/hybrid_predictor.py (REUSE - no changes)
↓
Return JSON via Pydantic

text

---

## Reusable Components (Zero Changes)

### 1. Feature Extraction Pipeline ✅
**File:** `src/chainguardian/feature_extraction/pipeline.py`  
**Usage:** 
pipeline = FeatureExtractionPipeline(db_manager)
features = pipeline.extract_features(contract_code, "temp_name")

text
**API Integration:** Direct import, wrap in service class

### 2. Hybrid Predictor ✅
**File:** `src/chainguardian/ml/models/hybrid_predictor.py`  
**Usage:**
predictor = HybridPredictor.load("models/hybrid_xgboost_v1.pkl")
result = predictor.predict(features)

text
**API Integration:** Load at startup, call predict() per request

### 3. Database Manager ⚠️
**File:** `src/chainguardian/database/manager.py`  
**Current Usage:** Single connection per script  
**API Requirement:** Connection pooling (5-10 connections)  
**Change Needed:** Wrap in SQLAlchemy session (Week 3, Day 3)

---

## Changes Required (Non-Breaking)

### 1. Input Method
**Current:** Read from file
with open("test_contracts/01_simple.sol") as f:
code = f.read()

text

**API:** Receive as string
code = request.code # Already in memory

text

**Impact:** ✅ Pipeline already accepts string, no code change

---

### 2. Output Method
**Current:** Print to terminal
print(f"Prediction: {result['prediction']}")
print(f"Confidence: {result['confidence']}")

text

**API:** Return JSON
return PredictionResponse(**result)

text

**Impact:** ✅ Just wrap dict in Pydantic, no predictor change

---

### 3. Error Handling
**Current:** Script crashes, shows traceback
try:
features = pipeline.extract_features(code)
except Exception as e:
print(f"Error: {e}")
sys.exit(1)

text

**API:** Return HTTP error
try:
features = pipeline.extract_features(code)
except SlitherException as e:
raise HTTPException(status_code=422, detail={
"error_code": "ERR_004",
"message": str(e)
})

text

**Impact:** ⚠️ Need exception mapping layer (Day 4)

---

## Week 3 Project Structure
chainguardian-ai/
├── src/chainguardian/ ← Existing (keep as-is)
│ ├── feature_extraction/
│ ├── ml/models/
│ └── database/
│
├── app/ ← NEW (API layer)
│ ├── main.py # FastAPI app
│ ├── models/ # Pydantic schemas
│ │ ├── request.py
│ │ └── response.py
│ ├── routers/
│ │ ├── analysis.py # /analyze endpoint
│ │ └── health.py # /health endpoint
│ ├── services/
│ │ └── predictor.py # Wraps existing pipeline
│ └── core/
│ ├── config.py # Settings
│ └── exceptions.py # Error mapping
│
├── scripts/ ← Existing (still works)
│ └── 3_training/predict.py # CLI still functional
│
├── models/ ← Existing (reused)
│ └── saved_models/hybrid_xgboost_v1.pkl
│
├── docs/api/ ← NEW (today's work)
│ ├── api_specification.md
│ ├── error_codes.md
│ ├── pydantic_schemas.md
│ └── integration_plan.md
│
└── tests/ ← Existing + NEW
├── unit/ # Existing tests still work
└── integration/ # Add API tests (Week 3 Day 6)

text

---

## Compatibility Verification Checklist

- [x] Pipeline accepts contract code as string (no file dependency)
- [x] Predictor returns dict (compatible with Pydantic)
- [x] Database manager has connection interface (can be pooled)
- [x] Model file exists at `models/saved_models/hybrid_xgboost_v1.pkl`
- [ ] Test existing CLI still works after API added (Week 4)

---

## Risk Mitigation

**Risk 1:** API changes break CLI scripts  
**Mitigation:** Keep `src/chainguardian/` untouched, API imports from it

**Risk 2:** Database connection pool conflicts with CLI single connection  
**Mitigation:** Use environment variable to toggle pooling on/off

**Risk 3:** Model loading twice (CLI + API)  
**Mitigation:** Lazy loading - only load when needed

