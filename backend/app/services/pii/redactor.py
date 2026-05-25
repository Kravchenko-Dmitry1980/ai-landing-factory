import copy
import logging

from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.schemas.pii import PIIEntity, PIIEntityType, RedactedExtractionResult
from app.services.pii.detector import PIIDetector

logger = logging.getLogger(__name__)

_TYPE_PREFIX: dict[PIIEntityType, str] = {
    PIIEntityType.PERSON_NAME: "PERSON",
    PIIEntityType.EMAIL: "EMAIL",
    PIIEntityType.PHONE: "PHONE",
    PIIEntityType.ADDRESS: "ADDRESS",
    PIIEntityType.URL: "URL",
    PIIEntityType.ORGANIZATION: "ORG",
    PIIEntityType.MEDICAL_DATA: "MEDICAL",
    PIIEntityType.PASSPORT_ID: "ID",
    PIIEntityType.TELEGRAM: "TELEGRAM",
    PIIEntityType.ROLE_PERSON: "ROLE",
}


class PIIRedactor:
    def __init__(self, detector: PIIDetector) -> None:
        self._detector = detector
        self._counters: dict[str, int] = {}

    def redact_extraction(
        self, extraction: ExtractionResult
    ) -> tuple[RedactedExtractionResult, list[PIIEntity], list[str]]:
        self._counters = {}
        all_entities: list[PIIEntity] = []
        all_warnings: list[str] = []
        safe_files: list[FileExtraction] = []

        for f in extraction.files:
            text = f.extracted_text or ""
            entities, warnings = self._detector.detect_text(text, f.filename)
            all_warnings.extend(warnings)
            entities = self._assign_placeholders(entities)
            redacted_text = self._apply_redactions(text, entities)
            safe_file = f.model_copy(update={"extracted_text": redacted_text})
            safe_files.append(safe_file)
            all_entities.extend(entities)

        payload = self._redact_payload(extraction.payload, all_entities)
        mapping = {e.placeholder: e.original for e in all_entities if e.placeholder}
        safe_text = "\n\n".join(
            f"### {sf.filename}\n{sf.extracted_text}" for sf in safe_files if sf.extracted_text
        )

        result = RedactedExtractionResult(
            project_id=extraction.project_id,
            raw_removed=True,
            safe_text=safe_text,
            mapping=mapping,
            files=safe_files,
            payload_snapshot=payload.model_dump(),
        )
        return result, all_entities, sorted(set(all_warnings))

    def _assign_placeholders(self, entities: list[PIIEntity]) -> list[PIIEntity]:
        seen_original: dict[str, str] = {}
        out: list[PIIEntity] = []
        for ent in entities:
            if ent.original in seen_original:
                placeholder = seen_original[ent.original]
            else:
                prefix = _TYPE_PREFIX.get(ent.type, "PII")
                self._counters[prefix] = self._counters.get(prefix, 0) + 1
                placeholder = f"[{prefix}_{self._counters[prefix]}]"
                seen_original[ent.original] = placeholder
            out.append(ent.model_copy(update={"placeholder": placeholder}))
        return out

    @staticmethod
    def _apply_redactions(text: str, entities: list[PIIEntity]) -> str:
        if not entities:
            return text
        ordered = sorted(entities, key=lambda e: e.start, reverse=True)
        result = text
        for ent in ordered:
            if ent.start < 0 or ent.end > len(result):
                continue
            result = result[: ent.start] + ent.placeholder + result[ent.end :]
        return result

    def _redact_payload(
        self,
        payload: ExtractionPayload,
        entities: list[PIIEntity],
    ) -> ExtractionPayload:
        data = copy.deepcopy(payload)
        mapping = {e.original: e.placeholder for e in entities if e.placeholder}

        def scrub(value: str | None) -> str | None:
            if not value:
                return value
            out = value
            for original, placeholder in sorted(mapping.items(), key=lambda x: -len(x[0])):
                out = out.replace(original, placeholder)
            return out

        data.client = scrub(data.client)
        data.essence = scrub(data.essence)
        data.purpose = scrub(data.purpose)
        data.outlook = scrub(data.outlook)
        data.tagline = scrub(data.tagline)
        data.presentation_style = scrub(data.presentation_style)
        data.goals = [scrub(g) or g for g in data.goals]
        data.tasks = [scrub(t) or t for t in data.tasks]
        data.inputs = [scrub(i) or i for i in data.inputs]
        data.outputs = [scrub(o) or o for o in data.outputs]
        data.results = [scrub(r) or r for r in data.results]
        data.tech_stack = [scrub(s) or s for s in data.tech_stack]
        data.team = [scrub(m) or m for m in data.team]
        data.raw_notes = [scrub(n) or n for n in data.raw_notes]
        return data

    def to_extraction_result(self, redacted: RedactedExtractionResult, original: ExtractionResult) -> ExtractionResult:
        """ExtractionResult-shaped object safe for cloud LLM prompts."""
        from app.schemas.extraction import ExtractionPayload

        payload = ExtractionPayload.model_validate(redacted.payload_snapshot)
        files = [FileExtraction.model_validate(f) for f in redacted.files]
        return ExtractionResult(
            project_id=redacted.project_id,
            payload=payload,
            files=files,
            source_file_ids=original.source_file_ids,
            extracted_at=original.extracted_at,
            extractor_version=original.extractor_version,
        )
