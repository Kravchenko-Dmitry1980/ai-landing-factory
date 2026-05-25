from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema_name: str,
    ) -> dict:
        """Return parsed JSON object from LLM."""
