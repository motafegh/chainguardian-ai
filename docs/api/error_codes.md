# ChainGuardian API Error Codes

## 4xx Client Errors (User's Fault)

### ERR_001: Invalid Solidity Syntax
**HTTP Status:** 400 Bad Request  
**Cause:** Code contains syntax errors, missing semicolons, etc.  
**Solution:** Fix Solidity syntax, use Remix IDE to validate  
**Example:**
{
"error_code": "ERR_001",
"message": "Invalid Solidity syntax",
"details": {"line": 45, "reason": "Expected ';'"}
}

text

### ERR_002: Code Too Large
**HTTP Status:** 400 Bad Request  
**Cause:** Contract exceeds 50KB limit  
**Solution:** Split into multiple contracts or reduce size  
**Example:**
{
"error_code": "ERR_002",
"message": "Code exceeds maximum size",
"details": {"max_bytes": 50000, "received_bytes": 75000}
}

text

### ERR_003: Missing Contract Keyword
**HTTP Status:** 400 Bad Request  
**Cause:** Code doesn't contain 'contract' keyword  
**Solution:** Ensure valid Solidity contract  

### ERR_004: Slither Analysis Failed
**HTTP Status:** 422 Unprocessable Entity  
**Cause:** Slither cannot analyze (unsupported version, complex assembly)  
**Solution:** Simplify contract or use supported Solidity version (0.8.x)  
**Example:**
{
"error_code": "ERR_004",
"message": "Slither analysis failed",
"details": {"reason": "Unsupported Solidity version 0.4.x"}
}

text

---

## 5xx Server Errors (Our Fault)

### ERR_101: Model Not Loaded
**HTTP Status:** 500 Internal Server Error  
**Cause:** Model file missing or corrupted  
**Solution:** Restart service, check model file exists  

### ERR_102: Feature Extraction Failed
**HTTP Status:** 500 Internal Server Error  
**Cause:** Pipeline crashed during feature extraction  
**Solution:** Check logs, report bug  

### ERR_103: Model Prediction Failed
**HTTP Status:** 500 Internal Server Error  
**Cause:** Model inference error (feature mismatch, numpy error)  
**Solution:** Check feature shape, model compatibility  

### ERR_104: Database Connection Failed
**HTTP Status:** 503 Service Unavailable  
**Cause:** PostgreSQL down or connection timeout  
**Solution:** Restart database, check connection string  

### ERR_105: Request Timeout
**HTTP Status:** 504 Gateway Timeout  
**Cause:** Analysis took longer than 30 seconds  
**Solution:** Simplify contract, increase timeout (Week 5)  
**Example:**
{
"error_code": "ERR_105",
"message": "Request timeout",
"details": {"timeout_seconds": 30}
}

text

---

## Error Handling Strategy

**Mapping Existing Exceptions → HTTP Errors:**

| Python Exception | HTTP Status | Error Code |
|------------------|-------------|------------|
| `ValueError` (Slither) | 422 | ERR_004 |
| `SyntaxError` (AST) | 400 | ERR_001 |
| `TimeoutError` | 504 | ERR_105 |
| `psycopg2.OperationalError` | 503 | ERR_104 |
| `FileNotFoundError` (model) | 500 | ERR_101 |
| Generic `Exception` | 500 | ERR_999 |

