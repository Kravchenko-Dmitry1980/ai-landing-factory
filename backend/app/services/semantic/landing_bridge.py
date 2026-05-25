"""Bridge GeneratedSemanticLanding → GeneratedLanding for Stage D renderer."""

from app.models.domain import utc_now
from app.schemas.generation import GeneratedLanding, LandingBlockContent
from app.schemas.landing_contract import LandingContract, LandingStylePreset
from app.schemas.semantic_generation import GeneratedSemanticLanding, SectionType


def _find_section(semantic: GeneratedSemanticLanding, *types: SectionType):
    type_vals = {t.value for t in types}
    for s in semantic.sections:
        st = s.section_type.value if hasattr(s.section_type, "value") else str(s.section_type)
        if st in type_vals:
            return s
    return None


def semantic_to_landing(
    semantic: GeneratedSemanticLanding,
    contract: LandingContract,
) -> GeneratedLanding:
    """Map semantic sections back to canonical block keys — renderer unchanged."""

    def body_for(*types: SectionType) -> tuple[str, list[str]]:
        sec = _find_section(semantic, *types)
        if not sec:
            return "", []
        bullets = list(sec.bullets)
        if sec.metrics:
            bullets = bullets + [f"[metric] {m}" for m in sec.metrics]
        return sec.narrative or "", bullets

    essence_sec = _find_section(semantic, SectionType.ESSENCE, SectionType.SYSTEM, SectionType.PROBLEM)
    tagline_body = contract.quote or (essence_sec.narrative[:120] if essence_sec else "")
    essence_body, _ = body_for(SectionType.ESSENCE, SectionType.SYSTEM)
    tasks_body, tasks_bullets = body_for(SectionType.MODULES)
    purpose_body, _ = body_for(SectionType.PROBLEM)
    inputs_body, inputs_bullets = body_for(SectionType.ARCHITECTURE, SectionType.INGESTION, SectionType.PIPELINE)
    outputs_body, outputs_bullets = body_for(SectionType.ORCHESTRATION)
    results_body, results_bullets = body_for(SectionType.METRICS, SectionType.DASHBOARDS, SectionType.VALIDATION)
    outlook_body, _ = body_for(SectionType.ROADMAP)
    stack_body, stack_bullets = body_for(SectionType.STACK)
    team_body, team_bullets = body_for(SectionType.TEAM)

    # Fallback to contract blocks if semantic empty
    def from_contract(key: str) -> tuple[str, list[str]]:
        for b in contract.blocks:
            if b.key == key:
                return b.content or "", list(b.bullets)
        return "", []

    if not essence_body:
        essence_body, _ = from_contract("essence")
    if not tasks_bullets:
        _, tasks_bullets = from_contract("tasks")
    if not inputs_bullets:
        _, inputs_bullets = from_contract("inputs")
    if not results_bullets:
        _, results_bullets = from_contract("results")
    if not stack_bullets:
        _, stack_bullets = from_contract("tech_stack")
    if not team_bullets:
        _, team_bullets = from_contract("team")
    if not outlook_body:
        outlook_body, _ = from_contract("outlook")
    if not tagline_body:
        tagline_body, _ = from_contract("tagline")

    style = contract.style
    profile = semantic.style_profile
    if profile == "medical":
        style = LandingStylePreset.CORPORATE
    elif profile == "ai_research":
        style = LandingStylePreset.TECH

    blocks = [
        LandingBlockContent(key="tagline", title="Фраза проекта", body=tagline_body, bullets=[]),
        LandingBlockContent(key="essence", title="Суть проекта", body=essence_body, bullets=[]),
        LandingBlockContent(key="tasks", title="Задачи проекта", body=tasks_body, bullets=tasks_bullets),
        LandingBlockContent(key="purpose", title="Для чего", body=purpose_body, bullets=[]),
        LandingBlockContent(key="inputs", title="Вводные данные", body=inputs_body, bullets=inputs_bullets),
        LandingBlockContent(key="outputs", title="Выходные данные", body=outputs_body, bullets=outputs_bullets),
        LandingBlockContent(key="results", title="Результаты проекта", body=results_body, bullets=results_bullets),
        LandingBlockContent(key="outlook", title="Перспектива развития", body=outlook_body, bullets=[]),
        LandingBlockContent(key="tech_stack", title="Технологический стек", body=stack_body, bullets=stack_bullets),
        LandingBlockContent(key="team", title="Команда проекта", body=team_body, bullets=team_bullets),
    ]

    return GeneratedLanding(
        project_id=semantic.project_id,
        style=style,
        blocks=blocks,
        generated_at=utc_now(),
        prompt_version=semantic.metadata.prompt_version,
    )
