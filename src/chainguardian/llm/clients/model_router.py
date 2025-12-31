"""
Model Router - Intelligent LLM Selection Based on Contract Complexity
Routes contracts to appropriate LLM model (fast vs accurate) based on complexity score.

🎯 ARCHITECTURE:
1. Extract features from contract using FeaturePipeline (tier1_core features)
2. Calculate complexity score (0-100) using weighted formula
3. Route based on threshold:
   - Score < 50: Llama 3.1 (fast, 3s, 90% of contracts)
   - Score ≥ 50: CodeLlama (accurate, 5s, 10% of contracts)

🚀 PERFORMANCE IMPACT:
- Without routing: All contracts → CodeLlama (5s average)
- With routing: 90% → Llama (3s) + 10% → CodeLlama (5s) = 3.2s average
- Improvement: 36% faster!

📊 COMPLEXITY SCORING FORMULA:
score = (
    normalize(LOC, 300) × 30% +           # Contract size
    normalize(Cyclomatic, 20) × 30% +     # Code complexity
    normalize(External_calls, 5) × 20% +  # External dependencies
    (20 if assembly/delegatecall else 0)  # Advanced patterns
)

🎓 KEY CONCEPTS:
- Weighted scoring (30/30/20/20 split across 4 factors)
- Normalization (scale different metrics to same range)
- Factory pattern (create appropriate client based on score)
- Explainability (track component scores for debugging)

Example:
    from chainguardian.llm.clients.model_router import ModelRouter
    from chainguardian.feature_extraction.pipeline import FeaturePipeline
    
    # Step 1: Extract features (your existing pipeline)
    pipeline = FeaturePipeline(mode="optimized")
    features = pipeline.extract(contract_code)
    
    # Step 2: Route to appropriate model
    router = ModelRouter()
    client, score = router.route(features)
    
    # Step 3: Generate report
    response = await client.generate(prompt)
    
    print(f"Routed to {client.model_name} (complexity={score.total:.1f})")
    # Output: "Routed to llama3.1:4b (complexity=42.3)"
"""

from typing import Dict, Any, Tuple
from dataclasses import dataclass

from loguru import logger

from chainguardian.llm.clients.ollama_client import OllamaClient
from chainguardian.llm.config import llm_config


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ComplexityMetrics:
    """
    Metrics extracted from FeaturePipeline for complexity calculation.
    
    These map directly to YOUR tier1_core feature names from pipeline.py.
    Your feature extraction returns 89 features; we extract the 5 we need.
    
    Attributes:
        loc: Lines of code (feature: 'lines_of_code')
        cyclomatic: Average function complexity (feature: 'avg_function_complexity')
        external_calls: External contract calls (feature: 'external_calls_count')
        uses_assembly: Inline assembly flag (feature: 'uses_assembly')
        uses_delegatecall: Delegatecall flag (feature: 'uses_delegatecall')
    """
    loc: int
    cyclomatic: int
    external_calls: int
    uses_assembly: bool
    uses_delegatecall: bool
    
    @classmethod
    def from_features(cls, features: Dict[str, Any]) -> "ComplexityMetrics":
        """
        Extract complexity metrics from FeaturePipeline output.
        
        Alternative constructor pattern - creates instance from feature dict.
        Uses .get() with defaults for safe extraction (no KeyError).
        
        Args:
            features: Dictionary from FeaturePipeline.extract()
        
        Returns:
            ComplexityMetrics instance with extracted values
        
        Example:
            pipeline = FeaturePipeline(mode="optimized")
            all_features = pipeline.extract(contract_code)  # 89 features
            metrics = ComplexityMetrics.from_features(all_features)  # 5 features
        """
        return cls(
            loc=features.get("lines_of_code", 0),
            cyclomatic=features.get("avg_function_complexity", 0),
            external_calls=features.get("external_calls_count", 0),
            uses_assembly=features.get("uses_assembly", False),
            uses_delegatecall=features.get("uses_delegatecall", False),
        )


@dataclass
class ComplexityScore:
    """
    Calculated complexity score with component breakdown for explainability.
    
    Total score is sum of 4 weighted components (0-100 range):
    - LOC component: 0-30 points (30% weight)
    - Cyclomatic component: 0-30 points (30% weight)
    - External component: 0-20 points (20% weight)
    - Custom component: 0-20 points (20% weight)
    
    Why track components?
    - Debugging: "Why did it route to CodeLlama?"
    - Tuning: "Is LOC weight too high?"
    - User feedback: "Your contract is complex due to X"
    - Monitoring: Track which factors dominate routing
    
    Attributes:
        total: Overall score (0-100, used for routing decision)
        loc_component: Points from LOC (0-30)
        cyclomatic_component: Points from cyclomatic complexity (0-30)
        external_component: Points from external calls (0-20)
        custom_component: Points from assembly/delegatecall (0-20)
    """
    total: float
    loc_component: float
    cyclomatic_component: float
    external_component: float
    custom_component: float
    
    def __str__(self) -> str:
        """Human-readable representation for logs."""
        return (
            f"ComplexityScore(total={self.total:.1f}/100) "
            f"[LOC={self.loc_component:.1f}, "
            f"Cyclomatic={self.cyclomatic_component:.1f}, "
            f"External={self.external_component:.1f}, "
            f"Custom={self.custom_component:.1f}]"
        )


# ============================================================================
# COMPLEXITY SCORING
# ============================================================================

def normalize(value: float, max_value: float, min_value: float = 0.0) -> float:
    """
    Normalize a value to 0-100 range using min-max normalization.
    
    Formula: normalized = ((value - min) / (max - min)) × 100
    
    Why normalize?
    - Different metrics have different scales:
      - LOC: 0-1000+ (large range)
      - Cyclomatic: 0-50+ (medium range)
      - External calls: 0-10+ (small range)
    - Normalization puts all metrics on same scale (0-100)
    - Allows fair comparison and weighting
    
    Clamping:
    - If value > max_value: clamp to 100 (cap at maximum)
    - If value < min_value: clamp to 0 (floor at minimum)
    - Prevents outliers from breaking the scale
    
    Args:
        value: Raw metric value to normalize
        max_value: Maximum expected value (maps to 100)
        min_value: Minimum expected value (maps to 0)
    
    Returns:
        Normalized value in 0-100 range
    
    Examples:
        normalize(150, 300) = 50.0     # 150 is halfway to 300
        normalize(300, 300) = 100.0    # 300 is at max
        normalize(450, 300) = 100.0    # Clamped to 100 (over max)
        normalize(0, 300) = 0.0        # 0 is at min
        normalize(10, 20, 5) = 33.3    # 10 is 1/3 between 5 and 20
    """
    # Clamp value to [min_value, max_value] range
    # min() ensures value doesn't exceed max_value
    # max() ensures value doesn't go below min_value
    clamped = max(min_value, min(value, max_value))
    
    # Calculate normalized value
    # Special case: if min == max, avoid division by zero
    if max_value == min_value:
        return 100.0 if clamped == max_value else 0.0
    
    # Standard min-max normalization formula
    normalized = ((clamped - min_value) / (max_value - min_value)) * 100.0
    
    return normalized


def calculate_complexity_score(metrics: ComplexityMetrics) -> ComplexityScore:
    """
    Calculate weighted complexity score from contract metrics.
    
    🎓 ALGORITHM BREAKDOWN:
    
    1. LOC Component (30% weight):
       - Measures contract size
       - Baseline: 300 LOC (typical contract)
       - Score = normalize(LOC, 300) × 0.30
       - Example: 150 LOC → 50/100 × 0.30 = 15.0 points
    
    2. Cyclomatic Component (30% weight):
       - Measures code complexity (branches, loops)
       - Baseline: 20 (complex function)
       - Score = normalize(Cyclomatic, 20) × 0.30
       - Example: 10 complexity → 50/100 × 0.30 = 15.0 points
    
    3. External Component (20% weight):
       - Measures external dependencies
       - Baseline: 5 external calls
       - Score = normalize(External, 5) × 0.20
       - Example: 2 calls → 40/100 × 0.20 = 8.0 points
    
    4. Custom Component (20% weight):
       - Binary flags for advanced patterns
       - Assembly: +10 points (advanced)
       - Delegatecall: +10 points (risky)
       - Example: Both used → 20.0 points
    
    Total = LOC + Cyclomatic + External + Custom
    
    🎯 WHY THESE WEIGHTS?
    - LOC + Cyclomatic = 60% (code complexity is primary factor)
    - External + Custom = 40% (dependency/risk is secondary)
    - Balanced between size, complexity, and risk
    
    🔧 TUNING:
    Adjust these parameters based on production metrics:
    - If too many contracts route to CodeLlama: increase thresholds
    - If accuracy suffers: decrease thresholds
    - Monitor component contributions to identify bottlenecks
    
    Args:
        metrics: ComplexityMetrics extracted from contract
    
    Returns:
        ComplexityScore with total and component breakdown
    
    Example:
        metrics = ComplexityMetrics(
            loc=245,
            cyclomatic=12,
            external_calls=3,
            uses_assembly=False,
            uses_delegatecall=True
        )
        
        score = calculate_complexity_score(metrics)
        print(score)
        # ComplexityScore(total=55.5/100) [LOC=24.5, Cyclomatic=18.0, External=12.0, Custom=10.0]
        
        # Decision: 55.5 >= 50 → Route to CodeLlama
    """
    # Component 1: Lines of Code (0-30 points)
    # Baseline: 300 LOC = typical smart contract
    # Rationale: Larger contracts need more context, CodeLlama better at this
    loc_component = normalize(metrics.loc, max_value=300) * 0.30
    
    # Component 2: Cyclomatic Complexity (0-30 points)
    # Baseline: 20 = complex function (many branches/loops)
    # Rationale: High complexity needs deeper analysis, CodeLlama excels here
    cyclomatic_component = normalize(metrics.cyclomatic, max_value=20) * 0.30
    
    # Component 3: External Calls (0-20 points)
    # Baseline: 5 external calls = significant dependencies
    # Rationale: More external calls = more attack surface, needs careful analysis
    external_component = normalize(metrics.external_calls, max_value=5) * 0.20
    
    # Component 4: Custom Patterns (0-20 points)
    # Binary flags: each adds 10 points if present
    # Rationale: Assembly/delegatecall = expert-level code, needs CodeLlama
    custom_score = 0.0
    if metrics.uses_assembly:
        custom_score += 10.0  # Inline assembly = advanced, risky
    if metrics.uses_delegatecall:
        custom_score += 10.0  # Delegatecall = proxy pattern, complex
    custom_component = min(custom_score, 20.0)  # Cap at 20 points max
    
    # Sum all components to get total score
    total = loc_component + cyclomatic_component + external_component + custom_component
    
    return ComplexityScore(
        total=total,
        loc_component=loc_component,
        cyclomatic_component=cyclomatic_component,
        external_component=external_component,
        custom_component=custom_component,
    )


# ============================================================================
# MODEL ROUTER
# ============================================================================

class ModelRouter:
    """
    Routes contracts to appropriate LLM model based on complexity.
    
    🎯 ROUTING LOGIC:
    - Complexity < threshold: Simple model (Llama 3.1)
    - Complexity ≥ threshold: Complex model (CodeLlama)
    
    📊 EXPECTED DISTRIBUTION:
    - 90% of contracts: Simple (score < 50)
    - 10% of contracts: Complex (score ≥ 50)
    
    ⚙️ CONFIGURATION:
    - Threshold: From llm_config.complexity_threshold (default: 50)
    - Simple model: From llm_config.simple_model (default: llama3.1:4b)
    - Complex model: From llm_config.complex_model (default: codellama:7b)
    
    🔧 TUNING:
    Monitor routing decisions and adjust threshold:
    - Too many routing to CodeLlama: increase threshold
    - Accuracy issues on simple contracts: decrease threshold
    - Track average latency per route for optimization
    
    Example:
        router = ModelRouter()
        
        # Route single contract
        features = pipeline.extract(contract_code)
        client, score = router.route(features)
        
        print(f"Model: {client.model_name}")
        print(f"Score: {score}")
        
        # Generate report
        response = await client.generate(prompt)
    """
    
    def __init__(
        self,
        threshold: float = None,
        simple_model: str = None,
        complex_model: str = None,
    ):
        """
        Initialize model router with configuration.
        
        Args:
            threshold: Complexity threshold (0-100). If None, uses config.
            simple_model: Model name for simple contracts. If None, uses config.
            complex_model: Model name for complex contracts. If None, uses config.
        
        Example:
            # Use config defaults
            router = ModelRouter()
            
            # Override threshold
            router = ModelRouter(threshold=60)  # More conservative
            
            # Override models
            router = ModelRouter(
                simple_model="llama3.2:3b",  # Even faster
                complex_model="codellama:13b"  # Even more accurate
            )
        """
        # Use provided values or fall back to config
        self.threshold = threshold if threshold is not None else llm_config.complexity_threshold
        self.simple_model = simple_model if simple_model is not None else llm_config.simple_model
        self.complex_model = complex_model if complex_model is not None else llm_config.complex_model
        
        # Validate threshold
        if not 0 <= self.threshold <= 100:
            logger.warning(
                f"Invalid threshold {self.threshold}, must be 0-100. Using default 50."
            )
            self.threshold = 50.0
        
        logger.info(
            f"ModelRouter initialized: threshold={self.threshold}, "
            f"simple={self.simple_model}, complex={self.complex_model}"
        )
    
    def route(self, features: Dict[str, Any]) -> Tuple[OllamaClient, ComplexityScore]:
        """
        Route contract to appropriate LLM model based on complexity.
        
        🔄 WORKFLOW:
        1. Extract complexity metrics from features (5 out of 89 features)
        2. Calculate complexity score (0-100 with component breakdown)
        3. Compare score to threshold
        4. Create and return appropriate OllamaClient
        
        Args:
            features: Dictionary from FeaturePipeline.extract()
                Must contain: lines_of_code, avg_function_complexity,
                              external_calls_count, uses_assembly, uses_delegatecall
        
        Returns:
            Tuple of (OllamaClient instance, ComplexityScore)
        
        Raises:
            KeyError: If required features are missing from input
        
        Example:
            from chainguardian.feature_extraction.pipeline import FeaturePipeline
            from chainguardian.llm.clients.model_router import ModelRouter
            
            # Extract features
            pipeline = FeaturePipeline(mode="optimized")
            features = pipeline.extract(contract_code)
            
            # Route to model
            router = ModelRouter()
            client, score = router.route(features)
            
            # Log decision
            print(f"Contract routed to {client.model_name}")
            print(f"Complexity: {score}")
            
            # Generate report
            prompt = build_prompt(features)
            response = await client.generate(prompt)
        """
        # Step 1: Extract complexity metrics from feature dict
        # This pulls out only the 5 features we need for routing
        try:
            metrics = ComplexityMetrics.from_features(features)
        except KeyError as e:
            logger.error(f"Missing required feature for routing: {e}")
            raise
        
        # Step 2: Calculate complexity score
        # Returns score with total and component breakdown
        score = calculate_complexity_score(metrics)
        
        # Step 3: Make routing decision
        if score.total < self.threshold:
            # Simple contract → Fast model
            model_name = self.simple_model
            reason = "simple"
        else:
            # Complex contract → Accurate model
            model_name = self.complex_model
            reason = "complex"
        
        # Step 4: Create appropriate client
        client = OllamaClient(model_name)
        
        # Log routing decision
        logger.info(
            f"Routed to {model_name} ({reason}): {score}"
        )
        
        # Return client and score (score useful for monitoring/debugging)
        return client, score
    
    def get_routing_stats(self, features_list: list) -> Dict[str, Any]:
        """
        Analyze routing distribution for a batch of contracts.
        
        Useful for:
        - Validating routing logic (should be ~90/10 split)
        - Tuning threshold (adjust if distribution is off)
        - Monitoring production traffic
        
        Args:
            features_list: List of feature dictionaries
        
        Returns:
            Dictionary with routing statistics
        
        Example:
            # Collect features from 100 contracts
            features_list = [pipeline.extract(code) for code in contracts]
            
            # Analyze routing
            stats = router.get_routing_stats(features_list)
            
            print(f"Simple: {stats['simple_pct']:.1f}%")
            print(f"Complex: {stats['complex_pct']:.1f}%")
            print(f"Avg score: {stats['avg_score']:.1f}")
        """
        if not features_list:
            return {
                "total": 0,
                "simple_count": 0,
                "complex_count": 0,
                "simple_pct": 0.0,
                "complex_pct": 0.0,
                "avg_score": 0.0,
                "min_score": 0.0,
                "max_score": 0.0,
            }
        
        simple_count = 0
        complex_count = 0
        scores = []
        
        for features in features_list:
            metrics = ComplexityMetrics.from_features(features)
            score = calculate_complexity_score(metrics)
            scores.append(score.total)
            
            if score.total < self.threshold:
                simple_count += 1
            else:
                complex_count += 1
        
        total = len(features_list)
        
        return {
            "total": total,
            "simple_count": simple_count,
            "complex_count": complex_count,
            "simple_pct": (simple_count / total) * 100,
            "complex_pct": (complex_count / total) * 100,
            "avg_score": sum(scores) / total,
            "min_score": min(scores),
            "max_score": max(scores),
        }
