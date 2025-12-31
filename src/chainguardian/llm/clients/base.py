"""
Abstract Base Client for LLM Interactions
Defines the contract that all LLM clients must implement.

Why use Abstract Base Classes (ABC)?
- Enforces consistent interface across providers (Ollama, OpenAI, Anthropic)
- Enables polymorphism (swap providers without changing calling code)
- Catches missing methods at instantiation (not runtime)
- Self-documenting (shows what methods are required)

Example:
    # Define interface
    class BaseLLMClient(ABC):
        @abstractmethod
        async def generate(self, prompt: str) -> LLMResponse:
            pass
    
    # Implement for Ollama
    class OllamaClient(BaseLLMClient):
        async def generate(self, prompt: str) -> LLMResponse:
            return await self._call_ollama(prompt)
    
    # Implement for OpenAI
    class OpenAIClient(BaseLLMClient):
        async def generate(self, prompt: str) -> LLMResponse:
            return await self._call_openai(prompt)
    
    # Polymorphic usage
    def audit_contract(client: BaseLLMClient, code: str):
        return await client.generate(f"Audit: {code}")
    
    # Works with any client!
    audit_contract(OllamaClient("llama3.1"), code)
    audit_contract(OpenAIClient("gpt-4"), code)
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    """
    Standardized response format from any LLM provider.
    
    Why standardize responses?
    - Different providers return different formats (Ollama ≠ OpenAI)
    - Our code shouldn't depend on provider-specific structure
    - Easy to swap providers without breaking downstream code
    - Type hints enable IDE autocomplete
    
    Example:
        # Ollama returns: {"response": "text", "eval_count": 50}
        # OpenAI returns: {"choices": [{"message": {"content": "text"}}], "usage": {"completion_tokens": 50}}
        
        # Both convert to:
        response = LLMResponse(
            text="text",
            tokens_used=50,
            model="...",
            latency_ms=3000.0
        )
        
        # Downstream code only sees:
        print(response.text)  # Always works, regardless of provider
    """
    
    text: str = Field(
        description="Generated text content (main result)"
    )
    
    model: str = Field(
        description="Model name used for generation (e.g., 'llama3.1:4b', 'gpt-4')"
    )
    
    tokens_used: int = Field(
        ge=0,
        description="Number of tokens generated in response (1 token ≈ 4 characters)"
    )
    
    latency_ms: float = Field(
        ge=0.0,
        description="Time taken to generate response in milliseconds"
    )
    
    cached: bool = Field(
        default=False,
        description="Whether response was served from cache (True) or freshly generated (False)"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Provider-specific metadata. "
            "Examples: prompt_tokens, total_duration, finish_reason, model_version"
        )
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "text": "The smart contract contains a reentrancy vulnerability in the withdraw function...",
                "model": "llama3.1:4b",
                "tokens_used": 87,
                "latency_ms": 2847.5,
                "cached": False,
                "metadata": {
                    "prompt_tokens": 45,
                    "total_duration_ns": 2847500000,
                    "finish_reason": "stop"
                }
            }
        }


class BaseLLMClient(ABC):
    """
    Abstract base class for all LLM clients.
    
    All subclasses must implement:
    1. generate() - Generate text from prompt
    2. health_check() - Verify service is reachable
    
    Why abstract methods?
    - Forces subclasses to implement required functionality
    - Catches bugs at instantiation (not when user calls method)
    - Enables polymorphism (treat all clients uniformly)
    
    Example:
        class MyLLMClient(BaseLLMClient):
            pass  # Forgot to implement methods!
        
        client = MyLLMClient()  # ❌ TypeError: Can't instantiate abstract class
    """
    
    def __init__(self, model_name: str, timeout: int = 60):
        """
        Initialize base LLM client.
        
        Args:
            model_name: Name of the model to use (provider-specific format)
            timeout: Request timeout in seconds (default: 60s for slow LLM inference)
        """
        self.model_name = model_name
        self.timeout = timeout
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.2,
        **kwargs
    ) -> LLMResponse:
        """
        Generate text from prompt (MUST be implemented by subclasses).
        
        This is the main method for text generation. Each provider implements
        this differently (Ollama uses POST /api/generate, OpenAI uses POST /v1/chat/completions).
        
        Args:
            prompt: Input text to send to LLM
            max_tokens: Maximum tokens to generate (1 token ≈ 4 characters)
            temperature: Sampling temperature (0.0=deterministic, 2.0=random)
            **kwargs: Provider-specific options (top_p, top_k, stop_sequences, etc.)
        
        Returns:
            LLMResponse with generated text, tokens, latency
        
        Raises:
            RuntimeError: If LLM request fails (timeout, HTTP error, etc.)
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if LLM service is reachable and healthy (MUST be implemented by subclasses).
        
        This should be a lightweight check (< 5 seconds) that verifies:
        1. Service is running (can connect)
        2. Model is available (downloaded/loaded)
        
        Returns:
            True if service is healthy and ready, False otherwise
        
        Example:
            if await client.health_check():
                response = await client.generate("Hello")
            else:
                print("LLM service is down!")
        """
        pass
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"{self.__class__.__name__}(model={self.model_name}, timeout={self.timeout}s)"
