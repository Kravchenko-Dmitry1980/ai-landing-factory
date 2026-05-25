"""Normalize tech labels to canonical node types."""

import re

from app.schemas.architecture import NodeType

_KEYWORD_MAP: list[tuple[re.Pattern[str], NodeType]] = [
    (re.compile(r"\breact|next\.?js|vue|angular|frontend|ui\b", re.I), NodeType.FRONTEND),
    (re.compile(r"\bfastapi|django|flask|express|backend|api server\b", re.I), NodeType.BACKEND),
    (re.compile(r"\bopenai|llm|gpt|claude|langchain|ai service\b", re.I), NodeType.AI_SERVICE),
    (re.compile(r"\bllm gateway|model gateway|inference gateway\b", re.I), NodeType.LLM_GATEWAY),
    (re.compile(r"\bvector|pinecone|weaviate|qdrant|chromadb|pgvector\b", re.I), NodeType.VECTOR_DB),
    (re.compile(r"\bpostgres|postgresql|mysql|sqlite\b", re.I), NodeType.POSTGRES),
    (re.compile(r"\bredis|memcached\b", re.I), NodeType.REDIS),
    (re.compile(r"\bqueue|kafka|rabbitmq|celery|sqs\b", re.I), NodeType.QUEUE),
    (re.compile(r"\borchestrat|airflow|prefect|dag\b", re.I), NodeType.ORCHESTRATOR),
    (re.compile(r"\bworker|consumer|processor\b", re.I), NodeType.WORKER),
    (re.compile(r"\banalytics|grafana|metabase|dashboard\b", re.I), NodeType.ANALYTICS),
    (re.compile(r"\bapi gateway|kong|nginx|traefik\b", re.I), NodeType.API_GATEWAY),
    (re.compile(r"\bexternal api|third.?party|webhook\b", re.I), NodeType.EXTERNAL_API),
    (re.compile(r"\bsecurity|auth|oauth|jwt|iam\b", re.I), NodeType.SECURITY_LAYER),
    (re.compile(r"\bpii|privacy|redact|guard\b", re.I), NodeType.PII_GUARD),
    (re.compile(r"\bmonitor|prometheus|sentry|observability\b", re.I), NodeType.MONITORING),
    (re.compile(r"\bs3|storage|blob|minio|file store\b", re.I), NodeType.STORAGE),
]


def slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text.lower())
    s = re.sub(r"[\s_]+", "-", s.strip())
    return s[:48] or "node"


def normalize_node_type(label: str) -> NodeType:
    for pattern, node_type in _KEYWORD_MAP:
        if pattern.search(label):
            return node_type
    return NodeType.GENERIC


def normalize_label(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())[:80]
