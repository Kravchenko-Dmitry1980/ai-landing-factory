from __future__ import annotations

from app.schemas.landing_contract import LandingBlock
from app.services.export.styled_html_exporter import StyledHtmlExporter
from tests.fixtures.export_contract_fixture import make_wow_indlab_fixture


def _block(key: str, content: str = "", bullets: list[str] | None = None) -> LandingBlock:
    return LandingBlock(key=key, title=key, content=content, bullets=bullets or [])


def test_io_section_uses_text_when_editor_filled_no_bullets() -> None:
    exporter = StyledHtmlExporter(None)
    html = exporter._io_section(
        {
            "inputs": _block("inputs", content="Видео с камер над кассой."),
            "outputs": _block("outputs", bullets=["Инцидент с отметкой времени"]),
        }
    )
    assert "Видео с камер над кассой." in html
    assert "Инцидент с отметкой времени" in html


def test_io_section_stays_hidden_when_both_blocks_are_empty() -> None:
    exporter = StyledHtmlExporter(None)
    assert exporter._io_section({"inputs": _block("inputs"), "outputs": _block("outputs")}) == ""


def test_empty_bullet_does_not_hide_the_text() -> None:
    exporter = StyledHtmlExporter(None)
    html = exporter._list_section(_block("results", content="Точность 95%", bullets=[""]), "results", "Результаты")
    assert "Точность 95%" in html


def test_list_section_keeps_text_above_bullets() -> None:
    exporter = StyledHtmlExporter(None)
    html = exporter._list_section(_block("tasks", content="Вступление", bullets=["Пункт"]), "tasks", "Задачи")
    assert html.index("Вступление") < html.index("Пункт")


def test_essence_shows_bullets_too() -> None:
    exporter = StyledHtmlExporter(None)
    html = exporter._block_section(_block("essence", bullets=["Только пункт"]), "essence")
    assert "Только пункт" in html


def test_export_has_no_service_banner_or_footer() -> None:
    _, contract, landing = make_wow_indlab_fixture()
    if contract.fidelity and contract.fidelity.completeness:
        contract.fidelity.completeness.export_incomplete = True
    exporter = StyledHtmlExporter(None)
    from app.schemas.style_config import LandingStyleConfigModel
    from app.services.export.export_theme import ExportTheme

    html = exporter._render_from_contract(
        contract, landing, ExportTheme.from_profile(LandingStyleConfigModel().profile), LandingStyleConfigModel()
    )
    assert "Export incomplete" not in html
    assert "AI Landing Factory ·" not in html
