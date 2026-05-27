"""Styled static HTML export mirroring renderer section structure."""

from __future__ import annotations

from html import escape
from uuid import UUID

from app.repositories.contract_repository import ContractRepository
from app.schemas.fidelity import FidelityMetadata, LandingModule, TeamMember
from app.schemas.generation import GeneratedLanding
from app.schemas.landing_contract import LandingContract, LandingBlock
from app.schemas.style_config import LandingStyleConfigModel
from app.services.export.export_interactive_css import (
    CSS_INTERACTIVE,
    LONG_LIST_ITEMS,
    LONG_TEXT_CHARS,
    SECTION_NAV_ITEMS,
)
from app.schemas.style_config import effective_style_config
from app.services.export.export_theme import ExportTheme
from app.services.export.export_theme_css import build_export_css
from app.services.export.theme_tokens import normalize_theme_tokens
from app.services.export.export_tagline import resolve_tagline
from app.services.export.html_bullet_utils import (
    MAX_TEAM_BULLET_CHARS,
    format_more_count,
    limit_bullets,
    normalize_bullet,
    truncate_sentence_safe,
)
from app.services.export.html_exporter import HtmlExporter
from app.services.contract_fidelity.team_candidate_validator import filter_team_members

class StyledHtmlExporter:
    """Export contract + landing as styled responsive HTML."""

    def __init__(self, repository: ContractRepository) -> None:
        self._repo = repository
        self._legacy = HtmlExporter(repository)

    async def to_html(
        self,
        project_id: UUID,
        theme: ExportTheme | None = None,
        style_config: LandingStyleConfigModel | None = None,
    ) -> str:
        contract = await self._repo.get_contract(project_id)
        landing = await self._repo.get_landing(project_id)

        if not contract and not landing:
            return "<html><body><p>Landing not generated yet.</p></body></html>"

        if contract:
            merged_style = (
                style_config
                or contract.style_config
                or effective_style_config(contract)
            )
            resolved_theme = ExportTheme.from_profile(merged_style.profile)
            if theme is not None:
                resolved_theme = theme
            return self._render_from_contract(
                contract, landing, resolved_theme, merged_style
            )

        return await self._legacy.to_html(project_id)

    def _render_from_contract(
        self,
        contract: LandingContract,
        landing: GeneratedLanding | None,
        theme: ExportTheme,
        style_config: LandingStyleConfigModel,
    ) -> str:
        blocks = {b.key: b for b in contract.blocks}
        fidelity: FidelityMetadata | None = contract.fidelity

        incomplete = ""
        if fidelity and fidelity.completeness and fidelity.completeness.export_incomplete:
            score = fidelity.completeness.score
            missing = ", ".join(fidelity.completeness.missing_fields[:8])
            incomplete = (
                f'<div class="incomplete-banner">'
                f"⚠ Export incomplete (score {score}/100). Missing: {escape(missing)}"
                f"</div>"
            )

        hero = self._hero(contract, blocks, style_config)
        modules = self._modules_section(fidelity)
        essence = self._block_section(blocks.get("essence"), "essence")
        tasks = self._list_section(blocks.get("tasks"), "tasks", "Задачи проекта")
        purpose = self._list_section(blocks.get("purpose"), "purpose", "Для чего")
        io = self._io_section(blocks)
        results = self._list_section(blocks.get("results"), "results", "Результаты проекта")
        stack = self._stack_section(blocks.get("tech_stack"), fidelity)
        team = self._team_section(blocks.get("team"), fidelity, theme)
        outlook = self._list_section(blocks.get("outlook"), "outlook", "Перспектива развития")
        footer = (
            f'<footer><p>AI Landing Factory · {escape(contract.title or "Проект")} '
            f"· v{contract.version}</p></footer>"
        )

        present_ids = {
            sid
            for sid, html in (
                ("modules", modules),
                ("essence", essence),
                ("tasks", tasks),
                ("stack", stack),
                ("team", team),
                ("outlook", outlook),
            )
            if html
        }
        nav = self._section_nav(present_ids)

        title_fallback = contract.title or "Проект"
        title = escape(title_fallback)
        body = (
            f"{incomplete}{hero}{nav}{modules}{essence}{tasks}{purpose}{io}"
            f"{results}{stack}{team}{outlook}{footer}"
        )
        css = build_export_css(theme, style_config) + CSS_INTERACTIVE
        body_class = theme.body_class()

        return (
            f"<!DOCTYPE html><html lang='ru'><head>"
            f"<meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width, initial-scale=1'>"
            f"<title>{title}</title><style>{css}</style></head>"
            f"<body class='{body_class}'><div class='container'>{body}</div></body></html>"
        )

    @staticmethod
    def _section_nav(present_ids: set[str]) -> str:
        links = []
        for section_id, label in SECTION_NAV_ITEMS:
            if section_id in present_ids:
                links.append(
                    f"<a href='#{section_id}'>{escape(label)}</a>"
                )
        if not links:
            return ""
        return (
            f"<nav class='section-nav alf-section-nav' "
            f"aria-label='Навигация по разделам'>{''.join(links)}</nav>"
        )

    @staticmethod
    def _hero_class(style_config: LandingStyleConfigModel | None) -> str:
        if not style_config:
            return ""
        tokens = normalize_theme_tokens(style_config)
        mode = tokens.heroMode
        if mode == "gradient":
            return " hero--gradient"
        if mode == "future_3d":
            return " hero--future-3d"
        if mode in ("bold",):
            return " hero--cards"
        return ""

    def _hero(
        self,
        contract: LandingContract,
        blocks: dict[str, LandingBlock],
        style_config: LandingStyleConfigModel | None = None,
    ) -> str:
        tagline_block = blocks.get("tagline")
        essence_block = blocks.get("essence")
        tagline_raw = tagline_block.content if tagline_block else ""
        essence_raw = essence_block.content if essence_block else ""
        domain = self._infer_domain(contract, essence_raw)
        tagline_text = resolve_tagline(
            contract.title,
            tagline_raw,
            essence_raw,
            domain,
        )
        meta_parts = []
        if contract.client:
            meta_parts.append(f"<span>Заказчик: {escape(contract.client[:120])}</span>")
        if contract.timeline:
            meta_parts.append(f"<span>Период: {escape(contract.timeline)}</span>")
        if contract.lead:
            meta_parts.append(f"<span>Тимлид: {escape(contract.lead)}</span>")
        meta_html = "".join(meta_parts)
        hero_mode = self._hero_class(style_config)
        return (
            f"<header class='hero{hero_mode}' id='hero'>"
            f"<h1>{escape(contract.title or 'Проект')}</h1>"
            f"<div class='meta'>{meta_html}</div>"
            f"<p class='tagline'>{escape(tagline_text)}</p>"
            f"</header>"
        )

    @staticmethod
    def _infer_domain(contract: LandingContract, essence: str) -> str | None:
        presentation = (contract.presentation_style or "").strip().lower()
        if presentation in ("medical", "medical_ai"):
            return "medical_ai"
        if presentation in ("education", "education_ai"):
            return "education_ai"
        if presentation == "analytics":
            return "analytics"
        title = (contract.title or "").casefold()
        if "эндокринолог" in title:
            return "medical_ai"
        essence_lower = essence.casefold()
        if "медиц" in essence_lower or "клинич" in essence_lower or "врач" in essence_lower:
            return "medical_ai"
        return None

    def _modules_section(self, fidelity: FidelityMetadata | None) -> str:
        modules: list[LandingModule] = fidelity.modules if fidelity else []
        if not modules:
            return ""
        cards = []
        for mod in modules:
            cards.append(
                f"<div class='card module-card alf-card--interactive'>"
                f"<h3>{escape(mod.name)}</h3>"
                f"<p>{escape(mod.description[:500])}</p>"
                f"<p style='font-size:0.75rem;margin-top:0.5rem;color:var(--muted)'>"
                f"{escape(mod.type)}</p>"
                f"</div>"
            )
        return (
            f"<section id='modules'><h2>Ключевые системы</h2>"
            f"<div class='grid-3'>{''.join(cards)}</div></section>"
        )

    def _block_section(self, block: LandingBlock | None, section_id: str) -> str:
        if not block or not block.content.strip():
            return ""
        content = block.content.strip()
        if len(content) > LONG_TEXT_CHARS:
            body = (
                f"<details class='collapsible-section'>"
                f"<summary>Показать полностью</summary>"
                f"<p>{escape(content)}</p></details>"
            )
        else:
            body = f"<p>{escape(content)}</p>"
        return (
            f"<section id='{section_id}'><h2>{escape(block.title)}</h2>"
            f"{body}</section>"
        )

    def _normalize_items(self, items: list[str]) -> list[str]:
        return [normalize_bullet(item) for item in items if normalize_bullet(item)]

    def _list_section(
        self,
        block: LandingBlock | None,
        section_id: str,
        fallback_title: str,
    ) -> str:
        if not block:
            return ""
        raw_items = block.bullets or (
            [ln.strip() for ln in block.content.splitlines() if ln.strip()]
        )
        items = self._normalize_items(raw_items)
        if not items:
            return ""
        title = escape(block.title or fallback_title)
        if len(items) > LONG_LIST_ITEMS:
            lis = "".join(f"<li>{escape(item)}</li>" for item in items)
            body = (
                f"<details class='collapsible-section'>"
                f"<summary>Показать все ({len(items)})</summary>"
                f"<ul class='bullets'>{lis}</ul></details>"
            )
        else:
            lis = "".join(f"<li>{escape(item)}</li>" for item in items)
            body = f"<ul class='bullets'>{lis}</ul>"
        return f"<section id='{section_id}'><h2>{title}</h2>{body}</section>"

    def _io_section(self, blocks: dict[str, LandingBlock]) -> str:
        inputs = blocks.get("inputs")
        outputs = blocks.get("outputs")
        in_items = self._normalize_items(inputs.bullets if inputs else [])
        out_items = self._normalize_items(outputs.bullets if outputs else [])
        if not in_items and not out_items:
            return ""
        in_html = "".join(f"<li>{escape(i)}</li>" for i in in_items)
        out_html = "".join(f"<li>{escape(o)}</li>" for o in out_items)
        return (
            f"<section id='io'><h2>Вводные и выходные данные</h2>"
            f"<div class='grid-2'>"
            f"<div class='card'><h3>Вводные данные</h3><ul>{in_html}</ul></div>"
            f"<div class='card'><h3>Выходные данные</h3><ul>{out_html}</ul></div>"
            f"</div></section>"
        )

    def _stack_section(
        self,
        block: LandingBlock | None,
        fidelity: FidelityMetadata | None,
    ) -> str:
        grouped = fidelity.tech_stack_grouped if fidelity else {}
        if grouped:
            groups = []
            for cat, items in grouped.items():
                tags = "".join(f"<span class='stack-tag'>{escape(i)}</span>" for i in items)
                groups.append(
                    f"<div class='stack-group'><h4>{escape(cat)}</h4>"
                    f"<div class='stack-tags'>{tags}</div></div>"
                )
            return (
                f"<section id='stack'><h2>Используемый технологический стек</h2>"
                f"{''.join(groups)}</section>"
            )
        return self._list_section(block, "stack", "Технологический стек")

    def _team_contributions_html(self, contributions: list[str]) -> str:
        shown, remaining = limit_bullets(contributions)
        parts = []
        for item in shown:
            text = truncate_sentence_safe(item, MAX_TEAM_BULLET_CHARS)
            parts.append(f"<li>{escape(text)}</li>")
        if remaining > 0:
            parts.append(f'<li class="more">{escape(format_more_count(remaining))}</li>')
        return "".join(parts)

    def _team_section(
        self,
        block: LandingBlock | None,
        fidelity: FidelityMetadata | None,
        theme: ExportTheme = ExportTheme.ENTERPRISE_DARK,
    ) -> str:
        from app.services.orchestration.agents.export_guard_agent import guard_team_for_export

        verification_report = fidelity.team_verification_report if fidelity else None
        publication_mode = fidelity.team_publication_mode if fidelity else "safe_public"
        accepted_ids = list(fidelity.accepted_team_candidate_ids) if fidelity else []
        members: list[TeamMember] = list(fidelity.team_structured) if fidelity else []
        if not members and block and block.bullets:
            members = self._members_from_team_bullets(block.bullets)
        members, guard_warnings = guard_team_for_export(
            members, verification_report, publication_mode, accepted_ids
        )
        members = filter_team_members(members)
        if members:
            cards = []
            for m in members:
                contribs = self._team_contributions_html(m.contributions)
                ul = ""
                if contribs:
                    ul = (
                        f"<div class='team-contrib'><details>"
                        f"<summary>Вклад участника</summary><ul>{contribs}</ul>"
                        f"</details></div>"
                    )
                area_html = (
                    f"<p class='area'>{escape(m.project_area)}</p>" if m.project_area else ""
                )
                cards.append(
                    f"<div class='card team-card alf-card--interactive'>"
                    f"<h3>{escape(m.name)}</h3>"
                    f"<p class='role'>{escape(m.role)}</p>"
                    f"{area_html}{ul}</div>"
                )
            intro = ""
            if theme == ExportTheme.UNIVERSITY_PLATFORM:
                intro = (
                    "<p class='team-intro'>"
                    "В разделе указаны участники проекта и зафиксированный вклад "
                    "по материалам стажировки."
                    "</p>"
                )
            return (
                f"<section id='team'><h2>Команда проекта</h2>"
                f"{intro}<div class='grid-2'>{''.join(cards)}</div></section>"
            )
        return self._list_section(block, "team", "Команда проекта")

    @staticmethod
    def _members_from_team_bullets(bullets: list[str]) -> list[TeamMember]:
        members: list[TeamMember] = []
        seen: set[str] = set()
        for line in bullets:
            header = line.strip()
            if not header or header.startswith("·") or header.startswith("  ·"):
                continue
            name = header.split(" — ", 1)[0].strip()
            role = header.split(" — ", 1)[1].strip() if " — " in header else ""
            if len(name) < 5 or name.lower() in seen:
                continue
            seen.add(name.lower())
            members.append(TeamMember(name=name, role=role, project_area="", contributions=[]))
        return filter_team_members(members)
