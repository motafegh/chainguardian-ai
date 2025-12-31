"""
Complete System Integration Test
Tests all LLM components working together:
- Configuration
- Model Router
- Redis Cache
- Ollama Client
- Full workflow

Run:
    poetry run python test_complete_system.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from chainguardian.llm.config import llm_config
from chainguardian.llm.clients.ollama_client import OllamaClient
from chainguardian.llm.clients.model_router import ModelRouter
from chainguardian.llm.cache import RedisCache


# ============================================================================
# TEST DATA: Simulated Contract Features
# ============================================================================

SIMPLE_CONTRACT_FEATURES = {
    'lines_of_code': 50,
    'avg_function_complexity': 2,
    'external_calls_count': 0,
    'uses_assembly': False,
    'uses_delegatecall': False,
}

COMPLEX_CONTRACT_FEATURES = {
    'lines_of_code': 350,
    'avg_function_complexity': 15,
    'external_calls_count': 4,
    'uses_assembly': True,
    'uses_delegatecall': True,
}


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

async def test_configuration():
    """Test 1: Configuration System"""
    print("\n" + "="*70)
    print("🧪 TEST 1: Configuration System")
    print("="*70)
    
    print(f"\n📋 LLM Configuration:")
    print(f"   Simple model: {llm_config.simple_model}")
    print(f"   Complex model: {llm_config.complex_model}")
    print(f"   Complexity threshold: {llm_config.complexity_threshold}")
    print(f"   Cache enabled: {llm_config.cache_enabled}")
    print(f"   Cache TTL: {llm_config.cache_ttl}s")
    print(f"   Redis URL: {llm_config.redis_url}")
    print(f"   Ollama URL: {llm_config.ollama_base_url}")
    
    assert llm_config.simple_model == "qwen3:4b"
    assert llm_config.complex_model in ["codellama:7b", "codellama:7b-instruct"]
    assert llm_config.cache_enabled is True
    
    print("\n✅ Configuration test passed!")


async def test_redis_connection():
    """Test 2: Redis Cache Connection"""
    print("\n" + "="*70)
    print("🧪 TEST 2: Redis Cache Connection")
    print("="*70)
    
    cache = RedisCache()
    
    print(f"\n📡 Redis Configuration:")
    print(f"   URL: {cache.redis_url}")
    print(f"   TTL: {cache.ttl}s")
    print(f"   Enabled: {cache.enabled}")
    
    try:
        # Test connection
        client = await cache._get_client()
        await client.ping()
        print("\n✅ Redis connection successful!")
        
        # Test basic operations
        print("\n🧪 Testing basic Redis operations...")
        await client.set("test_key", "test_value", ex=10)
        value = await client.get("test_key")
        assert value == "test_value"
        await client.delete("test_key")
        print("✅ Redis operations work!")
        
        await cache.close()
        
    except Exception as e:
        print(f"\n❌ Redis connection failed: {e}")
        print("\n💡 Make sure Redis is running:")
        print("   docker run -d --name redis -p 6379:6379 redis:7-alpine")
        raise


async def test_model_router():
    """Test 3: Model Router"""
    print("\n" + "="*70)
    print("🧪 TEST 3: Model Router")
    print("="*70)
    
    router = ModelRouter()
    
    print(f"\n⚙️ Router Configuration:")
    print(f"   Threshold: {router.threshold}")
    print(f"   Simple model: {router.simple_model}")
    print(f"   Complex model: {router.complex_model}")
    
    # Test simple contract routing
    print("\n📝 Test Case 1: Simple Contract")
    client1, score1 = router.route(SIMPLE_CONTRACT_FEATURES)
    print(f"   Features: LOC={SIMPLE_CONTRACT_FEATURES['lines_of_code']}, "
          f"Complexity={SIMPLE_CONTRACT_FEATURES['avg_function_complexity']}")
    print(f"   Score: {score1}")
    print(f"   Routed to: {client1.model_name}")
    assert client1.model_name == router.simple_model
    assert score1.total < router.threshold
    print("   ✅ Correctly routed to simple model")
    
    # Test complex contract routing
    print("\n📝 Test Case 2: Complex Contract")
    client2, score2 = router.route(COMPLEX_CONTRACT_FEATURES)
    print(f"   Features: LOC={COMPLEX_CONTRACT_FEATURES['lines_of_code']}, "
          f"Complexity={COMPLEX_CONTRACT_FEATURES['avg_function_complexity']}, "
          f"Assembly={COMPLEX_CONTRACT_FEATURES['uses_assembly']}")
    print(f"   Score: {score2}")
    print(f"   Routed to: {client2.model_name}")
    assert client2.model_name == router.complex_model
    assert score2.total >= router.threshold
    print("   ✅ Correctly routed to complex model")
    
    print("\n✅ Model router test passed!")


async def test_ollama_client():
    """Test 4: Ollama Client"""
    print("\n" + "="*70)
    print("🧪 TEST 4: Ollama Client (Real LLM Call)")
    print("="*70)
    
    client = OllamaClient("qwen3:4b")
    
    print(f"\n🤖 Testing with model: {client.model_name}")
    print(f"   Server: {client.base_url}")
    
    # Test simple prompt
    prompt = "What is a reentrancy vulnerability in smart contracts? Answer in one sentence."
    
    print(f"\n📤 Sending prompt: {prompt[:60]}...")
    
    try:
        response = await client.generate(
            prompt=prompt,
            temperature=0.2,
            max_tokens=50
        )
        
        print(f"\n📥 Response received:")
        print(f"   Text: {response.text[:100]}...")
        print(f"   Model: {response.model}")
        print(f"   Tokens: {response.tokens_used}")
        print(f"   Latency: {response.latency_ms:.0f}ms")
        print(f"   Cached: {response.cached}")
        
        assert len(response.text) > 0
        assert response.tokens_used > 0
        assert response.latency_ms > 0
        
        print("\n✅ Ollama client test passed!")
        return response
        
    except Exception as e:
        print(f"\n❌ Ollama call failed: {e}")
        print("\n💡 Make sure:")
        print("   1. Ollama is running on Windows")
        print("   2. Model is pulled: ollama pull qwen3:4b")
        print("   3. .env has correct URL: LLM_OLLAMA_BASE_URL=http://172.21.16.1:11434")
        raise


async def test_cache_workflow():
    """Test 5: Complete Cache Workflow"""
    print("\n" + "="*70)
    print("🧪 TEST 5: Complete Cache Workflow")
    print("="*70)
    
    cache = RedisCache()
    client = OllamaClient("qwen3:4b")
    
    prompt = "Explain delegatecall in Solidity in one sentence."
    
    # Generate cache key
    cache_key = cache.generate_key(
        prompt=prompt,
        model=client.model_name,
        temperature=0.2,
        max_tokens=50
    )
    
    print(f"\n🔑 Cache key: {cache_key[:40]}...")
    
    # Reset stats for clean test
    cache.reset_stats()
    
    # Test 1: Cache miss (first call)
    print("\n📝 Test Case 1: Cache Miss (First Call)")
    cached1 = await cache.get(cache_key)
    print(f"   Cache result: {cached1}")
    assert cached1 is None
    print("   ✅ Cache miss (expected)")
    
    # Generate fresh response
    print("\n🤖 Generating fresh response from LLM...")
    response1 = await client.generate(
        prompt=prompt,
        temperature=0.2,
        max_tokens=50
    )
    print(f"   Response: {response1.text[:80]}...")
    print(f"   Latency: {response1.latency_ms:.0f}ms")
    
    # Store in cache
    print("\n💾 Storing in cache...")
    success = await cache.set(cache_key, response1, ttl=60)
    assert success is True
    print("   ✅ Stored successfully")
    
    # Test 2: Cache hit (second call)
    print("\n📝 Test Case 2: Cache Hit (Second Call)")
    cached2 = await cache.get(cache_key)
    print(f"   Cache result: {cached2 is not None}")
    assert cached2 is not None
    assert cached2.text == response1.text
    assert cached2.cached is True
    print(f"   Response: {cached2.text[:80]}...")
    print(f"   Latency: ~5ms (from cache)")
    print("   ✅ Cache hit (expected)")
    
    # Check stats
    print("\n📊 Cache Statistics:")
    stats = cache.stats
    print(f"   Hits: {stats['hits']}")
    print(f"   Misses: {stats['misses']}")
    print(f"   Hit rate: {stats['hit_rate']:.1%}")
    print(f"   Total requests: {stats['total_requests']}")
    
    assert stats['hits'] == 1
    assert stats['misses'] == 1
    assert stats['hit_rate'] == 0.5
    
    await cache.close()
    
    print("\n✅ Cache workflow test passed!")


async def test_complete_integration():
    """Test 6: Complete Integration (Router + Cache + LLM)"""
    print("\n" + "="*70)
    print("🧪 TEST 6: Complete Integration (All Components)")
    print("="*70)
    
    router = ModelRouter()
    cache = RedisCache()
    
    # Simulate analyzing a simple contract
    print("\n📋 Scenario: Analyzing a simple smart contract")
    print(f"   Contract features: {SIMPLE_CONTRACT_FEATURES}")
    
    # Step 1: Route to appropriate model
    print("\n🎯 Step 1: Routing to appropriate model...")
    client, score = router.route(SIMPLE_CONTRACT_FEATURES)
    print(f"   Complexity score: {score}")
    print(f"   Routed to: {client.model_name}")
    
    # Step 2: Build prompt (simulated)
    prompt = """Analyze this simple ERC20 token contract:
    
contract SimpleToken {
    mapping(address => uint) public balances;
    
    function transfer(address to, uint amount) public {
        require(balances[msg.sender] >= amount);
        balances[msg.sender] -= amount;
        balances[to] += amount;
    }
}

Identify any security vulnerabilities. Answer briefly."""
    
    # Step 3: Generate cache key
    print("\n🔑 Step 2: Generating cache key...")
    cache_key = cache.generate_key(
        prompt=prompt,
        model=client.model_name,
        temperature=0.2,
        max_tokens=200
    )
    print(f"   Key: {cache_key[:40]}...")
    
    # Step 4: Check cache
    print("\n🔍 Step 3: Checking cache...")
    cached = await cache.get(cache_key)
    
    if cached:
        print("   ✅ Cache hit! Returning cached response")
        response = cached
    else:
        print("   ❌ Cache miss! Generating fresh response")
        
        # Step 5: Generate via LLM
        print(f"\n🤖 Step 4: Generating response via {client.model_name}...")
        response = await client.generate(
            prompt=prompt,
            temperature=0.2,
            max_tokens=200
        )
        print(f"   Generated {response.tokens_used} tokens in {response.latency_ms:.0f}ms")
        
        # Step 6: Store in cache
        print("\n�� Step 5: Storing in cache...")
        await cache.set(cache_key, response, ttl=3600)
        print("   ✅ Stored for 1 hour")
    
    # Display result
    print("\n📄 Final Response:")
    print(f"   Model: {response.model}")
    print(f"   Tokens: {response.tokens_used}")
    print(f"   Latency: {response.latency_ms:.0f}ms")
    print(f"   Cached: {response.cached}")
    print(f"\n   Text:\n   {response.text[:200]}...")
    
    # Test cache hit on second call
    print("\n🔄 Step 6: Testing cache hit (second call)...")
    cached2 = await cache.get(cache_key)
    assert cached2 is not None
    print("   ✅ Cache hit! Response retrieved in ~5ms")
    
    await cache.close()
    
    print("\n✅ Complete integration test passed!")


async def test_performance_comparison():
    """Test 7: Performance Comparison (Cache vs No Cache)"""
    print("\n" + "="*70)
    print("🧪 TEST 7: Performance Comparison")
    print("="*70)
    
    cache = RedisCache()
    client = OllamaClient("qwen3:4b")
    
    prompt = "What is a smart contract?"
    cache_key = cache.generate_key(prompt, client.model_name, 0.2, 50)
    
    # First call (cache miss)
    print("\n⏱️ Call 1: Cache Miss (Fresh Generation)")
    import time
    start = time.time()
    response1 = await client.generate(prompt, temperature=0.2, max_tokens=50)
    end = time.time()
    latency1 = (end - start) * 1000
    await cache.set(cache_key, response1)
    print(f"   Latency: {latency1:.0f}ms")
    
    # Second call (cache hit)
    print("\n⏱️ Call 2: Cache Hit (From Redis)")
    start = time.time()
    response2 = await cache.get(cache_key)
    end = time.time()
    latency2 = (end - start) * 1000
    print(f"   Latency: {latency2:.0f}ms")
    
    # Calculate improvement
    improvement = (latency1 / latency2) if latency2 > 0 else 0
    print(f"\n📊 Performance Improvement:")
    print(f"   Cache miss: {latency1:.0f}ms")
    print(f"   Cache hit: {latency2:.0f}ms")
    print(f"   Speedup: {improvement:.0f}x faster! 🚀")
    
    await cache.close()
    
    print("\n✅ Performance comparison test passed!")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def main():
    """Run all integration tests."""
    print("\n" + "="*70)
    print("🚀 CHAINGUARDIAN LLM SYSTEM - COMPLETE INTEGRATION TEST")
    print("="*70)
    
    tests = [
        ("Configuration", test_configuration),
        ("Redis Connection", test_redis_connection),
        ("Model Router", test_model_router),
        ("Ollama Client", test_ollama_client),
        ("Cache Workflow", test_cache_workflow),
        ("Complete Integration", test_complete_integration),
        ("Performance Comparison", test_performance_comparison),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"\n❌ Test '{name}' FAILED: {e}")
            import traceback
            traceback.print_exc()
            
            # Continue with remaining tests
            continue
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"   Total tests: {len(tests)}")
    print(f"   Passed: {passed} ✅")
    print(f"   Failed: {failed} ❌")
    print(f"   Success rate: {(passed/len(tests))*100:.0f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Your LLM system is fully operational!")
        print("\n📝 Next steps:")
        print("   1. Integrate with FastAPI")
        print("   2. Add unit tests (pytest)")
        print("   3. Deploy to production")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please fix issues before continuing.")
    
    print("="*70)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
