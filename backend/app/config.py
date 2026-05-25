from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Dev-only: allow local Next.js on any port in the start_dev.ps1 range (3000-3050).
DEV_FRONTEND_PORT_START = 3000
DEV_FRONTEND_PORT_END = 3050


def build_dev_cors_origins(
    start: int = DEV_FRONTEND_PORT_START,
    end: int = DEV_FRONTEND_PORT_END,
) -> list[str]:
    """Localhost origins for browser frontend during development."""
    origins: list[str] = []
    for port in range(start, end + 1):
        origins.append(f"http://localhost:{port}")
        origins.append(f"http://127.0.0.1:{port}")
    return origins


DEFAULT_CORS_ORIGINS: list[str] = build_dev_cors_origins()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Landing Factory"
    api_prefix: str = "/api/v1"
    # Stored as comma-separated string so env vars work without JSON encoding.
    backend_cors_origins_env: str = Field(
        default="",
        validation_alias="BACKEND_CORS_ORIGINS",
    )

    @property
    def cors_origins(self) -> list[str]:
        raw = self.backend_cors_origins_env
        if raw is None or not str(raw).strip():
            return list(DEFAULT_CORS_ORIGINS)
        return [origin.strip() for origin in str(raw).split(",") if origin.strip()]

    @field_validator("backend_cors_origins_env", mode="before")
    @classmethod
    def normalize_cors_env(cls, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, list):
            return ",".join(str(item).strip() for item in value if str(item).strip())
        return str(value)

    base_dir: Path = Path(__file__).resolve().parents[1]
    data_dir: Path = base_dir / "data"
    uploads_dir: Path = data_dir / "uploads"
    contracts_dir: Path = data_dir / "contracts"
    extractions_dir: Path = data_dir / "extractions"

    llm_enabled: bool = False
    llm_provider: str = "mock"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    llm_max_chars_per_file: int = 3000
    llm_max_total_chars: int = 12000

    # Semantic generation (Stage E)
    semantic_generation_enabled: bool = True
    semantic_use_llm: bool = False

    # Domain intelligence (Stage G)
    domain_intelligence_enabled: bool = True
    domain_use_llm: bool = False
    domain_min_confidence: float = 0.45
    domain_graph_max_entities: int = 120
    domain_graph_max_relations: int = 240

    # PII / privacy (Stage C.5)
    privacy_mode: str = "hybrid_safe"
    enable_pii_detection: bool = True
    enable_rehydration: bool = True
    pii_mask_names: bool = True
    pii_mask_emails: bool = True
    pii_mask_phones: bool = True
    pii_audit_log_originals: bool = False

    # PII hardening (Stage C.6)
    pii_report_ttl_hours: int = 72
    pii_cleanup_enabled: bool = True
    pii_encrypt_reports: bool = False
    pii_encryption_key: str | None = None

    @property
    def pii_reports_dir(self) -> Path:
        return self.data_dir / "pii_reports"

    @property
    def pii_safe_payloads_dir(self) -> Path:
        return self.data_dir / "pii_safe_payloads"

    @property
    def domain_reports_dir(self) -> Path:
        return self.data_dir / "domain_reports"

    @property
    def knowledge_graphs_dir(self) -> Path:
        return self.data_dir / "knowledge_graphs"

    # OCR layer (Stage H.8)
    ocr_enabled: bool = False
    ocr_engine: str = "paddleocr"
    ocr_fallback_engine: str = "tesseract"
    ocr_dpi: int = 250
    ocr_max_pages: int = 30
    ocr_max_slides: int = 40
    ocr_min_text_chars: int = 40
    ocr_cache_enabled: bool = True

    @property
    def ocr_cache_dir(self) -> Path:
        return self.data_dir / "ocr_cache"


settings = Settings()
