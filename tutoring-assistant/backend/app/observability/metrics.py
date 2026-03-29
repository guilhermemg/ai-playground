from prometheus_client import Counter, Histogram, Gauge


QUESTIONNAIRE_EVAL_DURATION = Histogram(
    "questionnaire_evaluation_duration_seconds",
    "Time spent evaluating a questionnaire",
    buckets=[1, 5, 10, 30, 60, 120, 300],
)

AGENT_INVOCATIONS = Counter(
    "agent_invocations_total",
    "Total number of agent invocations",
    ["agent_name", "domain"],
)

LLM_TOKENS_USED = Counter(
    "llm_tokens_used_total",
    "Total LLM tokens consumed",
    ["model", "type"],
)

RAG_RETRIEVAL_LATENCY = Histogram(
    "rag_retrieval_latency_seconds",
    "Time spent retrieving documents from Pinecone",
    buckets=[0.1, 0.5, 1, 2, 5],
)

ROUTING_DECISIONS = Counter(
    "routing_decisions_total",
    "Total routing decisions made",
    ["selected_domain"],
)

ACTIVE_AGENTS = Gauge(
    "active_agents_count",
    "Number of currently active agents",
)

DOCUMENTS_COUNT = Gauge(
    "documents_count",
    "Number of documents in the system",
)
