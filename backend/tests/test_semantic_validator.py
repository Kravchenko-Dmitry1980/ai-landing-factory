from app.services.semantic.semantic_validator import validate_semantic_llm_output
from uuid import uuid4


def test_confidence_clamped():
    raw = {
        "project_id": str(uuid4()),
        "domain": "general",
        "sections": [
            {
                "section_type": "essence",
                "title": "T",
                "narrative": "N",
                "confidence": {"overall": 1.5, "factual_grounding": -0.2},
            }
        ],
        "metadata": {},
    }
    out = validate_semantic_llm_output(raw)
    assert out.sections[0].confidence.overall == 1.0
    assert out.sections[0].confidence.factual_grounding == 0.0
