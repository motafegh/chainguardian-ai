#!/usr/bin/env python3
"""
Integration test for Ollama LLM functionality.
"""
import asyncio
import httpx
import time
import json
from typing import Dict, Any


async def test_ollama_connection(base_url: str = "http://localhost:11434") -> bool:
    """Test basic Ollama connection."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{base_url}/api/tags")
            if response.status_code == 200:
                print("✅ Ollama connection successful")
                print(f"Available models: {response.json()}")
                return True
            else:
                print(f"❌ Ollama connection failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Ollama connection error: {e}")
        return False


async def test_ollama_generation(
    model: str = "llama3.1",
    prompt: str = "Explain smart contract security in one sentence.",
    base_url: str = "http://localhost:11434"
) -> Dict[str, Any]:
    """Test Ollama text generation with performance metrics."""
    print(f"\n🧪 Testing Ollama generation with model: {model}")
    print(f"Prompt: {prompt[:100]}...")
    
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "num_predict": 100
                }
            }
            
            response = await client.post(
                f"{base_url}/api/generate",
                json=payload
            )
            
            latency = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                tokens_per_second = result.get("eval_count", 0) / latency if latency > 0 else 0
                
                print(f"✅ Generation successful in {latency:.2f}s")
                print(f"📊 Tokens: {result.get('eval_count', 'N/A')}")
                print(f"⚡ Speed: {tokens_per_second:.1f} tokens/sec")
                print(f"📝 Response: {result.get('response', '')[:200]}...")
                
                return {
                    "success": True,
                    "latency": latency,
                    "tokens": result.get("eval_count", 0),
                    "tokens_per_second": tokens_per_second,
                    "response": result.get("response", ""),
                    "model": model
                }
            else:
                print(f"❌ Generation failed: {response.status_code}")
                print(f"Error: {response.text}")
                return {
                    "success": False,
                    "error": response.text
                }
                
    except Exception as e:
        print(f"❌ Generation error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def benchmark_ollama(model: str = "llama3.1") -> None:
    """Run comprehensive benchmark tests."""
    print(f"\n{"="*60}")
    print(f"🧪 BENCHMARKING OLLAMA MODEL: {model}")
    print(f"{"="*60}")
    
    # Test 1: Simple response
    print("\n📋 Test 1: Simple Q&A")
    result1 = await test_ollama_generation(
        model=model,
        prompt="What is the capital of France?"
    )
    
    # Test 2: Code generation
    print("\n📋 Test 2: Code Generation")
    result2 = await test_ollama_generation(
        model=model,
        prompt="Write a Solidity function that safely transfers tokens."
    )
    
    # Test 3: Complex reasoning
    print("\n📋 Test 3: Security Analysis")
    result3 = await test_ollama_generation(
        model=model,
        prompt="Analyze this Solidity code for vulnerabilities: 'function withdraw() public { payable(msg.sender).transfer(address(this).balance); }'"
    )
    
    # Summary
    print(f"\n{"="*60}")
    print("📊 BENCHMARK SUMMARY")
    print(f"{"="*60}")
    
    results = [r for r in [result1, result2, result3] if r.get("success")]
    
    if results:
        avg_latency = sum(r["latency"] for r in results) / len(results)
        avg_tokens_per_second = sum(r["tokens_per_second"] for r in results) / len(results)
        
        print(f"✅ Model: {model}")
        print(f"📈 Average Latency: {avg_latency:.2f}s")
        print(f"⚡ Average Speed: {avg_tokens_per_second:.1f} tokens/sec")
        print(f"📊 Total Tests: {len(results)} successful, {3-len(results)} failed")
        
        # GPU check
        try:
            import subprocess
            gpu_info = subprocess.check_output(["nvidia-smi", "--query-gpu=name,memory.used,memory.total", "--format=csv"]).decode()
            print(f"\n🎮 GPU Info:\n{gpu_info}")
        except:
            print("\nℹ️ No GPU detected or nvidia-smi not available (running on CPU)")
    else:
        print("❌ All tests failed!")


async def test_api_integration() -> None:
    """Test the full API integration."""
    print(f"\n{"="*60}")
    print("🔌 TESTING API INTEGRATION")
    print(f{"="*60}")
    
    # Test health endpoint
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                print("✅ API health endpoint: OK")
            else:
                print(f"❌ API health endpoint: {response.status_code}")
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return
    
    # Test metrics endpoint
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8000/metrics")
            if response.status_code == 200:
                print("✅ Metrics endpoint: OK")
            else:
                print(f"❌ Metrics endpoint: {response.status_code}")
    except Exception as e:
        print(f"❌ Metrics endpoint failed: {e}")
    
    # Test reports endpoint
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "contract_code": "pragma solidity ^0.8.0; contract Test { uint public value; }",
                "contract_name": "TestContract",
                "format": "markdown",
                "depth": "intermediate",
                "llm_model": "llama3.1"
            }
            
            response = await client.post(
                "http://localhost:8000/api/v1/reports/generate",
                json=payload
            )
            
            if response.status_code in [200, 201]:
                print("✅ Reports endpoint: OK")
                print(f"Response time: {response.elapsed.total_seconds():.2f}s")
            else:
                print(f"❌ Reports endpoint: {response.status_code}")
                print(f"Error: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Reports endpoint failed: {e}")


async def main():
    """Main test runner."""
    print(f"\n{"="*60}")
    print("🧪 CHAINGUARDIAN LLM INTEGRATION TEST SUITE")
    print(f{"="*60}")
    
    # Test Ollama connection
    ollama_ok = await test_ollama_connection()
    
    if ollama_ok:
        # Run benchmarks
        await benchmark_ollama("llama3.1")
        
        # Test API integration
        await test_api_integration()
        
        print(f"\n{"="*60}")
        print("🎉 ALL TESTS COMPLETED")
        print(f{"="*60}")
    else:
        print("\n❌ Cannot proceed without Ollama connection")
        print("Please ensure Ollama is running on http://localhost:11434")
        print("Start with: docker-compose up -d ollama")


if __name__ == "__main__":
    asyncio.run(main())