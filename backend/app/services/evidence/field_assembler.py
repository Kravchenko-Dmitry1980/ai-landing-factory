"""Assemble LandingContract fields from FieldEvidence."""

from __future__ import annotations

import re

from app.schemas.evidence import (
    EvidenceItem,
    FieldEvidence,
    FieldSourceTrace,
    SourceInventoryItem,
    TeamMemberCandidate,
)
from app.schemas.fidelity import LandingModule, TeamMember
from app.services.contract_fidelity.structured_landing_parser import StructuredLandingParser
from app.services.evidence.field_candidates import GENERIC_TITLES, is_generic_title
from app.services.evidence.people_extractor import extract_people_from_text
from app.services.contract_fidelity.team_candidate_validator import (
    filter_team_members,
    is_team_context,
)
from app.services.evidence.technology_dictionary import (
    extract_technologies,
    technologies_to_grouped,
)

BULLET_RE = re.compile(r"^[\s]*(?:[-•*·]|–|\d+[.)])\s+(.+)$", re.MULTILINE)
NUMBERED_RE = re.compile(r"^\s*\d+\.\s+(.+)$", re.MULTILINE)
PROJECT_LINE_RE = re.compile(
    r"^Проект\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE
)
TIMELINE_RE = re.compile(
    r"Сроки проекта\s*:\s*([^\n]+)|"
    r"(\d{2}\.\d{2}\.\d{2,4}\s*[-–—]\s*\d{2}\.\d{2}\.\d{2,4})",
    re.IGNORECASE,
)
CLIENT_RE = re.compile(
    r'(ООО\s*["«][^"»]+["»]|АО\s*["«][^"»]+["»]|ИП\s+\S+)',
    re.IGNORECASE,
)
TITLE_CLIENT_RE = re.compile(r"^(.+?)\s*\(([^)]+)\)\s*$")


class FieldAssembler:
    """Merge evidence across files into contract field values."""

    def assemble_all(
        self,
        field_evidence: dict[str, FieldEvidence],
        inventory: list[SourceInventoryItem] | None = None,
    ) -> tuple[dict[str, object], list[FieldSourceTrace]]:
        traces: list[FieldSourceTrace] = []
        assembled: dict[str, object] = {}
        role_map = _role_map(inventory)
        all_items = _all_evidence_items(field_evidence)

        title, t = self.assemble_title(
            field_evidence.get("title"), role_map, all_items=all_items
        )
        traces.extend(t)
        assembled["title"] = title

        client, t = self.assemble_client(
            field_evidence.get("client"), role_map, all_items=all_items
        )
        traces.extend(t)
        assembled["client"] = client

        timeline, t = self.assemble_timeline(
            field_evidence.get("timeline"), role_map, all_items=all_items
        )
        traces.extend(t)
        assembled["timeline"] = timeline

        essence, t = self.assemble_essence(
            field_evidence.get("essence"),
            title=title,
            tech_evidence=field_evidence.get("tech_stack"),
            modules_evidence=field_evidence.get("modules"),
            purpose_evidence=field_evidence.get("purpose"),
            role_map=role_map,
            inventory=inventory,
            all_items=all_items,
        )
        traces.extend(t)
        assembled["essence"] = essence

        for field_name, method in (
            ("tasks", self.assemble_tasks),
            ("purpose", self.assemble_purpose),
            ("inputs", self.assemble_inputs),
            ("outputs", self.assemble_outputs),
            ("results", self.assemble_results),
            ("outlook", self.assemble_outlook),
        ):
            value, t = method(field_evidence.get(field_name), role_map)
            traces.extend(t)
            assembled[field_name] = value

        stack, t = self.assemble_tech_stack(field_evidence.get("tech_stack"))
        traces.extend(t)
        assembled["tech_stack"] = stack

        team, t = self.assemble_team(field_evidence.get("team"), role_map)
        traces.extend(t)
        assembled["team"] = team

        modules, t = self.assemble_modules(
            field_evidence.get("modules"),
            role_map=role_map,
            inventory=inventory,
            all_items=all_items,
        )
        traces.extend(t)
        assembled["modules"] = modules

        assembled["lead"] = _extract_lead(field_evidence, role_map, all_items=all_items)
        assembled["tagline"] = title or ""

        _apply_primary_sections(assembled, all_items, role_map)

        return assembled, traces

    def assemble_title(
        self,
        evidence: FieldEvidence | None,
        role_map: dict[str, str] | None = None,
        *,
        all_items: list[EvidenceItem] | None = None,
    ) -> tuple[str | None, list[FieldSourceTrace]]:
        traces: list[FieldSourceTrace] = []
        candidates: list[tuple[float, str, EvidenceItem]] = []
        role_map = role_map or {}

        primary_text = _combined_primary_text(all_items or [], role_map)
        if primary_text:
            parsed = StructuredLandingParser().parse(primary_text)
            if parsed.title and not is_generic_title(parsed.title):
                anchor = (evidence.items[0] if evidence and evidence.items else None)
                if anchor is None and all_items:
                    anchor = all_items[0]
                if anchor:
                    traces.append(_trace("title", anchor, "primary landing title", 1.0))
                return parsed.title, traces

        items = evidence.items if evidence else []
        ordered = _sort_items_by_role(items, role_map, "title")

        for item in ordered:
            role = role_map.get(item.source_id, "unknown")
            if role == "module_presentation":
                continue

            if role == "primary_project_doc":
                primary_title = _primary_document_title(item.text)
                if primary_title and not is_generic_title(primary_title):
                    candidates.append((1.0, primary_title, item))

            lines = [ln.strip() for ln in item.text.splitlines() if ln.strip()]
            for idx, line in enumerate(lines):
                tc = TITLE_CLIENT_RE.match(line)
                if tc:
                    val = tc.group(1).strip()
                    if not is_generic_title(val) and len(val) > 15:
                        candidates.append((_title_role_score(0.92, role), val, item))
                    continue
                proj = PROJECT_LINE_RE.match(line)
                if proj:
                    val = proj.group(1).strip()
                    if not is_generic_title(val):
                        candidates.append((_title_role_score(0.95, role), val, item))
                low = line.lower()
                if low in ("проект:", "проект") or low.startswith("проект:"):
                    inline = line.split(":", 1)[-1].strip()
                    if inline and not is_generic_title(inline):
                        candidates.append((_title_role_score(0.98, role), inline, item))
                    elif idx + 1 < len(lines):
                        nxt = lines[idx + 1].strip()
                        if not is_generic_title(nxt) and not nxt.lower().startswith("сроки"):
                            candidates.append((_title_role_score(0.99, role), nxt, item))
                    continue
                if len(line) > 25 and not is_generic_title(line):
                    if not line.lower().startswith("сроки") and not re.match(r"^\d+\.", line):
                        base = 0.75 if item.location_index == 1 else 0.35
                        candidates.append((_title_role_score(base, role), line, item))

            title_hint = item.section_hint or item.location_label
            if (
                title_hint
                and len(title_hint) > 20
                and not is_generic_title(title_hint)
                and item.location_index == 1
                and role != "module_presentation"
            ):
                candidates.append((_title_role_score(0.68, role), title_hint, item))

        candidates.sort(key=lambda x: x[0], reverse=True)
        for score, val, item in candidates:
            traces.append(_trace("title", item, "explicit project title line", score))
            return val, traces

        return None, traces

    def assemble_client(
        self,
        evidence: FieldEvidence | None,
        role_map: dict[str, str] | None = None,
        *,
        all_items: list[EvidenceItem] | None = None,
    ) -> tuple[str | None, list[FieldSourceTrace]]:
        traces: list[FieldSourceTrace] = []
        role_map = role_map or {}
        primary_text = _combined_primary_text(all_items or [], role_map)
        if primary_text:
            parsed = StructuredLandingParser().parse(primary_text)
            if parsed.client:
                return parsed.client, traces
        for item in _sort_items_by_role(evidence.items if evidence else [], role_map, "client"):
            match = CLIENT_RE.search(item.text)
            if match:
                traces.append(_trace("client", item, "legal entity marker", 0.8))
                return match.group(1).strip(), traces
            for line in _strip_slide_header(item.text).splitlines():
                tc = TITLE_CLIENT_RE.match(line.strip())
                if tc:
                    client = tc.group(2).strip()
                    if len(client) > 3:
                        traces.append(_trace("client", item, "title parenthetical", 0.75))
                        return client, traces
            if "заказчик" in item.normalized_text.lower():
                lines = item.text.splitlines()
                for ln in lines:
                    if "заказчик" in ln.lower() and len(ln) > 12:
                        traces.append(_trace("client", item, "client line", 0.6))
                        return ln.split(":", 1)[-1].strip() or ln.strip(), traces
        return None, traces

    def assemble_timeline(
        self,
        evidence: FieldEvidence | None,
        role_map: dict[str, str] | None = None,
        *,
        all_items: list[EvidenceItem] | None = None,
    ) -> tuple[str | None, list[FieldSourceTrace]]:
        traces: list[FieldSourceTrace] = []
        role_map = role_map or {}
        primary_text = _combined_primary_text(all_items or [], role_map)
        if primary_text:
            parsed = StructuredLandingParser().parse(primary_text)
            if parsed.timeline:
                return parsed.timeline, traces
        for item in _sort_items_by_role(evidence.items if evidence else [], role_map, "timeline"):
            for date in item.dates:
                if "-" in date or "—" in date or "–" in date:
                    traces.append(_trace("timeline", item, "date range", 0.85))
                    return date.replace("Сроки проекта:", "").strip(), traces
            match = TIMELINE_RE.search(item.text)
            if match:
                val = (match.group(1) or match.group(2) or "").strip()
                if val:
                    traces.append(_trace("timeline", item, "timeline pattern", 0.85))
                    return val, traces
        return None, traces

    def assemble_essence(
        self,
        evidence: FieldEvidence | None,
        *,
        title: str | None,
        tech_evidence: FieldEvidence | None,
        modules_evidence: FieldEvidence | None,
        purpose_evidence: FieldEvidence | None,
        role_map: dict[str, str] | None = None,
        inventory: list[SourceInventoryItem] | None = None,
        all_items: list[EvidenceItem] | None = None,
    ) -> tuple[str, list[FieldSourceTrace]]:
        traces: list[FieldSourceTrace] = []
        role_map = role_map or {}
        primary_text = _combined_primary_text(all_items or [], role_map)
        if primary_text:
            parsed = StructuredLandingParser().parse(primary_text)
            if parsed.essence and len(parsed.essence.strip()) >= 200:
                traces.append(
                    FieldSourceTrace(
                        field_name="essence",
                        source_filename=_primary_filename(inventory, role_map) or "",
                        location_type="section",
                        location_index=1,
                        reason="primary landing essence",
                        confidence=0.95,
                    )
                )
                return parsed.essence.strip()[:1500], traces

        paragraphs: list[str] = []
        ordered = _sort_items_by_role(evidence.items if evidence else [], role_map, "essence")

        for item in ordered:
            role = role_map.get(item.source_id, "unknown")
            if role == "module_presentation":
                continue
            body = _strip_slide_header(item.text)
            if "суть проекта" in body.lower()[:40]:
                section_body = re.split(r"суть проекта\s*\n", body, maxsplit=1, flags=re.IGNORECASE)
                essence_body = section_body[-1].strip() if section_body else body
                if len(essence_body) >= 200:
                    traces.append(_trace("essence", item, "primary essence section", 0.95))
                    return essence_body[:1500], traces
            if "главная цель" in body.lower() or "цели проекта" in body.lower():
                for sent in _sentences(body):
                    if len(sent) > 50 and "slide" not in sent.lower():
                        paragraphs.append(sent)
                        traces.append(_trace("essence", item, "goal slide", 0.85))
            elif "контекст и цель" in body.lower() or "цель прототипа" in body.lower():
                for sent in _sentences(body):
                    if len(sent) > 45:
                        paragraphs.append(sent)
                        traces.append(_trace("essence", item, "context slide", 0.8))

        if not paragraphs:
            for item in ordered[:3]:
                body = _strip_slide_header(item.text)
                if item.location_index == 1:
                    continue
                if role_map.get(item.source_id) == "module_presentation":
                    continue
                for sent in _sentences(body):
                    if len(sent) > 60 and not sent.lower().startswith("slide"):
                        paragraphs.append(sent)
                        traces.append(_trace("essence", item, "slide body", 0.6))
                        if len(paragraphs) >= 3:
                            break

        technologies = extract_technologies(
            "\n".join(i.text for i in (evidence.items if evidence else [])[:10])
        )
        if tech_evidence:
            for item in tech_evidence.items[:5]:
                technologies.extend(item.technologies)
        technologies = list(dict.fromkeys(technologies))[:8]

        module_names: list[str] = []
        if modules_evidence:
            mods, _ = self.assemble_modules(
                modules_evidence,
                role_map=role_map,
                inventory=inventory,
                all_items=all_items,
            )
            module_names = [m.name for m in mods[:6]]

        purpose_bits: list[str] = []
        if purpose_evidence:
            purpose_bits, _ = self.assemble_purpose(purpose_evidence)

        if title and len(paragraphs) < 2:
            paragraphs.insert(0, f"Проект «{title}» направлен на разработку решения для автоматизации и аналитики.")

        if technologies or module_names:
            tech_str = ", ".join(technologies[:5]) if technologies else "современные технологии"
            mod_str = ", ".join(module_names[:5]) if module_names else "ключевые модули обработки"
            purpose_str = purpose_bits[0] if purpose_bits else "повышение качества аналитики и скорости работы с данными"
            synth = (
                f"Проект направлен на создание аналитической системы, которая {purpose_str[:120]}. "
                f"Система использует {tech_str} и объединяет этапы: {mod_str}. "
                f"Основная ценность — автоматизация сбора, анализа и представления данных."
            )
            if evidence and evidence.items:
                traces.append(_trace("essence", evidence.items[0], "deterministic synthesis", 0.7))
            paragraphs.append(synth)

        essence = " ".join(dict.fromkeys(p.strip() for p in paragraphs if p.strip()))
        if len(essence) < 280 and evidence:
            extra = " ".join(_strip_slide_header(i.text)[:400] for i in evidence.items[1:4])
            essence = f"{essence} {extra[:500]}".strip()
        return essence[:1500], traces

    def assemble_tasks(
        self,
        evidence: FieldEvidence | None,
        role_map: dict[str, str] | None = None,
    ) -> tuple[list[str], list[FieldSourceTrace]]:
        traces: list[FieldSourceTrace] = []
        tasks: list[str] = []
        role_map = role_map or {}
        for item in _sort_items_by_role(evidence.items if evidence else [], role_map, "tasks"):
            body = _strip_slide_header(item.text)
            lower = body.lower()
            if "задачи проекта" in lower or "этапы работы" in lower:
                for line in _bullet_lines(body):
                    if len(line) > 15:
                        tasks.append(_normalize_line(line))
                        traces.append(_trace("tasks", item, "task bullet", 0.8))
                for line in body.splitlines():
                    line = line.strip()
                    if len(line) < 20:
                        continue
                    low_line = line.lower()
                    if low_line.startswith(
                        ("задачи проекта", "slide", "этапы работы", "главная", "расширенные")
                    ):
                        continue
                    if re.match(r"^\d+\.", line):
                        tasks.append(_normalize_line(re.sub(r"^\d+\.\s*", "", line)))
                        traces.append(_trace("tasks", item, "numbered task", 0.78))
                    elif re.match(r"^[А-ЯЁ]", line) and len(line) > 25:
                        tasks.append(_normalize_line(line))
                        traces.append(_trace("tasks", item, "task line", 0.75))
            if any(
                k in lower
                for k in (
                    "семантический поиск", "bertopic", "neo4j", "qdrant",
                    "пользовательский запрос", "граф новостей", "темы (",
                )
            ):
                for line in _bullet_lines(body):
                    if len(line) > 10:
                        tasks.append(_normalize_line(line))
                        traces.append(_trace("tasks", item, "pipeline bullet", 0.8))
                title = item.section_hint or _first_meaningful_line(body)
                if title and len(title) > 8 and "направления развития" not in title.lower():
                    tasks.append(_normalize_line(title))
                    traces.append(_trace("tasks", item, "pipeline slide title", 0.75))
            for line in NUMBERED_RE.findall(body):
                if len(line) > 20:
                    tasks.append(_normalize_line(line))
        return _dedupe(tasks)[:14], traces

    def assemble_purpose(
        self,
        evidence: FieldEvidence | None,
        role_map: dict[str, str] | None = None,
    ) -> tuple[list[str], list[FieldSourceTrace]]:
        traces: list[FieldSourceTrace] = []
        purpose: list[str] = []
        role_map = role_map or {}
        for item in _sort_items_by_role(evidence.items if evidence else [], role_map, "purpose"):
            body = _strip_slide_header(item.text)
            lower = body.lower()
            if any(
                k in lower
                for k in ("польза проекта", "главная цель", "цели проекта", "цель прототипа")
            ):
                for sent in _sentences(item.text):
                    sl = sent.lower()
                    if any(
                        v in sl
                        for v in ("обеспечить", "повысить", "снизить", "автоматиз", "создать", "предостав")
                    ):
                        purpose.append(sent.strip())
                        traces.append(_trace("purpose", item, "goal sentence", 0.75))
                for line in _bullet_lines(item.text):
                    if len(line) > 20:
                        purpose.append(line)
                        traces.append(_trace("purpose", item, "goal bullet", 0.7))
                main_goal = re.search(
                    r"Главная цель:\s*(.+?)(?:\nРасширенные|\Z)",
                    item.text,
                    re.IGNORECASE | re.DOTALL,
                )
                if main_goal:
                    purpose.append(_normalize_line(main_goal.group(1)[:300]))
                    traces.append(_trace("purpose", item, "main goal", 0.85))
            if "шлагбаум" in lower:
                purpose.append("Автоматизировать открытие шлагбаума по распознанному номеру.")
                traces.append(_trace("purpose", item, "KSK goal", 0.8))
        return _dedupe(purpose)[:10], traces

    def assemble_inputs(
        self,
        evidence: FieldEvidence | None,
        role_map: dict[str, str] | None = None,
    ) -> tuple[list[str], list[FieldSourceTrace]]:
        traces: list[FieldSourceTrace] = []
        inputs: list[str] = []
        role_map = role_map or {}
        for item in _sort_items_by_role(evidence.items if evidence else [], role_map, "inputs"):
            body = item.text
            lower = body.lower()
            if any(
                k in lower
                for k in (
                    "входные", "исходные данные", "telegram", "подготовка данных",
                    "требования к входным", "видеодан",
                )
            ):
                for line in _bullet_lines(body):
                    if len(line) > 12:
                        inputs.append(line)
                        traces.append(_trace("inputs", item, "input bullet", 0.75))
                if "десятки тысяч постов" in lower or "исходные данные" in lower:
                    inputs.append("Потоки сообщений и постов из Telegram-каналов.")
                    traces.append(_trace("inputs", item, "data source", 0.8))
                    for line in item.text.splitlines():
                        line = line.strip()
                        if len(line) > 20 and "исходные" not in line.lower():
                            inputs.append(line)
                            traces.append(_trace("inputs", item, "source line", 0.7))
                if "камер" in lower and "заказчик" in lower:
                    inputs.append("Кадры и видео с камер заказчика.")
                    traces.append(_trace("inputs", item, "video input", 0.8))
                if "roboflow" in lower or "cvat" in lower:
                    inputs.append("Датасеты и разметка в CVAT / Roboflow.")
                    traces.append(_trace("inputs", item, "annotation", 0.75))
        return _dedupe(inputs)[:12], traces

    def assemble_outputs(
        self,
        evidence: FieldEvidence | None,
        role_map: dict[str, str] | None = None,
    ) -> tuple[list[str], list[FieldSourceTrace]]:
        traces: list[FieldSourceTrace] = []
        outputs: list[str] = []
        role_map = role_map or {}
        for item in _sort_items_by_role(evidence.items if evidence else [], role_map, "outputs"):
            body = item.text.lower()
            if any(k in body for k in ("выходные", "демо", "прототип", "интерфейс", "дашборд", "веб-прилож")):
                for line in _bullet_lines(item.text):
                    if len(line) > 12:
                        outputs.append(line)
                        traces.append(_trace("outputs", item, "output bullet", 0.75))
            if "что видит конечный пользователь" in body:
                outputs.append("Интерфейс аналитика с поиском, темами и графом связанных новостей.")
                traces.append(_trace("outputs", item, "user-facing slide", 0.85))
            if "google colab" in body or "демонстрационный пайплайн" in body:
                outputs.append("Демонстрационный пайплайн в Google Colab.")
                traces.append(_trace("outputs", item, "demo format", 0.8))
        return _dedupe(outputs)[:12], traces

    def assemble_results(
        self,
        evidence: FieldEvidence | None,
        role_map: dict[str, str] | None = None,
    ) -> tuple[list[str], list[FieldSourceTrace]]:
        traces: list[FieldSourceTrace] = []
        results: list[str] = []
        role_map = role_map or {}
        for item in _sort_items_by_role(evidence.items if evidence else [], role_map, "results"):
            body = item.text
            lower = body.lower()
            if any(
                k in lower
                for k in ("метрики", "результат", "итог", "достигнут", "показател", "полученные")
            ):
                for line in _bullet_lines(body):
                    if len(line) > 12 and (
                        "точность" in line.lower() or "%" in line or "uptime" in line.lower()
                    ):
                        results.append(line)
                        traces.append(_trace("results", item, "metric", 0.8))
                    elif len(line) > 20:
                        results.append(line)
                        traces.append(_trace("results", item, "result bullet", 0.7))
                for line in body.splitlines():
                    line = line.strip()
                    if "%" in line and len(line) > 15:
                        results.append(line)
                        traces.append(_trace("results", item, "metric line", 0.75))
            if "прототип" in lower and ("итог" in lower or "стажировк" in lower):
                results.append(
                    "Рабочий демо-пайплайн семантического поиска, тем и графа сущностей."
                )
                traces.append(_trace("results", item, "prototype outcome", 0.85))
            if "streamlit" in lower and "демо" in lower:
                results.append("Streamlit demo panel для демонстрации pipeline.")
                traces.append(_trace("results", item, "demo result", 0.75))
        return _dedupe(results)[:12], traces

    def assemble_outlook(
        self,
        evidence: FieldEvidence | None,
        role_map: dict[str, str] | None = None,
    ) -> tuple[list[str], list[FieldSourceTrace]]:
        traces: list[FieldSourceTrace] = []
        outlook: list[str] = []
        role_map = role_map or {}
        for item in _sort_items_by_role(evidence.items if evidence else [], role_map, "outlook"):
            lower = item.text.lower()
            if any(
                k in lower
                for k in ("направления развития", "планы по", "перспектив", "roadmap")
            ):
                for line in _bullet_lines(item.text):
                    if len(line) > 15:
                        outlook.append(line)
                        traces.append(_trace("outlook", item, "roadmap bullet", 0.75))
                for line in item.text.splitlines():
                    line = line.strip()
                    if len(line) < 18:
                        continue
                    if line.lower().startswith(
                        ("направления", "планы по", "slide", "рекомендации")
                    ):
                        continue
                    if re.match(r"^[А-ЯЁA-Z]", line):
                        outlook.append(line)
                        traces.append(_trace("outlook", item, "roadmap line", 0.7))
        return _dedupe(outlook)[:10], traces

    def assemble_tech_stack(
        self, evidence: FieldEvidence | None
    ) -> tuple[dict[str, list[str]], list[FieldSourceTrace]]:
        traces: list[FieldSourceTrace] = []
        all_tech: list[str] = []
        for item in evidence.items if evidence else []:
            all_tech.extend(item.technologies)
            all_tech.extend(extract_technologies(item.text))
            if item.technologies or extract_technologies(item.text):
                traces.append(_trace("tech_stack", item, "technology mentions", 0.8))
        canonical = list(dict.fromkeys(all_tech))
        return technologies_to_grouped(canonical), traces

    def assemble_team(
        self,
        evidence: FieldEvidence | None,
        role_map: dict[str, str] | None = None,
    ) -> tuple[list[TeamMember], list[FieldSourceTrace]]:
        traces: list[FieldSourceTrace] = []
        candidates: list[TeamMemberCandidate] = []
        role_map = role_map or {}
        for item in _sort_items_by_role(evidence.items if evidence else [], role_map, "team"):
            ref = f"{item.filename}#{item.location_index}"
            hint = item.section_hint or item.location_label or ""
            in_team = is_team_context(hint, item.text)
            candidates.extend(
                extract_people_from_text(
                    item.text,
                    source_ref=ref,
                    section_hint=hint,
                    in_team_section=in_team,
                )
            )
            if candidates:
                traces.append(_trace("team", item, "people extraction", 0.75))

        members: list[TeamMember] = []
        seen: set[str] = set()
        for c in candidates:
            key = c.name.lower()
            if key in seen:
                continue
            seen.add(key)
            members.append(
                TeamMember(
                    name=c.name,
                    role=c.role,
                    project_area=c.project_area,
                    contributions=c.contributions,
                )
            )
        return filter_team_members(members)[:20], traces

    def assemble_modules(
        self,
        evidence: FieldEvidence | None,
        *,
        role_map: dict[str, str] | None = None,
        inventory: list[SourceInventoryItem] | None = None,
        all_items: list[EvidenceItem] | None = None,
    ) -> tuple[list[LandingModule], list[FieldSourceTrace]]:
        traces: list[FieldSourceTrace] = []
        modules: list[LandingModule] = []
        seen: set[str] = set()
        role_map = role_map or {}

        primary_text = _combined_primary_text(all_items or [], role_map)
        if primary_text:
            parsed = StructuredLandingParser().parse(primary_text)
            for mod in parsed.modules:
                _add_module(modules, seen, mod.name, mod.type or "system", None, traces, mod.description)

        has_primary_modules = bool(modules)

        for item in evidence.items if evidence else []:
            role = role_map.get(item.source_id, "unknown")
            body = _strip_slide_header(item.text)
            title = item.section_hint or _first_meaningful_line(body)

            if role == "module_presentation":
                _enrich_module_from_presentation(modules, item, body, traces)
                continue

            if has_primary_modules and role not in ("supporting_presentation", "unknown"):
                continue

            if re.search(r"шаг\s*\d+", body, re.IGNORECASE):
                for match in re.finditer(
                    r"Шаг\s*(\d+)\s*:\s*(.+?)(?=\nШаг\s*\d+\s*:|\Z)",
                    body,
                    re.IGNORECASE | re.DOTALL,
                ):
                    name = match.group(2).split("\n")[0].strip()[:120]
                    _add_module(modules, seen, name, "pipeline_step", item, traces)

            if any(k in body.lower() for k in ("семантический поиск", "bertopic", "neo4j", "граф новостей")):
                for line in _bullet_lines(body):
                    if any(t in line.lower() for t in ("qdrant", "bertopic", "neo4j", "поиск", "граф", "запрос")):
                        _add_module(modules, seen, line[:120], "analytics_module", item, traces)
                if title and len(title) > 8:
                    _add_module(modules, seen, title, "slide_module", item, traces)

            if (
                not has_primary_modules
                and "архитектура" in body.lower()
                and item.technologies
            ):
                for tech in item.technologies[:6]:
                    _add_module(
                        modules, seen, f"Компонент: {tech}", "architecture", item, traces
                    )

        return modules[:15], traces


def _add_module(
    modules: list[LandingModule],
    seen: set[str],
    name: str,
    mod_type: str,
    item: EvidenceItem | None,
    traces: list[FieldSourceTrace],
    description: str = "",
) -> None:
    key = name.lower()[:80]
    if key in seen or len(name) < 2:
        return
    seen.add(key)
    modules.append(LandingModule(name=name, description=description, type=mod_type))
    if item is not None:
        traces.append(_trace("modules", item, f"module: {name[:40]}", 0.7))


def _trace(field: str, item: EvidenceItem, reason: str, confidence: float) -> FieldSourceTrace:
    return FieldSourceTrace(
        field_name=field,
        source_filename=item.filename,
        location_type=item.location_type,
        location_index=item.location_index,
        reason=reason,
        confidence=confidence,
    )


def _strip_slide_header(text: str) -> str:
    lines = text.splitlines()
    if lines and re.match(r"Slide\s+\d+\s*:", lines[0], re.IGNORECASE):
        lines = lines[1:]
    return "\n".join(lines).strip()


def _bullet_lines(text: str) -> list[str]:
    items = BULLET_RE.findall(text) + NUMBERED_RE.findall(text)
    out: list[str] = []
    for item in items:
        line = item.strip()
        if line and line not in out:
            out.append(line)
    if not out:
        for line in text.splitlines():
            line = line.strip()
            if line.startswith(("•", "-", "—")) and len(line) > 10:
                out.append(line.lstrip("•-— ").strip())
    return out


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.replace("\n", " "))
    return [p.strip() for p in parts if len(p.strip()) > 25]


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.lower()[:100]
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def _normalize_line(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


def _first_meaningful_line(text: str) -> str:
    for line in _strip_slide_header(text).splitlines():
        line = line.strip()
        if len(line) > 8 and line.lower() not in GENERIC_TITLES:
            return line
    return ""


def _extract_lead(
    field_evidence: dict[str, FieldEvidence],
    role_map: dict[str, str] | None = None,
    *,
    all_items: list[EvidenceItem] | None = None,
) -> str | None:
    role_map = role_map or {}
    primary_text = _combined_primary_text(all_items or [], role_map)
    if primary_text:
        parsed = StructuredLandingParser().parse(primary_text)
        if parsed.lead:
            return parsed.lead
    team = field_evidence.get("team")
    if not team:
        return None
    role_map = role_map or {}
    for item in _sort_items_by_role(team.items, role_map, "team"):
        match = re.search(r"Тимлид\s*:\s*(.+?)(?:\n|$)", item.text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _apply_primary_sections(
    assembled: dict[str, object],
    all_items: list[EvidenceItem],
    role_map: dict[str, str],
) -> None:
    primary_text = _combined_primary_text(all_items, role_map)
    if not primary_text:
        return
    parsed = StructuredLandingParser().parse(primary_text)
    if parsed.tasks:
        assembled["tasks"] = parsed.tasks
    if parsed.purpose:
        assembled["purpose"] = parsed.purpose
    if parsed.inputs:
        assembled["inputs"] = parsed.inputs
    if parsed.outputs:
        assembled["outputs"] = parsed.outputs
    if parsed.results:
        assembled["results"] = parsed.results
    if parsed.outlook:
        assembled["outlook"] = parsed.outlook
    if parsed.team:
        assembled["team"] = filter_team_members(parsed.team)


def _role_map(inventory: list[SourceInventoryItem] | None) -> dict[str, str]:
    if not inventory:
        return {}
    return {item.source_id: item.source_role for item in inventory}
    if not inventory:
        return {}
    return {item.source_id: item.source_role for item in inventory}


def _role_rank(role: str, field: str) -> float:
    from app.services.evidence.field_evidence_builder import SOURCE_ROLE_PRIORITY

    return SOURCE_ROLE_PRIORITY.get(field, {}).get(role, 0.15)


def _sort_items_by_role(
    items: list[EvidenceItem],
    role_map: dict[str, str],
    field: str,
) -> list[EvidenceItem]:
    return sorted(
        items,
        key=lambda it: (
            -_role_rank(role_map.get(it.source_id, "unknown"), field),
            0 if it.location_index == 1 else 1,
            it.location_index or 99,
        ),
    )


def _title_role_score(base: float, role: str) -> float:
    if role == "primary_project_doc":
        return max(base, 0.99)
    if role == "module_presentation":
        return min(base, 0.2)
    if role == "supporting_presentation":
        return base
    return base


def _primary_document_title(text: str) -> str | None:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return None
    first = lines[0]
    if re.match(r"^заказчик\s*:", first, re.IGNORECASE):
        return None
    if len(first) < 120 and not first.endswith(":"):
        return first
    return None


def _combined_primary_text(
    items: list[EvidenceItem],
    role_map: dict[str, str],
) -> str:
    primary_ids = {
        sid for sid, role in role_map.items() if role == "primary_project_doc"
    }
    if not primary_ids or not items:
        return ""
    chunks = [
        item.text
        for item in sorted(
            items,
            key=lambda it: (it.source_id, it.location_index or 0),
        )
        if item.source_id in primary_ids
    ]
    return "\n\n".join(chunks)


def _all_evidence_items(field_evidence: dict[str, FieldEvidence]) -> list[EvidenceItem]:
    merged: list[EvidenceItem] = []
    seen: set[str] = set()
    for fe in field_evidence.values():
        for item in fe.items:
            if item.evidence_id in seen:
                continue
            seen.add(item.evidence_id)
            merged.append(item)
    return merged


def _primary_filename(
    inventory: list[SourceInventoryItem] | None,
    role_map: dict[str, str],
) -> str | None:
    if not inventory:
        return None
    for src in inventory:
        if src.source_role == "primary_project_doc":
            return src.filename
    return None


def _enrich_module_from_presentation(
    modules: list[LandingModule],
    item: EvidenceItem,
    body: str,
    traces: list[FieldSourceTrace],
) -> None:
    slide_title = item.section_hint or _first_meaningful_line(body)
    if not slide_title:
        return
    for mod in modules:
        if _module_names_related(mod.name, slide_title):
            detail = body[:400].strip()
            if detail and detail not in mod.description:
                mod.description = detail[:400]
            traces.append(_trace("modules", item, f"enriched module: {mod.name[:30]}", 0.75))
            return


def _module_names_related(module_name: str, candidate: str) -> bool:
    mod = module_name.lower()
    cand = candidate.lower()
    if mod in cand or cand in mod:
        return True
    if "copilot" in mod and "copilot" in cand:
        return True
    if "glauco" in mod and "glauco" in cand:
        return True
    if "vitacalc" in mod and ("vita" in cand or "calc" in cand):
        return True
    return mod.split()[0] in cand if mod.split() else False
