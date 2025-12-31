"""
Ollama LLM Client
Communicates with local Ollama server via HTTP API.

Ollama API Documentation: https://github.com/ollama/ollama/blob/main/docs/api.md

Key Features:
- Async HTTP client with connection pooling (reduces latency by 50-100ms)
- Comprehensive error handling (timeout, HTTP errors, JSON parsing)
- Health checks (verify Ollama is running and model is available)
- Context manager support (automatic connection cleanup)
- Detailed logging and metrics

Example Usage:
    # Method 1: Manual
    client = OllamaClient("llama3.1:4b")
    if await client.health_check():
        response = await client.generate("Analyze this smart contract...")
        print(response.text)
    await client.client.aclose()
    
    # Method 2: Context manager (recommended)
    async with OllamaClient("llama3.1:4b") as client:
        response = await client.generate("Analyze this smart contract...")
        print(response.text)
    # Automatically closes connection
"""

# 🔥 CRITICAL: Standard Python libraries (built-in, no installation needed)
import time  # For measuring request latency
from typing import Optional, Dict, Any  # For type hints

# 🔥 CRITICAL: Third-party libraries (installed via poetry)
import httpx  # Async HTTP client (like requests but async)
from loguru import logger  # Structured logging

# 🔥 CRITICAL: Our own modules (absolute imports for clarity)
from chainguardian.llm.clients.base import BaseLLMClient, LLMResponse
from chainguardian.llm.config import llm_config


class OllamaClient(BaseLLMClient):
    """
    Client for local Ollama LLM server.
    
    Ollama is a local LLM server that runs models like Llama, CodeLlama, Mistral
    on your own hardware. It exposes a REST API on http://localhost:11434.
    
    Why httpx instead of requests?
    - Native async/await support (requests requires threading)
    - HTTP/2 support (better multiplexing)
    - Better timeout handling
    - Connection pooling out of the box
    - Active development (requests is in maintenance mode)
    
    Performance Characteristics:
    - Connection setup: 0ms (reused connections via pooling)
    - Typical latency: 2-5 seconds (depends on model size and prompt complexity)
    - Max throughput: Limited by GPU (Ollama processes 1 request per model at a time)
    """
    
    def __init__(
        self,
        model_name: str,
        base_url: Optional[str] = None,
        timeout: int = 60
    ):
        """
        Initialize Ollama client.
        
        Args:
            model_name: Ollama model name (format: "name:tag")
                Examples: "llama3.1:4b", "codellama:7b-instruct", "mistral:7b"
                Run `ollama list` to see available models
            
            base_url: Ollama server URL (default: from config or http://localhost:11434)
                In Docker: use "http://ollama:11434"
                Remote: use "http://server-ip:11434"
            
            timeout: Request timeout in seconds (default: 60s)
                Why so long? LLM generation is slow (3-5s typical, can be 30s+ for long outputs)
        
        Example:
            # Development (local)
            client = OllamaClient("llama3.1:4b")
            
            # Production (Docker)
            client = OllamaClient("llama3.1:4b", base_url="http://ollama:11434")
        """
        # 🔥 CRITICAL: Call parent's __init__ to set model_name and timeout
        # This is inheritance - parent class sets up common attributes
        super().__init__(model_name, timeout)
        
        # 📘 IMPORTANT: Set Ollama server URL
        # "or" operator: if base_url is None, use config value
        self.base_url = base_url or llm_config.ollama_base_url
        
        # 📘 IMPORTANT: Create persistent HTTP client (connection pooling)
        # Why persistent? Opening new connection costs 50-100ms per request
        # With pooling: First request pays connection cost, subsequent requests are instant
        self.client = httpx.AsyncClient(
            base_url=self.base_url,  # All requests will go to this URL
            timeout=timeout,  # Default timeout for all requests
            limits=httpx.Limits(
                max_keepalive_connections=5,  # Keep 5 connections alive for reuse
                max_connections=10,  # Maximum total connections
                keepalive_expiry=30.0  # Close idle connections after 30 seconds
            )
        )
        
        # 🎯 PATTERN: Log initialization (helpful for debugging)
        logger.info(
            f"✅ OllamaClient initialized: "
            f"model={model_name}, "
            f"server={self.base_url}, "
            f"timeout={timeout}s"
        )
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.2,
        **kwargs
    ) -> LLMResponse:
        """
        Generate text from Ollama model.
        
        Ollama API Endpoint: POST /api/generate
        Documentation: https://github.com/ollama/ollama/blob/main/docs/api.md#generate-a-completion
        
        Args:
            prompt: Text to send to LLM (can be multi-line, supports markdown)
            max_tokens: Maximum tokens to generate (1 token ≈ 4 chars)
                Example: 500 tokens ≈ 2000 characters ≈ 300-400 words
            temperature: Sampling temperature (0.0-2.0)
                - 0.0: Deterministic (same output every time)
                - 0.2: Low randomness (good for technical reports) ← Default
                - 0.8: High randomness (creative writing)
                - 2.0: Maximum randomness (experimental)
            **kwargs: Advanced Ollama options
                - top_p: Nucleus sampling (0.0-1.0)
                - top_k: Top-K sampling (1-100)
                - repeat_penalty: Penalize repetition (1.0-2.0)
                - stop: Stop sequences (list of strings)
        
        Returns:
            LLMResponse with:
                - text: Generated text (main result)
                - tokens_used: Token count
                - latency_ms: Time taken
                - model: Model name used
                - cached: False (fresh generation)
                - metadata: Ollama-specific data
        
        Raises:
            RuntimeError: If request fails (timeout, HTTP error, invalid JSON)
        
        Example:
            response = await client.generate(
                prompt="Explain reentrancy vulnerability in 2 sentences",
                max_tokens=100,
                temperature=0.2
            )
            print(response.text)  # "A reentrancy vulnerability occurs when..."
            print(f"Generated in {response.latency_ms:.0f}ms")
        """
        # 📘 IMPORTANT: Record start time to measure latency
        # time.time() returns seconds since epoch (e.g., 1735567890.123)
        start_time = time.time()
        
        # 🔥 CRITICAL: Start try block for error handling
        try:
            # 📘 IMPORTANT: Build JSON payload for Ollama API
            # This matches Ollama's expected format
            payload = {
                "model": self.model_name,  # Which model to use
                "prompt": prompt,  # User's text
                "stream": False,  # Get full response at once (not token-by-token)
                "options": {  # Generation parameters
                    "num_predict": max_tokens,  # Max output tokens
                    "temperature": temperature,  # Randomness level
                    # Spread any additional kwargs here
                    **kwargs
                }
            }
            
            # 🎯 PATTERN: Log debug info (helpful during development)
            logger.debug(
                f"📤 Sending to Ollama: "
                f"model={self.model_name}, "
                f"prompt_length={len(prompt)} chars, "
                f"max_tokens={max_tokens}, "
                f"temperature={temperature}"
            )
            
            # 🔥 CRITICAL: Send HTTP POST request to Ollama
            # await = wait for response without blocking other requests
            # This is where we actually talk to Ollama server
            response = await self.client.post(
                "/api/generate",  # Ollama's text generation endpoint
                json=payload  # httpx automatically serializes dict to JSON
            )
            
            # 📘 IMPORTANT: Check if request succeeded
            # Raises HTTPStatusError if status code is 4xx or 5xx
            # Why? Don't try to parse error HTML as JSON!
            response.raise_for_status()
            
            # 📘 IMPORTANT: Parse JSON response from Ollama
            # Ollama returns: {"model": "...", "response": "...", "eval_count": N, ...}
            data = response.json()
            
            # 📘 IMPORTANT: Calculate request latency
            end_time = time.time()
            elapsed_seconds = end_time - start_time
            # Ensure non-negative (defensive programming for clock issues)
            elapsed_ms = max(0.0, elapsed_seconds * 1000)  # Convert to milliseconds
            
            # 🔥 CRITICAL: Extract text from response
            # Different models use different field names:
            # - Most models: "response"
            # - Qwen models: "thinking" (yes, really!)
            # - Chat models: "message" -> "content"
            # - Some models: "text"
            text = (
                data.get("response") or 
                data.get("thinking") or 
                data.get("message", {}).get("content") or
                data.get("text") or
                ""
            )
            
            # 📘 IMPORTANT: Log warning if text is empty (debugging)
            if not text:
                logger.warning(
                    f"⚠️ Empty response from Ollama! "
                    f"Response keys: {list(data.keys())}, "
                    f"Response sample: {str(data)[:200]}"
                )
            
            # 🎯 PATTERN: Log success (helpful for monitoring)
            logger.info(
                f"✅ Ollama response received: "
                f"model={self.model_name}, "
                f"tokens={data.get('eval_count', 0)}, "
                f"latency={elapsed_ms:.0f}ms, "
                f"text_length={len(text)} chars"
            )
            
            # 🔥 CRITICAL: Return standardized response
            # Convert Ollama's format to our LLMResponse format
            return LLMResponse(
                text=text,  # Generated text (extracted above)
                model=self.model_name,  # Model that was used
                tokens_used=data.get("eval_count", 0),  # Tokens generated (0 if key missing)
                latency_ms=elapsed_ms,  # Time taken
                cached=False,  # Not from cache (fresh generation)
                metadata={  # Extra Ollama-specific info
                    "prompt_tokens": data.get("prompt_eval_count", 0),  # Tokens in prompt
                    "total_duration_ns": data.get("total_duration", 0),  # Total time in nanoseconds
                    "load_duration_ns": data.get("load_duration", 0),  # Model loading time
                    "eval_duration_ns": data.get("eval_duration", 0),  # Generation time
                    "thinking": data.get("thinking", ""),  # Qwen models include reasoning
                }
            )
        
        # 🔥 CRITICAL: Error handling (from specific to general)
        except httpx.TimeoutException as e:
            # Request took longer than timeout (60 seconds default)
            # Usually means: Ollama is overloaded, model is too large, or prompt is too complex
            logger.error(f"⏱️ Ollama request timeout after {self.timeout}s: {e}")
            raise RuntimeError(f"LLM request timeout after {self.timeout}s: {e}") from e
        
        except httpx.HTTPStatusError as e:
            # Server returned error status code (404, 500, 503, etc.)
            # 404: Model not found
            # 500: Ollama crashed
            # 503: Ollama not running
            logger.error(
                f"❌ Ollama HTTP error: "
                f"status={e.response.status_code}, "
                f"body={e.response.text[:200]}"  # Log first 200 chars of error
            )
            raise RuntimeError(f"LLM API returned error {e.response.status_code}: {e}") from e
        
        except Exception as e:
            # Catch any other unexpected errors
            # Examples: JSON parsing error, network issues, programming bugs
            logger.error(f"💥 Unexpected error in Ollama client: {e}")
            raise  # Re-raise original exception for debugging
    
    async def health_check(self) -> bool:
        """
        Check if Ollama server is reachable and model is available.
        
        This verifies two things:
        1. Ollama server is running (can connect to API)
        2. Our model exists and is downloaded
        
        Ollama API Endpoint: GET /api/tags
        Returns: {"models": [{"name": "llama3.1:4b", ...}, {"name": "codellama:7b", ...}]}
        
        Returns:
            True: Ollama is healthy and model is ready
            False: Ollama is down or model is missing
        
        Example:
            if await client.health_check():
                print("✅ Ready to generate!")
                response = await client.generate("Hello")
            else:
                print("❌ Ollama not ready. Please start it:")
                print("  ollama serve")
                print(f"  ollama pull {client.model_name}")
        """
        try:
            # 📘 IMPORTANT: GET request to /api/tags endpoint
            # This lists all available models in Ollama
            # We use shorter timeout (5s vs 60s) - health checks should be fast!
            response = await self.client.get(
                "/api/tags",  # Ollama endpoint that lists models
                timeout=5.0  # Don't wait long for health check
            )
            
            # 📘 IMPORTANT: Check if request succeeded
            response.raise_for_status()
            
            # 📘 IMPORTANT: Parse JSON response
            # Format: {"models": [{"name": "llama3.1:4b", "size": 2500000000, ...}, ...]}
            data = response.json()
            
            # 🔥 CRITICAL: Extract model names from response
            # List comprehension: [expression for item in list]
            # Equivalent to:
            #   available_models = []
            #   for model in data.get("models", []):
            #       available_models.append(model["name"])
            available_models = [
                model["name"] 
                for model in data.get("models", [])
            ]
            
            # 🔥 CRITICAL: Check if our model is in the list
            if self.model_name not in available_models:
                logger.warning(
                    f"⚠️ Model '{self.model_name}' not found in Ollama. "
                    f"Available models: {available_models}. "
                    f"Please run: ollama pull {self.model_name}"
                )
                return False  # Model not available
            
            # 🎯 PATTERN: Log success
            logger.info(
                f"✅ Health check passed: "
                f"{self.model_name} is ready "
                f"({len(available_models)} models available)"
            )
            return True  # Everything OK!
        
        except Exception as e:
            # 🔥 CRITICAL: If ANY error occurs, health check fails
            # Don't raise exception - just return False (health check is non-critical)
            logger.error(f"❌ Health check failed: {e}")
            return False
    
    # 🎯 PATTERN: Context manager support
    # Allows: async with OllamaClient(...) as client:
    async def __aenter__(self):
        """
        Called when entering "async with" block.
        
        Example:
            async with OllamaClient("llama3.1") as client:
                # __aenter__ runs here
                response = await client.generate("Hello")
            # __aexit__ runs here (automatic cleanup)
        """
        return self  # Return self so user can access the client
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Called when exiting "async with" block (cleanup).
        
        Args:
            exc_type: Exception type if error occurred (None if no error)
            exc_val: Exception value
            exc_tb: Exception traceback
        
        This runs even if exception occurs inside the "with" block,
        ensuring connections are always closed.
        """
        # 📘 IMPORTANT: Close HTTP client to free resources
        # This closes all connections and frees memory
        await self.client.aclose()
        logger.debug(f"�� OllamaClient connections closed: {self.model_name}")
