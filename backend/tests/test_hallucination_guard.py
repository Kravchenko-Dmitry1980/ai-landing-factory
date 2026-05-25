from app.schemas.landing_contract import LandingBlock, LandingContract, LandingStylePreset
from app.models.domain import utc_now
from app.services.semantic.fallback_generator import generate_fallback_semantic
from app.services.semantic.hallucination_guard import guard_hallucinations
from uuid import uuid4


def _contract():
    return LandingContract(
        project_id=uuid4(),
        style=LandingStylePreset.MINIMAL,
        blocks=[
            LandingBlock(key="results", title="R", content="", bullets=["Delivered MVP"]),
            LandingBlock(key="team", title="T", content="", bullets=["Alice Dev"]),
        ],
        updated_at=utc_now(),
    )


def test_fabricated_metric_stripped():
    c = _contract()
    sem = generate_fallback_semantic(c)
    sem.sections[0].metrics = ["123456789 users"]
    rep = guard_hallucinations(sem, c)
    assert any("Unverified metric" in w for w in rep.warnings)


def test_grounded_metric_kept():
    c = _contract()
    c.blocks[0].bullets = ["Improvement 42% in cycle time"]
    sem = generate_fallback_semantic(c)
    sem.sections[0].metrics = ["42% improvement"]
    rep = guard_hallucinations(sem, c)
    assert rep.adjusted_sections[0].metrics == ["42% improvement"]
