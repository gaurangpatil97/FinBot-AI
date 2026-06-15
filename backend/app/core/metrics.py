from prometheus_client import Histogram, Counter

OPENAI_CALL_LATENCY = Histogram(
    "openai_api_call_latency_seconds",
    "Time spent on OpenAI API calls",
    ["model", "purpose"]
)

OPENAI_CALL_COUNT = Counter(
    "openai_api_call_total",
    "Total OpenAI API calls",
    ["model", "purpose", "status"]
)
