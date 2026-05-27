"""OCR runtime diagnostics schemas (Stage H.8.2)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EngineRuntimeStatus(BaseModel):
    package_installed: bool = False
    binary_available: bool | None = None
    init_ok: bool = False
    model_ready: bool | None = None
    inference_ok: bool | None = None
    test_image_ok: bool | None = None
    test_image_chars: int | None = None
    failure_stage: (
        str | None
    ) = None  # import | dependency | init | model_download | inference | unknown
    error_code: str | None = None
    recommended_action: str | None = None
    version: str | None = None
    error: str | None = None
    warnings: list[str] = Field(default_factory=list)


class OcrRuntimeStatus(BaseModel):
    ocr_enabled: bool = False
    configured_engine: str = "paddleocr"
    fallback_engine: str | None = "tesseract"
    paddleocr: EngineRuntimeStatus = Field(default_factory=EngineRuntimeStatus)
    tesseract: EngineRuntimeStatus = Field(default_factory=EngineRuntimeStatus)
    easyocr: EngineRuntimeStatus = Field(default_factory=EngineRuntimeStatus)
    surya: EngineRuntimeStatus = Field(default_factory=EngineRuntimeStatus)
    pillow_available: bool = False
    pymupdf_available: bool = False
    cache_enabled: bool = True
    cache_dir: str = ""
    cache_dir_writable: bool = False
    test_image_ok: bool | None = None
    test_image_chars: int | None = None
    indlab_slide25_ready: bool | None = None
    indlab_slide25_note: str | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    ready: bool = False
    recommended_action: str = ""
