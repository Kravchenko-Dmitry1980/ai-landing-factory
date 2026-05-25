from app.schemas.landing_contract import LandingBlock, LandingContract, LandingStylePreset
from app.models.domain import utc_now
from app.services.semantic.domain_classifier import classify_domain, DomainProfile
from uuid import uuid4


def _c(text: str) -> LandingContract:
    return LandingContract(
        project_id=uuid4(),
        style=LandingStylePreset.MINIMAL,
        blocks=[LandingBlock(key="essence", title="E", content=text, bullets=[])],
        updated_at=utc_now(),
    )


def test_analytics_domain():
    r = classify_domain(_c("Analytics dashboard with KPI metrics and ingestion pipeline"))
    assert r.domain == DomainProfile.ANALYTICS


def test_cybersecurity_domain():
    r = classify_domain(_c("Cybersecurity compliance audit and security architecture"))
    assert r.domain == DomainProfile.CYBERSECURITY


def test_general_when_empty():
    r = classify_domain(
        LandingContract(
            project_id=uuid4(),
            style=LandingStylePreset.MINIMAL,
            blocks=[],
            updated_at=utc_now(),
        )
    )
    assert r.domain == DomainProfile.GENERAL
