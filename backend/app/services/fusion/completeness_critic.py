"""Post-fusion completeness evaluation."""

from __future__ import annotations

from app.schemas.fidelity import ContractCompletenessReport
from app.schemas.landing_contract import LandingContract
from app.services.contract_fidelity.completeness_gate import ContractCompletenessGate


class CompletenessCritic:
    """Evaluate fused contract completeness and weak fields."""

    def __init__(self) -> None:
        self._gate = ContractCompletenessGate()

    def evaluate(self, contract: LandingContract) -> ContractCompletenessReport:
        return self._gate.evaluate(contract)

    def missing_and_weak(
        self, report: ContractCompletenessReport
    ) -> tuple[list[str], list[str]]:
        return list(report.missing_fields), list(report.weak_fields)
