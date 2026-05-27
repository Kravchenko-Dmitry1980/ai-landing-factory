"""Multi-OCR engine benchmark for image-only slides."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from app.schemas.ocr_benchmark import OcrBenchmarkReport, OcrEngineBenchmarkResult
from app.services.evidence.ocr_team_extractor import extract_team_from_ocr_text
from app.services.ocr.engine_registry import create_engine
from app.services.ocr.engines.paddleocr_engine import classify_paddle_error
from app.services.ocr.postprocess.ocr_team_text_normalizer import (
    detect_team_ocr_section,
    normalize_ocr_team_text,
)
from app.services.ocr.postprocess.ocr_text_cleaner import clean_ocr_text
from app.services.ocr.renderers.image_loader import load_image_bytes
from app.services.ocr.renderers.pptx_image_extractor import extract_pptx_images_by_slide

logger = logging.getLogger(__name__)

PREVIEW_LIMIT = 480
ERROR_PENALTY = 50.0


def compute_benchmark_score(result: OcrEngineBenchmarkResult) -> float:
    if not result.ok:
        return -ERROR_PENALTY
    score = (
        result.accepted_team_count * 10
        + result.known_names_hit_count * 5
        + (3 if result.team_section_detected else 0)
        + min(result.raw_chars / 300, 5)
        - result.rejected_person_count * 1
    )
    if result.error_code:
        score -= ERROR_PENALTY
    return score


def count_known_name_hits(
    text: str,
    accepted_names: list[str],
    known_names: list[str],
) -> int:
    if not known_names:
        return 0
    blob = f"{text}\n{' '.join(accepted_names)}".lower()
    hits = 0
    for name in known_names:
        low = name.strip().lower()
        if not low:
            continue
        parts = low.split()
        if all(part in blob for part in parts):
            hits += 1
        elif low in blob:
            hits += 1
    return hits


def _preview(text: str, limit: int = PREVIEW_LIMIT) -> str:
    compact = text[:limit].replace("\n", " | ")
    if len(text) > limit:
        compact += " ..."
    return compact


def _load_slide_images(source: Path, slide: int) -> list[bytes]:
    suffix = source.suffix.lower()
    if suffix == ".pptx":
        return [
            img.image_bytes
            for img in extract_pptx_images_by_slide(source)
            if img.slide_index == slide
        ]
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}:
        loaded = load_image_bytes(source)
        return [loaded.image_bytes] if loaded else []
    return []


def benchmark_engine_on_images(
    engine_name: str,
    images: list[bytes],
    *,
    known_names: list[str] | None = None,
    source_trace: str = "",
) -> OcrEngineBenchmarkResult:
    known = known_names or []
    result = OcrEngineBenchmarkResult(engine=engine_name)
    engine = create_engine(engine_name)
    if engine is None:
        result.warnings.append(f"Unknown engine: {engine_name}")
        result.error_code = "unknown_engine"
        result.score = compute_benchmark_score(result)
        return result

    result.available = engine.is_available()
    if not result.available:
        init_err = getattr(engine, "_init_error", None)
        result.warnings.append(init_err or f"{engine_name} not available")
        result.error_code = f"{engine_name}_unavailable"
        result.score = compute_benchmark_score(result)
        return result

    if not images:
        result.warnings.append("No images to OCR")
        result.error_code = "no_images"
        result.score = compute_benchmark_score(result)
        return result

    started = time.perf_counter()
    raw_parts: list[str] = []
    try:
        for image_bytes in images:
            ocr_result = engine.extract_text(image_bytes)
            if ocr_result.warnings:
                result.warnings.extend(ocr_result.warnings)
            if ocr_result.text.strip():
                raw_parts.append(ocr_result.text)
            for warning in ocr_result.warnings or []:
                low = warning.lower()
                if engine_name == "paddleocr" and (
                    "failed" in low or "convertpirattribute" in low or "onednn" in low
                ):
                    code, _stage, _ = classify_paddle_error(warning, stage="inference")
                    result.error_code = code
        raw_text = "\n\n".join(raw_parts).strip()
        result.raw_chars = len(raw_text)
        result.ok = bool(raw_text)
        if not result.ok and result.error_code:
            result.ok = False
    except Exception as exc:
        result.warnings.append(f"{engine_name} benchmark error: {exc}")
        if engine_name == "paddleocr":
            code, _, _ = classify_paddle_error(str(exc), stage="inference")
            result.error_code = code
        else:
            result.error_code = f"{engine_name}_runtime_error"
        result.ok = False
        raw_text = ""
    finally:
        result.runtime_ms = int((time.perf_counter() - started) * 1000)

    cleaned = clean_ocr_text(raw_text)
    normalized = normalize_ocr_team_text(cleaned)
    result.normalized_chars = len(normalized)
    result.text_preview = _preview(raw_text)
    result.normalized_preview = _preview(normalized)
    result.team_section_detected = detect_team_ocr_section(raw_text) or detect_team_ocr_section(
        normalized
    )

    if normalized or raw_text:
        extraction = extract_team_from_ocr_text(
            normalized or raw_text,
            source_trace=source_trace,
        )
        result.accepted_team_count = len(extraction.members)
        result.accepted_names = [m.name for m in extraction.members]
        result.rejected_person_count = len(extraction.rejected)
        result.rejected_preview = [
            f"{name} ({reason})" for name, _role, reason in extraction.rejected[:10]
        ]
        result.warnings.extend(extraction.warnings)
        result.known_names_hit_count = count_known_name_hits(
            normalized or raw_text,
            result.accepted_names,
            known,
        )

    if not result.ok and not result.error_code:
        result.error_code = f"{engine_name}_empty_or_failed"

    result.score = compute_benchmark_score(result)
    return result


def run_ocr_benchmark(
    source_file: Path,
    *,
    page_or_slide: int = 0,
    engines: list[str],
    known_names: list[str] | None = None,
) -> OcrBenchmarkReport:
    images = _load_slide_images(source_file, page_or_slide)
    known = known_names or []
    trace = f"{source_file.name}#slide-{page_or_slide}"

    results: list[OcrEngineBenchmarkResult] = []
    for engine_name in engines:
        logger.info("Benchmarking engine %s on %s slide %s", engine_name, source_file, page_or_slide)
        results.append(
            benchmark_engine_on_images(
                engine_name,
                images,
                known_names=known,
                source_trace=trace,
            )
        )

    best_engine, reason = select_best_engine(results)
    return OcrBenchmarkReport(
        source_file=str(source_file),
        page_or_slide=page_or_slide,
        image_count=len(images),
        known_names=known,
        results=results,
        best_engine=best_engine,
        reason=reason,
    )


def select_best_engine(
    results: list[OcrEngineBenchmarkResult],
) -> tuple[str | None, str]:
    ok_results = [r for r in results if r.ok]
    if not ok_results:
        return None, "All engines failed or returned empty OCR text."

    ranked = sorted(
        ok_results,
        key=lambda r: (r.score, r.accepted_team_count, r.known_names_hit_count, r.raw_chars),
        reverse=True,
    )
    best = ranked[0]
    reason = (
        f"score={best.score:.1f}, accepted_team={best.accepted_team_count}, "
        f"known_hits={best.known_names_hit_count}, chars={best.raw_chars}"
    )
    return best.engine, reason


def format_benchmark_table(report: OcrBenchmarkReport) -> str:
    header = (
        "engine | ok | chars | team_section | accepted | known_hits | runtime_ms | error"
    )
    lines = [header, "-" * len(header)]
    for r in report.results:
        err = r.error_code or "-"
        lines.append(
            f"{r.engine} | {r.ok} | {r.raw_chars} | {r.team_section_detected} | "
            f"{r.accepted_team_count} | {r.known_names_hit_count} | {r.runtime_ms} | {err}"
        )
    lines.append("")
    lines.append(f"best_engine: {report.best_engine or '-'}")
    lines.append(f"reason: {report.reason}")
    return "\n".join(lines)
