"""VLM adapter interface — provider abstraction without runtime model."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.schemas.vlm import VlmStructuredExtraction, VlmTaskType
from app.services.vlm.vlm_contracts import VlmExtractionContext


@runtime_checkable
class VlmAdapter(Protocol):
    """Contract for VLM providers (stub, local, ollama, vllm, cloud)."""

    provider: str

    def is_available(self) -> bool:
        """Return True when adapter can serve requests."""
        ...

    def extract(
        self,
        image_bytes: bytes,
        task_type: VlmTaskType,
        context: VlmExtractionContext,
    ) -> VlmStructuredExtraction:
        """Extract structured field candidates from a visual block."""
        ...
