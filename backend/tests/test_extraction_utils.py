from app.schemas.extraction import FileExtraction
from app.services.extraction.utils import (
    aggregate_extracted_text,
    build_payload_from_extractions,
)


def test_build_payload_uses_extracted_text_not_filename():
    files = [
        FileExtraction(
            filename="ignored-name.docx",
            file_type="docx",
            extracted_text="Суть проекта: AI Landing Factory\n- Задача первая\n- Задача вторая",
        )
    ]
    payload = build_payload_from_extractions(files, [])
    assert "AI Landing Factory" in (payload.essence or "")
    assert "ignored-name" not in (payload.essence or "")


def test_aggregate_text_joins_files():
    files = [
        FileExtraction(filename="a.txt", file_type="txt", extracted_text="Alpha"),
        FileExtraction(filename="b.txt", file_type="txt", extracted_text="Beta"),
    ]
    combined = aggregate_extracted_text(files)
    assert "Alpha" in combined
    assert "Beta" in combined
