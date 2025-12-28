"""
LLM-specific Prometheus metrics for ChainGuardian AI.
"""
from prometheus_client import Counter, Histogram, Gauge

# Counters
llm_requests_total = Counter(
    'chainguardian_llm_requests_total',
    'Total number of LLM requests made',
    ['model', 'endpoint', 'status']
)

llm_tokens_total = Counter(
    'chainguardian_llm_tokens_total',
    'Total number of tokens processed by LLM',
    ['model', 'direction']  # direction: input/output
)

llm_errors_total = Counter(
    'chainguardian_llm_errors_total',
    'Total number of LLM errors',
    ['model', 'error_type']
)

llm_cache_hits_total = Counter(
    'chainguardian_llm_cache_hits_total',
    'Total number of LLM cache hits',
    ['model', 'cache_type']
)

rate_limit_exceeded_total = Counter(
    'chainguardian_rate_limit_exceeded_total',
    'Total number of rate limit exceeded events',
    ['endpoint', 'ip_address']
)

# Histograms
llm_latency_seconds = Histogram(
    'chainguardian_llm_latency_seconds',
    'LLM response latency in seconds',
    ['model'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

# Gauges
llm_cost_estimated = Gauge(
    'chainguardian_llm_cost_estimated',
    'Estimated LLM cost in USD',
    ['model', 'provider']
)

llm_context_length = Gauge(
    'chainguardian_llm_context_length',
    'Current LLM context length (tokens)',
    ['model']
)

llm_model_version = Gauge(
    'chainguardian_llm_model_version',
    'LLM model version',
    ['model', 'version']
)

active_llm_requests = Gauge(
    'chainguardian_active_llm_requests',
    'Number of active LLM requests'
)

llm_gpu_memory_usage = Gauge(
    'chainguardian_llm_gpu_memory_usage_bytes',
    'GPU memory usage by LLM',
    ['gpu_id', 'model']
)

# Cost estimation function
def estimate_llm_cost(input_tokens: int, output_tokens: int, model: str = "llama3.1") -> float:
    """Estimate cost for LLM usage in USD."""
    # Current cost estimates (per 1M tokens)
    cost_rates = {
        "llama3.1": {"input": 0.5, "output": 0.75},  # $0.5/M input, $0.75/M output
        "mistral": {"input": 0.25, "output": 0.25},
        "codellama": {"input": 0.75, "output": 1.0},
        "phi3": {"input": 0.1, "output": 0.1},
    }
    
    rates = cost_rates.get(model, cost_rates["llama3.1"])
    
    cost = (input_tokens * rates["input"] / 1_000_000) + \
           (output_tokens * rates["output"] / 1_000_000)
    
    return round(cost, 6)  # Round to microdollars