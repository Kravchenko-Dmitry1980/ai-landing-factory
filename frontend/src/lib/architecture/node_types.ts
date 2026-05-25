export type NodeTypeId =
  | "frontend"
  | "backend"
  | "ai_service"
  | "llm_gateway"
  | "vector_db"
  | "postgres"
  | "redis"
  | "queue"
  | "orchestrator"
  | "worker"
  | "analytics"
  | "api_gateway"
  | "external_api"
  | "security_layer"
  | "pii_guard"
  | "monitoring"
  | "storage"
  | "generic";

export interface NodeTypeConfig {
  id: NodeTypeId;
  label: string;
  color: string;
  icon?: string;
}

export const NODE_TYPE_CONFIG: Record<string, NodeTypeConfig> = {
  frontend: { id: "frontend", label: "Frontend", color: "#3b82f6" },
  backend: { id: "backend", label: "Backend", color: "#6366f1" },
  ai_service: { id: "ai_service", label: "AI Service", color: "#8b5cf6" },
  llm_gateway: { id: "llm_gateway", label: "LLM Gateway", color: "#a855f7" },
  vector_db: { id: "vector_db", label: "Vector DB", color: "#14b8a6" },
  postgres: { id: "postgres", label: "Postgres", color: "#0ea5e9" },
  redis: { id: "redis", label: "Redis", color: "#ef4444" },
  queue: { id: "queue", label: "Queue", color: "#f59e0b" },
  orchestrator: { id: "orchestrator", label: "Orchestrator", color: "#eab308" },
  worker: { id: "worker", label: "Worker", color: "#84cc16" },
  analytics: { id: "analytics", label: "Analytics", color: "#06b6d4" },
  api_gateway: { id: "api_gateway", label: "API Gateway", color: "#64748b" },
  external_api: { id: "external_api", label: "External API", color: "#78716c" },
  security_layer: { id: "security_layer", label: "Security", color: "#dc2626" },
  pii_guard: { id: "pii_guard", label: "PII Guard", color: "#b91c1c" },
  monitoring: { id: "monitoring", label: "Monitoring", color: "#475569" },
  storage: { id: "storage", label: "Storage", color: "#0284c7" },
  generic: { id: "generic", label: "Component", color: "#94a3b8" },
};

export function resolveNodeType(type: string): NodeTypeConfig {
  return NODE_TYPE_CONFIG[type] ?? NODE_TYPE_CONFIG.generic;
}
