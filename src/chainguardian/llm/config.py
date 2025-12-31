"""
LLM Configuration Module
Manages all settings for LLM system with environment variable support.

Key Features:
- Pydantic-based validation (fail-fast on invalid config)
- Environment variable overrides (12-factor app methodology)
- Model selection (simple vs complex routing)
- Cache settings (Redis TTL, enabled/disabled)
- Generation parameters (temperature, max_tokens)

Example:
    # Use defaults
    from chainguardian.llm.config import llm_config
    print(llm_config.simple_model)  # "llama3.1:4b"
    
    # Override via environment
    export LLM_SIMPLE_MODEL="llama3.2:3b"
    export LLM_CACHE_TTL=7200
"""

from typing import Literal
from pydantic_settings import BaseSettings
from pydantic import Field


class LLMConfig(BaseSettings):
    """
    LLM system configuration with validation.
    
    All settings can be overridden via environment variables with LLM_ prefix.
    Example: LLM_OLLAMA_BASE_URL, LLM_SIMPLE_MODEL, LLM_CACHE_ENABLED
    
    Why Pydantic BaseSettings?
    - Type validation at startup (catch errors early)
    - Environment variable support (deploy anywhere)
    - Default values for development
    - Self-documenting configuration
    """
    
    # ==================== Ollama Server Settings ====================
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama API endpoint. Change to http://ollama:11434 in Docker."
    )
    
    ollama_timeout: int = Field(
        default=60,
        ge=10,
        le=300,
        description="Request timeout in seconds. LLM generation is slow (3-5s typical)."
    )
    
    # ==================== Model Configuration ====================
    simple_model: str = Field(
        default="llama3.1:4b",
        description="Fast model for simple contracts (90% of requests). Uses 2.5GB VRAM."
    )
    
    complex_model: str = Field(
        default="codellama:7b-instruct",
        description="Accurate model for complex contracts (10% of requests). Uses 3.5GB VRAM."
    )
    
    # ==================== Routing Logic ====================
    complexity_threshold: int = Field(
        default=50,
        ge=0,
        le=100,
        description=(
            "Complexity score threshold (0-100). "
            "If score >= threshold, route to complex_model. "
            "Score factors: LOC (30%), cyclomatic (30%), external calls (20%), "
            "custom patterns (20%)."
        )
    )
    
    # ==================== Cache Settings ====================
    cache_enabled: bool = Field(
        default=True,
        description="Enable Redis response caching. Reduces latency by ~80% on cache hits."
    )
    
    cache_ttl: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Cache TTL in seconds (1 hour default). Range: 1 min to 24 hours."
    )
    
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string. Format: redis://host:port/db"
    )
    
    # ==================== Generation Settings ====================
    max_tokens: int = Field(
        default=500,
        ge=50,
        le=2000,
        description=(
            "Maximum output tokens per request. "
            "1 token ≈ 4 characters. "
            "500 tokens ≈ 2000 characters ≈ 300-400 words."
        )
    )
    
    temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
        description=(
            "Sampling temperature (randomness level). "
            "0.0 = deterministic (same output every time), "
            "0.2 = low randomness (good for technical reports), "
            "0.8 = high randomness (creative writing), "
            "2.0 = maximum randomness (experimental)."
        )
    )
    
    # ==================== Advanced Settings ====================
    stream_responses: bool = Field(
        default=False,
        description=(
            "Enable streaming (token-by-token) responses. "
            "False = wait for full response (easier to cache). "
            "True = typewriter effect (better UX, harder to implement)."
        )
    )
    
    retry_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of retry attempts on LLM failure."
    )
    
    retry_delay: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Delay between retry attempts in seconds (exponential backoff)."
    )
    
    class Config:
        """Pydantic configuration."""
        env_prefix = "LLM_"  # Environment variables: LLM_SIMPLE_MODEL, LLM_CACHE_ENABLED, etc.
        case_sensitive = False  # LLM_simple_model and LLM_SIMPLE_MODEL both work
        env_file = ".env"  # Load from .env file if present
        env_file_encoding = "utf-8"
        extra = "ignore"


# ==================== Singleton Instance ====================
# Global instance - import this in other modules
llm_config = LLMConfig()

# Log configuration on import (helpful for debugging)
if __name__ != "__main__":
    from loguru import logger
    logger.info(
        f"LLM Config loaded: "
        f"simple={llm_config.simple_model}, "
        f"complex={llm_config.complex_model}, "
        f"cache={'enabled' if llm_config.cache_enabled else 'disabled'}, "
        f"ollama={llm_config.ollama_base_url}"
    )
