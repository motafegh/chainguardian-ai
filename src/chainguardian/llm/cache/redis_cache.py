"""
Redis Cache Layer for LLM Responses
Provides response caching to reduce latency and costs.

🎯 PURPOSE:
- Cache LLM responses for repeated prompts (80%+ hit rate expected)
- Reduce latency from 3000ms → 5ms on cache hits (600x faster!)
- Share cache across multiple API workers
- Automatic expiration via TTL

🔑 KEY CONCEPTS:
- Cache key = hash(prompt + model + temperature + max_tokens)
- TTL = 1 hour (balance between freshness and hit rate)
- Serialization = JSON (store LLMResponse as JSON string)
- Metrics = Track hit/miss rates for optimization

📊 EXPECTED PERFORMANCE:
- Cache hit rate: 80%+
- Cache hit latency: ~5ms
- Cache miss latency: ~3000ms (LLM generation)
- Average latency: 0.8 × 5ms + 0.2 × 3000ms = 604ms
- Improvement: 5x faster than no cache!

🏗️ ARCHITECTURE:
1. User request → Generate cache key (hash)
2. Check Redis → Cache hit? Return cached (5ms)
3. Cache miss? → Generate via LLM (3000ms)
4. Store in Redis → Set TTL (1 hour)
5. Return fresh response

Example:
    from chainguardian.llm.cache import RedisCache
    from chainguardian.llm.clients import OllamaClient
    
    cache = RedisCache()
    client = OllamaClient("llama3.1:4b")
    
    # Generate cache key
    cache_key = cache.generate_key(
        prompt="Explain reentrancy",
        model="llama3.1:4b",
        temperature=0.2,
        max_tokens=100
    )
    
    # Check cache first
    cached = await cache.get(cache_key)
    if cached:
        return cached  # 5ms latency!
    
    # Cache miss, generate fresh
    response = await client.generate(prompt)
    
    # Store in cache
    await cache.set(cache_key, response, ttl=3600)
    
    return response
"""

# 🔥 CRITICAL: Standard libraries
import hashlib  # For SHA256 hashing (cache keys)
import json  # For serializing LLMResponse to JSON
from typing import Optional, Dict, Any

# 🔥 CRITICAL: Third-party libraries
import redis.asyncio as redis  # Async Redis client
from loguru import logger

# 🔥 CRITICAL: Our modules
from chainguardian.llm.clients.base import LLMResponse
from chainguardian.llm.config import llm_config


# ============================================================================
# CACHE KEY GENERATION (Module-level function)
# ============================================================================

def generate_cache_key(
    prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
    **kwargs
) -> str:
    """
    Generate deterministic cache key from request parameters.
    
    🎓 CONCEPT: Deterministic Hashing
    - Same inputs → Same hash (always)
    - Different inputs → Different hash (always)
    - Hash is fixed length (64 chars for SHA256)
    
    🔑 KEY COMPONENTS:
    1. Prompt - Main input (different prompt = different response)
    2. Model - Different models = different responses
    3. Temperature - Affects randomness
    4. Max tokens - Affects response length
    5. **kwargs - Any other parameters that affect output
    
    🎯 WHY HASH INSTEAD OF USING PROMPT AS KEY?
    - Prompt can be 1000+ chars (inefficient lookup)
    - Hash is always 64 chars (fast lookup)
    - Hash handles special characters (no escaping needed)
    - Hash is deterministic (same input = same hash)
    
    🧮 SHA256 ALGORITHM:
    - Input: Arbitrary length string
    - Output: 256-bit (64 hex chars) hash
    - Properties: Fast, collision-resistant, deterministic
    
    Args:
        prompt: Input text for LLM
        model: Model name (e.g., "llama3.1:4b")
        temperature: Sampling temperature (0.0-2.0)
        max_tokens: Maximum tokens to generate
        **kwargs: Additional parameters (top_p, top_k, etc.)
    
    Returns:
        64-character hex string (SHA256 hash) prefixed with "llm:cache:"
    
    Example:
        key1 = generate_cache_key(
            prompt="Explain reentrancy",
            model="llama3.1:4b",
            temperature=0.2,
            max_tokens=100
        )
        # "llm:cache:a3f8d9e2c1b4..." (64 chars)
        
        # Same inputs = same hash
        key2 = generate_cache_key(
            prompt="Explain reentrancy",
            model="llama3.1:4b",
            temperature=0.2,
            max_tokens=100
        )
        assert key1 == key2  # ✅ Same hash
        
        # Different temperature = different hash
        key3 = generate_cache_key(
            prompt="Explain reentrancy",
            model="llama3.1:4b",
            temperature=0.3,  # Changed!
            max_tokens=100
        )
        assert key1 != key3  # ✅ Different hash
    """
    # 📘 IMPORTANT: Create dictionary with all parameters
    # Order matters! We use sort_keys=True to ensure consistent ordering
    key_data = {
        'prompt': prompt,
        'model': model,
        'temperature': temperature,
        'max_tokens': max_tokens,
        **kwargs  # Include any additional parameters
    }
    
    # 📘 IMPORTANT: Serialize to JSON with sorted keys
    # sort_keys=True ensures deterministic ordering
    # {"a": 1, "b": 2} and {"b": 2, "a": 1} produce same JSON
    key_string = json.dumps(key_data, sort_keys=True)
    
    # 🔥 CRITICAL: Hash the JSON string
    # SHA256 produces 256-bit hash (32 bytes)
    # hexdigest() converts to 64-character hex string
    key_hash = hashlib.sha256(key_string.encode('utf-8')).hexdigest()
    
    # 🎯 PATTERN: Add prefix for clarity
    # Helps identify cache keys in Redis (debugging)
    # "llm:cache:a3f8..." is clearly an LLM cache key
    cache_key = f"llm:cache:{key_hash}"
    
    # 📊 LOG: Debug logging (helps troubleshoot cache misses)
    logger.debug(
        f"Generated cache key: {cache_key[:20]}... "
        f"(model={model}, temp={temperature}, tokens={max_tokens})"
    )
    
    return cache_key


# ============================================================================
# REDIS CACHE CLASS
# ============================================================================

class RedisCache:
    """
    Redis-based cache for LLM responses.
    
    🎯 FEATURES:
    - Async operations (non-blocking)
    - Connection pooling (reuse connections)
    - Automatic serialization (LLMResponse ↔ JSON)
    - TTL management (automatic expiration)
    - Metrics tracking (hit/miss rates)
    - Error handling (graceful degradation)
    
    🔧 CONFIGURATION:
    - Redis URL: From llm_config.redis_url
    - TTL: From llm_config.cache_ttl (default: 3600s = 1 hour)
    - Enabled: From llm_config.cache_enabled (can disable cache)
    
    📊 METRICS:
    - hits: Number of cache hits
    - misses: Number of cache misses
    - errors: Number of Redis errors
    - hit_rate: hits / (hits + misses)
    
    Example:
        cache = RedisCache()
        
        # Check if cache is enabled
        if not cache.enabled:
            return await generate_without_cache()
        
        # Try cache
        cache_key = cache.generate_key(prompt, model, temperature, max_tokens)
        cached = await cache.get(cache_key)
        
        if cached:
            return cached  # Cache hit!
        
        # Cache miss, generate fresh
        response = await llm_client.generate(prompt)
        await cache.set(cache_key, response)
        
        return response
    """
    
    def __init__(
        self,
        redis_url: str = None,
        ttl: int = None,
        enabled: bool = None,
    ):
        """
        Initialize Redis cache with configuration.
        
        🎓 CONCEPT: Dependency Injection
        - Constructor accepts optional parameters
        - Falls back to config defaults if not provided
        - Makes testing easier (can inject mock Redis)
        
        Args:
            redis_url: Redis connection string (default: from config)
                Format: "redis://host:port/db"
                Example: "redis://localhost:6379/0"
            
            ttl: Cache TTL in seconds (default: from config)
                How long to keep cached responses
                
            enabled: Whether caching is enabled (default: from config)
                Can disable cache for debugging/testing
        
        Example:
            # Use config defaults
            cache = RedisCache()
            
            # Override for testing
            cache = RedisCache(
                redis_url="redis://localhost:6379/1",  # Test DB
                ttl=60,  # Shorter TTL for tests
                enabled=True
            )
        """
        # 📘 IMPORTANT: Use provided values or fall back to config
        self.redis_url = redis_url or llm_config.redis_url
        self.ttl = ttl if ttl is not None else llm_config.cache_ttl
        self.enabled = enabled if enabled is not None else llm_config.cache_enabled
        
        # 🔥 CRITICAL: Initialize Redis client (async)
        # Connection is lazy - only connects when first used
        # decode_responses=True: Return strings, not bytes
        self._client = None  # Will be initialized on first use
        
        # 📊 METRICS: Track cache performance
        self._hits = 0  # Number of cache hits
        self._misses = 0  # Number of cache misses
        self._errors = 0  # Number of Redis errors
        
        # 🎯 PATTERN: Log initialization
        logger.info(
            f"RedisCache initialized: "
            f"url={self.redis_url}, "
            f"ttl={self.ttl}s, "
            f"enabled={self.enabled}"
        )
        
        # ⚠️ WARNING: If disabled, log it prominently
        if not self.enabled:
            logger.warning("⚠️ Cache is DISABLED! All requests will hit LLM.")
    
    async def _get_client(self) -> redis.Redis:
        """
        Get or create Redis client (lazy initialization).
        
        🎓 CONCEPT: Lazy Initialization
        - Don't connect to Redis until first cache operation
        - Saves resources if cache is disabled
        - Allows app to start even if Redis is down
        
        Why async?
        - redis.from_url() is async in redis.asyncio
        - Must be called with await
        - Creates connection pool asynchronously
        
        Returns:
            Connected Redis client
        
        Raises:
            redis.ConnectionError: If can't connect to Redis
        """
        # 📘 IMPORTANT: Check if already initialized
        if self._client is None:
            try:
                # 🔥 CRITICAL: Create Redis client with connection pooling
                # decode_responses=True: Return strings, not bytes
                # max_connections=10: Pool size (reuse connections)
                self._client = await redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,  # Return strings, not bytes
                    max_connections=10,  # Connection pool size
                )
                
                # 📘 IMPORTANT: Test connection with PING
                await self._client.ping()
                
                logger.info(f"✅ Connected to Redis: {self.redis_url}")
                
            except Exception as e:
                logger.error(f"❌ Failed to connect to Redis: {e}")
                self._errors += 1
                raise
        
        return self._client
    
    async def close(self):
        """
        Close Redis connection (cleanup).
        
        🎓 CONCEPT: Resource Management
        - Always close connections when done
        - Frees resources (memory, sockets)
        - Prevents connection leaks
        
        Call this:
        - On app shutdown
        - In finally blocks
        - With async context manager
        
        Example:
            cache = RedisCache()
            try:
                await cache.get(key)
            finally:
                await cache.close()  # Always cleanup
            
            # Or use context manager:
            async with RedisCache() as cache:
                await cache.get(key)
            # Automatically closes
        """
        if self._client is not None:
            await self._client.close()
            logger.info("🔌 Redis connection closed")
    
    # 🎯 PATTERN: Context manager support
    async def __aenter__(self):
        """Enter async context (setup)."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context (cleanup)."""
        await self.close()
    
    def _serialize_response(self, response: LLMResponse) -> str:
        """
        Serialize LLMResponse to JSON string for Redis storage.
        
        🎓 CONCEPT: Serialization
        - Redis stores strings (or bytes)
        - Python objects must be converted to strings
        - JSON is human-readable, widely supported
        
        Why not pickle?
        - ❌ Binary format (hard to debug)
        - ❌ Python-specific (not cross-language)
        - ❌ Security risk (can execute code)
        - ✅ JSON is safer, readable, cross-platform
        
        Args:
            response: LLMResponse object to serialize
        
        Returns:
            JSON string representation
        
        Example:
            response = LLMResponse(
                text="Reentrancy is...",
                model="llama3.1:4b",
                tokens_used=87,
                latency_ms=2847.5,
                cached=False,
                metadata={"prompt_tokens": 45}
            )
            
            json_str = cache._serialize_response(response)
            # '{"text": "Reentrancy is...", "model": "llama3.1:4b", ...}'
        """
        # 📘 IMPORTANT: Convert Pydantic model to dict
        # model_dump() is Pydantic v2 method (was dict() in v1)
        response_dict = response.model_dump()
        
        # 🔥 CRITICAL: Mark as cached (for metrics)
        response_dict['cached'] = True
        
        # 📘 IMPORTANT: Serialize to JSON string
        # indent=None: Compact JSON (saves space)
        # ensure_ascii=False: Support Unicode characters
        json_str = json.dumps(response_dict, ensure_ascii=False)
        
        return json_str
    
    def _deserialize_response(self, json_str: str) -> LLMResponse:
        """
        Deserialize JSON string back to LLMResponse object.
        
        🎓 CONCEPT: Deserialization
        - Convert stored string back to Python object
        - JSON → dict → Pydantic model
        - Pydantic validates during construction
        
        Args:
            json_str: JSON string from Redis
        
        Returns:
            LLMResponse object
        
        Raises:
            json.JSONDecodeError: If JSON is invalid
            pydantic.ValidationError: If data doesn't match model
        
        Example:
            json_str = '{"text": "Reentrancy is...", ...}'
            response = cache._deserialize_response(json_str)
            
            print(response.text)  # "Reentrancy is..."
            print(response.cached)  # True
        """
        # 📘 IMPORTANT: Parse JSON string to dict
        response_dict = json.loads(json_str)
        
        # 🔥 CRITICAL: Construct Pydantic model from dict
        # Pydantic validates all fields during construction
        # Will raise ValidationError if data is invalid
        response = LLMResponse(**response_dict)
        
        return response
    
    async def get(self, cache_key: str) -> Optional[LLMResponse]:
        """
        Get cached response from Redis.
        
        🎓 WORKFLOW:
        1. Check if cache is enabled (return None if disabled)
        2. Connect to Redis
        3. Lookup key (GET command)
        4. If found: Deserialize JSON → LLMResponse
        5. Update metrics (hit or miss)
        6. Return result
        
        Args:
            cache_key: Cache key (from generate_cache_key)
        
        Returns:
            LLMResponse if cache hit, None if cache miss
        
        Example:
            cache_key = generate_cache_key(prompt, model, temperature, max_tokens)
            cached = await cache.get(cache_key)
            
            if cached:
                print(f"Cache hit! {cached.text}")
                print(f"Latency: 5ms")
            else:
                print("Cache miss, generating fresh...")
        """
        # ⚠️ EARLY RETURN: If cache disabled, always miss
        if not self.enabled:
            return None
        
        try:
            # 🔥 CRITICAL: Get Redis client
            client = await self._get_client()
            
            # 📘 IMPORTANT: Lookup key in Redis (GET command)
            json_str = await client.get(cache_key)
            
            # 📘 IMPORTANT: Check if key exists
            if json_str is None:
                # Cache miss
                self._misses += 1
                logger.debug(f"Cache miss: {cache_key[:20]}...")
                return None
            
            # 🔥 CRITICAL: Deserialize JSON → LLMResponse
            response = self._deserialize_response(json_str)
            
            # 📊 METRICS: Record cache hit
            self._hits += 1
            logger.info(
                f"✅ Cache hit: {cache_key[:20]}... "
                f"(hit_rate={self.hit_rate:.1%})"
            )
            
            return response
            
        except redis.ConnectionError as e:
            # Redis is down, log and continue without cache
            self._errors += 1
            logger.error(f"❌ Redis connection error: {e}")
            return None
            
        except Exception as e:
            # Unexpected error, log and continue without cache
            self._errors += 1
            logger.error(f"💥 Cache get error: {e}")
            return None
    
    async def set(
        self,
        cache_key: str,
        response: LLMResponse,
        ttl: int = None,
    ) -> bool:
        """
        Store response in Redis cache.
        
        🎓 WORKFLOW:
        1. Check if cache is enabled (return False if disabled)
        2. Connect to Redis
        3. Serialize LLMResponse → JSON
        4. Store with TTL (SETEX command)
        5. Return success status
        
        Args:
            cache_key: Cache key (from generate_cache_key)
            response: LLMResponse to cache
            ttl: Time-to-live in seconds (default: from config)
        
        Returns:
            True if stored successfully, False otherwise
        
        Example:
            response = await llm_client.generate(prompt)
            
            cache_key = generate_cache_key(prompt, model, temperature, max_tokens)
            success = await cache.set(cache_key, response, ttl=3600)
            
            if success:
                print("Stored in cache for 1 hour")
            else:
                print("Cache storage failed (non-critical)")
        """
        # ⚠️ EARLY RETURN: If cache disabled, don't store
        if not self.enabled:
            return False
        
        # 📘 IMPORTANT: Use provided TTL or default from config
        ttl = ttl if ttl is not None else self.ttl
        
        try:
            # 🔥 CRITICAL: Get Redis client
            client = await self._get_client()
            
            # 📘 IMPORTANT: Serialize LLMResponse → JSON
            json_str = self._serialize_response(response)
            
            # 🔥 CRITICAL: Store in Redis with TTL (SETEX command)
            # SETEX = SET + EXPIRE (atomic operation)
            await client.setex(
                name=cache_key,
                time=ttl,  # Seconds until expiration
                value=json_str
            )
            
            logger.debug(
                f"Stored in cache: {cache_key[:20]}... (ttl={ttl}s)"
            )
            
            return True
            
        except redis.ConnectionError as e:
            # Redis is down, log and continue (non-critical)
            self._errors += 1
            logger.error(f"❌ Redis connection error: {e}")
            return False
            
        except Exception as e:
            # Unexpected error, log and continue (non-critical)
            self._errors += 1
            logger.error(f"💥 Cache set error: {e}")
            return False
    
    def generate_key(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> str:
        """
        Generate cache key from request parameters.
        
        This is a wrapper around the module-level generate_cache_key function
        to make it accessible as an instance method.
        
        Args:
            prompt: Input text for LLM
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
        
        Returns:
            Cache key string
        
        Example:
            cache = RedisCache()
            key = cache.generate_key(
                prompt="Explain reentrancy",
                model="llama3.1:4b",
                temperature=0.2,
                max_tokens=100
            )
        """
        return generate_cache_key(prompt, model, temperature, max_tokens, **kwargs)
    
    @property
    def hit_rate(self) -> float:
        """
        Calculate cache hit rate.
        
        🎓 CONCEPT: Property Decorator
        - @property makes method look like attribute
        - Calculates value on-the-fly (no storage)
        - Read-only (no setter)
        
        Returns:
            Hit rate as fraction (0.0-1.0)
            0.8 = 80% hit rate
        
        Example:
            cache = RedisCache()
            # ... do some cache operations ...
            
            print(f"Hit rate: {cache.hit_rate:.1%}")
            # "Hit rate: 80.5%"
        """
        total = self._hits + self._misses
        
        if total == 0:
            return 0.0
        
        return self._hits / total
    
    @property
    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache metrics
        
        Example:
            stats = cache.stats
            print(json.dumps(stats, indent=2))
            # {
            #   "enabled": true,
            #   "hits": 85,
            #   "misses": 15,
            #   "errors": 2,
            #   "hit_rate": 0.85,
            #   "total_requests": 100
            # }
        """
        return {
            "enabled": self.enabled,
            "hits": self._hits,
            "misses": self._misses,
            "errors": self._errors,
            "hit_rate": self.hit_rate,
            "total_requests": self._hits + self._misses,
        }
    
    def reset_stats(self):
        """
        Reset cache statistics (for testing/monitoring).
        
        Example:
            # Before load test
            cache.reset_stats()
            
            # Run load test
            for i in range(1000):
                await cache.get(key)
            
            # Check results
            print(f"Hit rate: {cache.hit_rate:.1%}")
        """
        self._hits = 0
        self._misses = 0
        self._errors = 0
        logger.info("📊 Cache stats reset")
