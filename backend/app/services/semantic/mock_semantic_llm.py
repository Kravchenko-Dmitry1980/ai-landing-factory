"""Mock semantic LLM — structured output from safe contract payload."""

import json
from uuid import UUID

from app.services.llm.base import LLMClient
from app.services.semantic.fallback_generator import generate_fallback_semantic
from app.schemas.landing_contract import LandingContract


class MockSemanticLLMClient(LLMClient):
    def __init__(self, contract: LandingContract) -> None:
        self._contract = contract

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema_name: str,
    ) -> dict:
        del system_prompt, user_prompt, schema_name
        semantic = generate_fallback_semantic(self._contract)
        return {
            "project_id": str(self._contract.project_id),
            "domain": semantic.domain.value,
            "layout_preset": semantic.layout_preset,
            "style_profile": semantic.style_profile,
            "narrative": semantic.narrative.model_dump(),
            "sections": [s.model_dump(mode="json") for s in semantic.sections],
            "metadata": {
                **semantic.metadata.model_dump(mode="json"),
                "provider": "mock",
                "llm_enabled": True,
                "fallback_used": False,
            },
        }
