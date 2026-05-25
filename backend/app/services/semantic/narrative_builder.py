"""Engineering-first narrative arc from contract blocks."""

from app.schemas.landing_contract import LandingContract
from app.schemas.semantic_generation import SemanticNarrative


def _block_text(contract: LandingContract, key: str) -> tuple[str, list[str]]:
    for b in contract.blocks:
        if b.key == key:
            return b.content or "", list(b.bullets)
    return "", []


def build_narrative(contract: LandingContract) -> SemanticNarrative:
    essence, _ = _block_text(contract, "essence")
    purpose, _ = _block_text(contract, "purpose")
    _, tasks = _block_text(contract, "tasks")
    _, inputs = _block_text(contract, "inputs")
    _, outputs = _block_text(contract, "outputs")
    _, results = _block_text(contract, "results")
    outlook, _ = _block_text(contract, "outlook")

    problem = purpose or essence or (contract.lead or "")
    system = essence or purpose or ""
    architecture = "\n".join(
        x for x in [
            f"Inputs: {', '.join(inputs[:4])}" if inputs else "",
            f"Outputs: {', '.join(outputs[:4])}" if outputs else "",
        ] if x
    )
    modules = "; ".join(tasks[:6]) if tasks else ""
    metrics = "; ".join(results[:6]) if results else ""
    roadmap = outlook or ""

    return SemanticNarrative(
        problem=problem[:800],
        system=system[:800],
        architecture=architecture[:800],
        modules=modules[:600],
        metrics=metrics[:600],
        roadmap=roadmap[:600],
        tone="engineering-first",
    )
