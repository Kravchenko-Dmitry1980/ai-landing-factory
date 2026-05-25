# Domain Intelligence & Knowledge Graph (Stage G)

## Purpose

Stage G adds **domain-architectural understanding** before semantic generation (E) and topology (F). It is deterministic-first, PII-safe, and stored as JSON — no graph DB.

## Pipeline

```
LandingContract
  → DomainIntelligenceEngine.analyze()
  → ProjectKnowledgeGraph (JSON)
  → SemanticGenerationEngine (enriched narrative)
  → ArchitectureTopologyEngine (KG nodes/edges + pattern hints)
  → Renderer
```

## Configuration

| Env | Default | Description |
|-----|---------|-------------|
| `DOMAIN_INTELLIGENCE_ENABLED` | `true` | Master switch |
| `DOMAIN_USE_LLM` | `false` | Optional LLM refinement (PII-safe payload only) |
| `DOMAIN_MIN_CONFIDENCE` | `0.45` | Minimum domain confidence threshold |
| `DOMAIN_GRAPH_MAX_ENTITIES` | `120` | Cap entity count |
| `DOMAIN_GRAPH_MAX_RELATIONS` | `240` | Cap relation count |

`LOCAL_ONLY` privacy mode forces `DOMAIN_USE_LLM=false`.

## Storage

- `data/domain_reports/{project_id}.domain.json`
- `data/knowledge_graphs/{project_id}.kg.json`

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/projects/{id}/domain-analyze` | Run / refresh analysis |
| GET | `/api/v1/projects/{id}/domain-report` | Full report |
| GET | `/api/v1/projects/{id}/knowledge-graph` | Graph only |

`/generate` automatically runs domain analysis when report is missing or stale (contract updated after report).

## Modules

```
backend/app/services/domain/
  domain_classifier.py      # Hybrid keyword classifier (13 domains)
  archetype_detector.py     # System archetypes (Copilot, RAG, DSS, …)
  pattern_detector.py       # Architecture patterns with evidence
  entity_extractor.py       # Grounded entities from contract blocks
  relation_builder.py       # Entity relations (uses, depends_on, …)
  knowledge_graph_builder.py
  domain_validator.py       # Hallucination + PII guard
  engine.py                 # Orchestrator
```

## Hallucination Guard

Entities must be grounded in contract text. Team members, technologies, metrics, and integrations not present in the contract are rejected or marked `inferred=true` with low confidence.

## Frontend

- Editor Advanced: `DomainDebugPanel` + refresh button
- Preview: `?domain_debug=1` overlay

## Smoke Test

```powershell
cd backend
python scripts/smoke_domain.py
pytest tests/test_domain_classifier_stage_g.py tests/test_archetype_detector.py tests/test_pattern_detector.py tests/test_knowledge_graph_builder.py tests/test_domain_integration_generate.py -q
```

## Limitations

- No Neo4j / vector DB
- LLM refinement stub (deterministic path is production default)
- Entity extraction is keyword/token based, not NER
- Cross-project ontology not supported

## Next Safe Step

- Wire `DOMAIN_USE_LLM` refinement with safe payload + validation
- Expose pattern → diagram_type rationale in architecture section UI
- Domain-specific section planner overrides per `PrimaryDomain`
