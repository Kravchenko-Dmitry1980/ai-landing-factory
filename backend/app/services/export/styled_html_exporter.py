"""Styled static HTML export mirroring renderer section structure."""

from __future__ import annotations

from html import escape
from uuid import UUID

from app.repositories.contract_repository import ContractRepository
from app.schemas.fidelity import FidelityMetadata, LandingModule, TeamMember
from app.schemas.generation import GeneratedLanding
from app.schemas.landing_contract import LandingContract, LandingBlock
from app.services.export.export_theme import ExportTheme
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

CSS_ENTERPRISE_DARK = """
:root {
  --bg: #0f1419;
  --surface: #1a2332;
  --surface-2: #243044;
  --text: #e8edf4;
  --muted: #94a3b8;
  --accent: #3b82f6;
  --accent-muted: rgba(59,130,246,0.15);
  --border: rgba(148,163,184,0.2);
  --radius: 12px;
  --gap: 1.5rem;
  --font: "Segoe UI", system-ui, -apple-system, sans-serif;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: var(--font);
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  min-height: 100vh;
}
.container { width: 100%; max-width: 1200px; margin: 0 auto; padding: 2rem 1.5rem; }
.hero {
  padding: 3rem 0 2rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: var(--gap);
}
.hero h1 { font-size: clamp(2rem, 5vw, 3rem); font-weight: 700; margin-bottom: 0.5rem; }
.hero .meta { color: var(--muted); font-size: 0.95rem; display: flex; flex-wrap: wrap; gap: 1rem; }
.hero .tagline { font-size: 1.15rem; color: var(--muted); margin-top: 1rem; max-width: 720px; }
section { margin: 2.5rem 0; }
section h2 {
  font-size: 1.35rem;
  font-weight: 600;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid var(--accent-muted);
}
.grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: var(--gap); }
.grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: var(--gap); }
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.25rem;
}
.card h3 { font-size: 1.05rem; margin-bottom: 0.5rem; color: var(--accent); }
.card p, .card li { color: var(--muted); font-size: 0.92rem; }
.card ul { list-style: none; padding: 0; }
.card ul li { padding: 0.25rem 0; padding-left: 1rem; position: relative; }
.card ul li::before { content: "·"; position: absolute; left: 0; color: var(--accent); }
.card ul li.more { color: var(--muted); font-style: italic; }
.card ul li.more::before { content: "+"; }
ul.bullets { list-style: none; padding: 0; }
ul.bullets li {
  padding: 0.5rem 0 0.5rem 1.25rem;
  position: relative;
  border-bottom: 1px solid var(--border);
}
ul.bullets li::before { content: "▸"; position: absolute; left: 0; color: var(--accent); }
.stack-group { margin-bottom: 1rem; }
.stack-group h4 { font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--accent); margin-bottom: 0.5rem; }
.stack-tags { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.stack-tag {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 0.25rem 0.75rem;
  font-size: 0.82rem;
  color: var(--text);
}
.team-card .role { color: var(--accent); font-size: 0.85rem; margin-bottom: 0.25rem; }
.team-card .area { color: var(--muted); font-size: 0.8rem; margin-bottom: 0.5rem; }
.incomplete-banner {
  background: rgba(234,179,8,0.15);
  border: 1px solid rgba(234,179,8,0.4);
  color: #fcd34d;
  padding: 0.75rem 1rem;
  border-radius: var(--radius);
  margin-bottom: var(--gap);
  font-size: 0.9rem;
}
footer {
  margin-top: 3rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border);
  color: var(--muted);
  font-size: 0.85rem;
  text-align: center;
}
@media (max-width: 640px) {
  .container { padding: 1rem; }
  .hero { padding: 2rem 0 1.5rem; }
}
"""

CSS_UNIVERSITY_PLATFORM = """
:root {
  --bg: #ffffff;
  --surface: #F1F4F7;
  --surface-2: #EEF2F5;
  --text: #111111;
  --muted: #7A8799;
  --line: #111111;
  --accent: #7C3AED;
  --accent-hover: #6D28D9;
  --accent-light: #EDE9FE;
  --border: #E5E7EB;
  --radius: 8px;
  --gap: 1.5rem;
  --font: "Segoe UI", system-ui, Inter, -apple-system, sans-serif;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: var(--font);
  background: #ffffff;
  color: var(--text);
  line-height: 1.65;
  min-height: 100vh;
  font-size: 16px;
}
.container { width: 100%; max-width: 1200px; margin: 0 auto; padding: 2rem 1.5rem; }
.hero {
  padding: 3rem 0 2rem;
  border-bottom: 1px solid var(--line);
  margin-bottom: 3rem;
}
.hero h1 {
  font-size: clamp(2rem, 5vw, 3rem);
  font-weight: 700;
  margin-bottom: 0.75rem;
  color: #111111;
  line-height: 1.2;
}
.hero .meta { color: var(--muted); font-size: 0.95rem; display: flex; flex-wrap: wrap; gap: 1rem; }
.hero .tagline { font-size: 1.05rem; color: var(--muted); margin-top: 1rem; max-width: 100%; }
section { margin: 3rem 0; }
section h2 {
  font-size: clamp(1.5rem, 3vw, 2rem);
  font-weight: 700;
  margin-bottom: 1.25rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--line);
  color: #111111;
}
.grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: var(--gap); }
.grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: var(--gap); }
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.25rem;
}
.card h3 { font-size: 1.15rem; margin-bottom: 0.5rem; color: #111111; font-weight: 600; }
.card p, .card li { color: var(--text); font-size: 0.9375rem; line-height: 1.55; }
.card ul { list-style: none; padding: 0; }
.card ul li { padding: 0.35rem 0; padding-left: 1rem; position: relative; }
.card ul li::before { content: "·"; position: absolute; left: 0; color: var(--accent); }
.card ul li.more { color: var(--muted); font-style: italic; }
.card ul li.more::before { content: "+"; }
ul.bullets { list-style: none; padding: 0; }
ul.bullets li {
  padding: 0.65rem 0 0.65rem 1.25rem;
  position: relative;
  border-bottom: 1px solid var(--border);
}
ul.bullets li::before { content: "▸"; position: absolute; left: 0; color: var(--accent); }
.stack-group { margin-bottom: 1.25rem; }
.stack-group h4 {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--muted);
  margin-bottom: 0.5rem;
  font-weight: 600;
}
.stack-tags { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.stack-tag {
  background: var(--accent-light);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 0.3rem 0.85rem;
  font-size: 0.82rem;
  color: var(--accent);
  font-weight: 500;
}
.team-card .role { color: var(--accent); font-size: 0.85rem; margin-bottom: 0.25rem; font-weight: 500; }
.team-card .area { color: var(--muted); font-size: 0.8rem; margin-bottom: 0.5rem; }
.team-intro { color: var(--muted); font-size: 0.9rem; margin-bottom: 1.25rem; max-width: 100%; line-height: 1.55; }
.incomplete-banner {
  background: #FEF3C7;
  border: 1px solid #F59E0B;
  color: #92400E;
  padding: 0.75rem 1rem;
  border-radius: var(--radius);
  margin-bottom: var(--gap);
  font-size: 0.9rem;
}
footer {
  margin-top: 4rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border);
  color: var(--muted);
  font-size: 0.85rem;
  text-align: center;
}
@media (max-width: 640px) {
  .container { padding: 1rem; }
  .hero { padding: 2rem 0 1.5rem; }
  section { margin: 2rem 0; }
}
"""

THEME_CSS: dict[ExportTheme, str] = {
    ExportTheme.ENTERPRISE_DARK: CSS_ENTERPRISE_DARK,
    ExportTheme.UNIVERSITY_PLATFORM: CSS_UNIVERSITY_PLATFORM,
}


class StyledHtmlExporter:
    """Export contract + landing as styled responsive HTML."""

    def __init__(self, repository: ContractRepository) -> None:
        self._repo = repository
        self._legacy = HtmlExporter(repository)

    async def to_html(
        self,
        project_id: UUID,
        theme: ExportTheme = ExportTheme.ENTERPRISE_DARK,
    ) -> str:
        contract = await self._repo.get_contract(project_id)
        landing = await self._repo.get_landing(project_id)

        if not contract and not landing:
            return "<html><body><p>Landing not generated yet.</p></body></html>"

        if contract:
            return self._render_from_contract(contract, landing, theme)

        return await self._legacy.to_html(project_id)

    def _render_from_contract(
        self,
        contract: LandingContract,
        landing: GeneratedLanding | None,
        theme: ExportTheme,
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

        hero = self._hero(contract, blocks)
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

        title_fallback = contract.title or "Проект"
        title = escape(title_fallback)
        body = (
            f"{incomplete}{hero}{modules}{essence}{tasks}{purpose}{io}"
            f"{results}{stack}{team}{outlook}{footer}"
        )
        css = THEME_CSS[theme]
        body_class = (
            "theme-university_platform"
            if theme == ExportTheme.UNIVERSITY_PLATFORM
            else "theme-enterprise_dark"
        )

        return (
            f"<!DOCTYPE html><html lang='ru'><head>"
            f"<meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width, initial-scale=1'>"
            f"<title>{title}</title><style>{css}</style></head>"
            f"<body class='{body_class}'><div class='container'>{body}</div></body></html>"
        )

    def _hero(self, contract: LandingContract, blocks: dict[str, LandingBlock]) -> str:
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
        return (
            f"<header class='hero' id='hero'>"
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
                f"<div class='card module-card'>"
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
        return (
            f"<section id='{section_id}'><h2>{escape(block.title)}</h2>"
            f"<p>{escape(block.content)}</p></section>"
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
        lis = "".join(f"<li>{escape(item)}</li>" for item in items)
        return (
            f"<section id='{section_id}'><h2>{escape(block.title or fallback_title)}</h2>"
            f"<ul class='bullets'>{lis}</ul></section>"
        )

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

        members: list[TeamMember] = list(fidelity.team_structured) if fidelity else []
        if not members and block and block.bullets:
            members = self._members_from_team_bullets(block.bullets)
        members, guard_warnings = guard_team_for_export(members)
        members = filter_team_members(members)
        if members:
            cards = []
            for m in members:
                contribs = self._team_contributions_html(m.contributions)
                ul = f"<ul>{contribs}</ul>" if contribs else ""
                area_html = (
                    f"<p class='area'>{escape(m.project_area)}</p>" if m.project_area else ""
                )
                cards.append(
                    f"<div class='card team-card'>"
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
