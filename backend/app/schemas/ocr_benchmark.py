"""OCR engine benchmark schemas (Stage H.8.4)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class OcrEngineBenchmarkResult(BaseModel):
    engine: str
    available: bool = False
    ok: bool = False
    runtime_ms: int = 0
    raw_chars: int = 0
    normalized_chars: int = 0
    team_section_detected: bool = False
    accepted_team_count: int = 0
    rejected_person_count: int = 0
    known_names_hit_count: int = 0
    accepted_names: list[str] = Field(default_factory=list)
    rejected_preview: list[str] = Field(default_factory=list)
    text_preview: str = ""
    normalized_preview: str = ""
    error_code: str | None = None
    warnings: list[str] = Field(default_factory=list)
    score: float = 0.0


class OcrBenchmarkReport(BaseModel):
    source_file: str
    page_or_slide: int = 0
    image_count: int = 0
    known_names: list[str] = Field(default_factory=list)
    results: list[OcrEngineBenchmarkResult] = Field(default_factory=list)
    best_engine: str | None = None
    reason: str = ""
