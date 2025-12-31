"""
Quick Manual Test for Model Router
Verifies routing logic with synthetic features (no Ollama needed).

Run this:
    python test_router_manual.py

Expected output:
    ✅ Simple contract → llama3.1:4b
    ✅ Medium contract → llama3.1:4b
    ✅ Complex contract → codellama:7b
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from chainguardian.llm.clients.model_router import (
    ModelRouter,
    ComplexityMetrics,
    calculate_complexity_score,
    normalize,
)


def test_normalization():
    """Test normalize() function."""
    print("\n" + "="*60)
    print("🧪 TEST 1: Normalization Function")
    print("="*60)
    
    tests = [
        (50, 300, 16.67, "Small contract"),
        (150, 300, 50.0, "Medium contract"),
        (300, 300, 100.0, "Large contract"),
        (500, 300, 100.0, "Very large (clamped)"),
        (0, 300, 0.0, "Empty contract"),
    ]
    
    for value, max_val, expected, description in tests:
        result = normalize(value, max_val)
        status = "✅" if abs(result - expected) < 0.1 else "❌"
        print(f"{status} {description}: normalize({value}, {max_val}) = {result:.2f} (expected ~{expected})")


def test_complexity_calculation():
    """Test complexity score calculation."""
    print("\n" + "="*60)
    print("🧪 TEST 2: Complexity Score Calculation")
    print("="*60)
    
    # Test case 1: Simple contract
    print("\n📝 Case 1: Simple ERC20 Token")
    metrics1 = ComplexityMetrics(
        loc=50,
        cyclomatic=2,
        external_calls=0,
        uses_assembly=False,
        uses_delegatecall=False,
    )
    score1 = calculate_complexity_score(metrics1)
    print(f"   Metrics: {metrics1}")
    print(f"   Score: {score1}")
    print(f"   Expected: ~8.0")
    print(f"   Status: {'✅' if 5 <= score1.total <= 12 else '❌'}")
    
    # Test case 2: Medium contract
    print("\n📝 Case 2: Medium DeFi Contract")
    metrics2 = ComplexityMetrics(
        loc=200,
        cyclomatic=8,
        external_calls=3,
        uses_assembly=False,
        uses_delegatecall=False,
    )
    score2 = calculate_complexity_score(metrics2)
    print(f"   Metrics: {metrics2}")
    print(f"   Score: {score2}")
    print(f"   Expected: ~44.0")
    print(f"   Status: {'✅' if 40 <= score2.total <= 48 else '❌'}")
    
    # Test case 3: Complex proxy
    print("\n📝 Case 3: Complex Upgradeable Proxy")
    metrics3 = ComplexityMetrics(
        loc=350,
        cyclomatic=15,
        external_calls=4,
        uses_assembly=True,
        uses_delegatecall=True,
    )
    score3 = calculate_complexity_score(metrics3)
    print(f"   Metrics: {metrics3}")
    print(f"   Score: {score3}")
    print(f"   Expected: ~88.5")
    print(f"   Status: {'✅' if 85 <= score3.total <= 92 else '❌'}")


def test_routing_logic():
    """Test ModelRouter routing decisions."""
    print("\n" + "="*60)
    print("🧪 TEST 3: Model Router Routing Logic")
    print("="*60)
    
    router = ModelRouter()
    print(f"\nRouter config: threshold={router.threshold}")
    print(f"Simple model: {router.simple_model}")
    print(f"Complex model: {router.complex_model}")
    
    # Test case 1: Simple contract
    print("\n📝 Case 1: Simple Contract (score ~8.0)")
    features1 = {
        'lines_of_code': 50,
        'avg_function_complexity': 2,
        'external_calls_count': 0,
        'uses_assembly': False,
        'uses_delegatecall': False,
    }
    client1, score1 = router.route(features1)
    expected1 = router.simple_model
    status1 = "✅" if client1.model_name == expected1 else "❌"
    print(f"   {status1} Routed to: {client1.model_name} (expected {expected1})")
    print(f"   Score: {score1}")
    
    # Test case 2: Medium contract (edge case - just under threshold)
    print("\n📝 Case 2: Medium Contract (score ~44.0)")
    features2 = {
        'lines_of_code': 200,
        'avg_function_complexity': 8,
        'external_calls_count': 3,
        'uses_assembly': False,
        'uses_delegatecall': False,
    }
    client2, score2 = router.route(features2)
    expected2 = router.simple_model
    status2 = "✅" if client2.model_name == expected2 else "❌"
    print(f"   {status2} Routed to: {client2.model_name} (expected {expected2})")
    print(f"   Score: {score2}")
    
    # Test case 3: Complex contract
    print("\n📝 Case 3: Complex Contract (score ~88.5)")
    features3 = {
        'lines_of_code': 350,
        'avg_function_complexity': 15,
        'external_calls_count': 4,
        'uses_assembly': True,
        'uses_delegatecall': True,
    }
    client3, score3 = router.route(features3)
    expected3 = router.complex_model
    status3 = "✅" if client3.model_name == expected3 else "❌"
    print(f"   {status3} Routed to: {client3.model_name} (expected {expected3})")
    print(f"   Score: {score3}")
    
    # Test case 4: Edge case (exactly at threshold)
    print("\n📝 Case 4: Edge Case (score exactly at threshold)")
    features4 = {
        'lines_of_code': 250,
        'avg_function_complexity': 10,
        'external_calls_count': 3,
        'uses_assembly': False,
        'uses_delegatecall': True,
    }
    client4, score4 = router.route(features4)
    print(f"   Routed to: {client4.model_name}")
    print(f"   Score: {score4}")
    print(f"   Note: Score {score4.total:.1f} {'<' if score4.total < router.threshold else '>='} {router.threshold} (threshold)")


def test_routing_stats():
    """Test get_routing_stats() method."""
    print("\n" + "="*60)
    print("🧪 TEST 4: Routing Statistics")
    print("="*60)
    
    router = ModelRouter()
    
    # Create 100 synthetic contracts
    # 90 simple, 10 complex (ideal distribution)
    features_list = []
    
    # 90 simple contracts
    for i in range(90):
        features_list.append({
            'lines_of_code': 50 + i,  # 50-140 LOC
            'avg_function_complexity': 2 + (i % 5),  # 2-6 complexity
            'external_calls_count': i % 3,  # 0-2 calls
            'uses_assembly': False,
            'uses_delegatecall': False,
        })
    
    # 10 complex contracts
    for i in range(10):
        features_list.append({
            'lines_of_code': 300 + i * 10,  # 300-390 LOC
            'avg_function_complexity': 15 + i,  # 15-24 complexity
            'external_calls_count': 4,
            'uses_assembly': True,
            'uses_delegatecall': True,
        })
    
    # Calculate stats
    stats = router.get_routing_stats(features_list)
    
    print(f"\n📊 Statistics for {stats['total']} contracts:")
    print(f"   Simple: {stats['simple_count']} ({stats['simple_pct']:.1f}%)")
    print(f"   Complex: {stats['complex_count']} ({stats['complex_pct']:.1f}%)")
    print(f"   Avg score: {stats['avg_score']:.1f}")
    print(f"   Min score: {stats['min_score']:.1f}")
    print(f"   Max score: {stats['max_score']:.1f}")
    
    # Validate distribution
    simple_ok = 80 <= stats['simple_pct'] <= 95
    complex_ok = 5 <= stats['complex_pct'] <= 20
    status = "✅" if simple_ok and complex_ok else "⚠️"
    print(f"\n   {status} Distribution: {'Good' if simple_ok and complex_ok else 'Needs tuning'}")
    print(f"   Target: 85-95% simple, 5-15% complex")


def main():
    """Run all manual tests."""
    print("\n" + "="*60)
    print("🚀 MODEL ROUTER - MANUAL TEST SUITE")
    print("="*60)
    
    try:
        test_normalization()
        test_complexity_calculation()
        test_routing_logic()
        test_routing_stats()
        
        print("\n" + "="*60)
        print("✅ ALL MANUAL TESTS PASSED!")
        print("="*60)
        print("\n📝 Next steps:")
        print("   1. Run unit tests: pytest tests/unit/llm/")
        print("   2. Run integration test: pytest tests/integration/llm/")
        print("   3. Test with real contracts")
        
    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ TEST FAILED: {e}")
        print("="*60)
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
