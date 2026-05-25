import logging
import re
from typing import Any

from app.schemas.landing import LLMContractOutput
from app.schemas.landing_contract import LandingContract

logger = logging.getLogger(__name__)

_PLACEHOLDER_RE = re.compile(r"\[(?:PERSON|EMAIL|PHONE|ADDRESS|URL|ORG|MEDICAL|ID|TELEGRAM|ROLE)_\d+\]")


class PIIRehydrator:
    """Restore placeholders in LLM/heuristic outputs using server-side mapping."""

    def __init__(self, mapping: dict[str, str]) -> None:
        self._mapping = mapping

    def rehydrate_llm_output(self, output: LLMContractOutput) -> LLMContractOutput:
        data = output.model_dump()
        restored = self._walk(data)
        return LLMContractOutput.model_validate(restored)

    def rehydrate_contract(self, contract: LandingContract) -> LandingContract:
        data = contract.model_dump(mode="json")
        restored = self._walk(data)
        return LandingContract.model_validate(restored)

    def _walk(self, obj: Any) -> Any:
        if isinstance(obj, str):
            return self._replace_in_string(obj)
        if isinstance(obj, list):
            return [self._walk(item) for item in obj]
        if isinstance(obj, dict):
            return {k: self._walk(v) for k, v in obj.items()}
        return obj

    def _replace_in_string(self, text: str) -> str:
        if not text or not self._mapping:
            return text

        def repl(match: re.Match[str]) -> str:
            key = match.group(0)
            return self._mapping.get(key, key)

        return _PLACEHOLDER_RE.sub(repl, text)
