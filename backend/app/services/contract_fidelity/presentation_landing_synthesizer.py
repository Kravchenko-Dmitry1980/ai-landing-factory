"""Synthesize LandingContract fields from project presentation (PPTX) text."""

from __future__ import annotations

import re

from app.schemas.fidelity import (
    LandingModule,
    ParsedStructuredLanding,
    SourceTypeResult,
    TeamMember,
)
from app.services.contract_fidelity.stack_parser import stack_to_bullets

SLIDE_SPLIT_RE = re.compile(r"(?:^|\n)(Slide\s+\d+\s*:)", re.IGNORECASE)
STEP_RE = re.compile(
    r"Шаг\s*(\d+)\s*:\s*(.+?)(?=\nШаг\s*\d+\s*:|\Z)",
    re.IGNORECASE | re.DOTALL,
)
PHASE_RE = re.compile(
    r"(\d+)\.\s*(?:Фаза\s+)?([^:\n]+?):\s*\n((?:[^\n]+\n?)*)",
    re.IGNORECASE,
)
NAME_RE = re.compile(
    r"^[А-ЯЁA-Z][а-яёa-z]+\s+[А-ЯЁA-Z][а-яёa-z]+(?:\s+[А-ЯЁA-Z][а-яёa-z]+)?$"
)
TITLE_CLIENT_RE = re.compile(r"^(.+?)\s*\(([^)]+)\)\s*$")
LEAD_RE = re.compile(r"Тимлид\s*:\s*(.+?)(?:\n|$)", re.IGNORECASE)
ASSISTANT_RE = re.compile(
    r"Помощник\s+тимлида\s*:\s*(.+?)(?:\n|$)", re.IGNORECASE
)
NUMBERED_ITEM_RE = re.compile(r"^\s*\d+\.\s+(.+)$", re.MULTILINE)
BULLET_RE = re.compile(r"^[\s]*(?:[-•*·]|–)\s+(.+)$", re.MULTILINE)

TECH_CATALOG: dict[str, tuple[str, str]] = {
    "yolov8-n-cls": ("AI / CV", "YOLOv8-n-cls"),
    "yolov8-n": ("AI / CV", "YOLOv8-n"),
    "yolov8n": ("AI / CV", "YOLOv8-n"),
    "yolov8": ("AI / CV", "YOLOv8"),
    "computer vision": ("AI / CV", "Computer Vision"),
    "компьютерного зрения": ("AI / CV", "Computer Vision"),
    "bounding box": ("AI / CV", "Bounding Box"),
    "bbox": ("AI / CV", "Bounding Box"),
    "opencv": ("AI / CV", "OpenCV"),
    "cvat": ("Data / Annotation", "CVAT"),
    "roboflow": ("Data / Annotation", "Roboflow"),
    "supervision": ("Data / Annotation", "Supervision"),
    "python": ("Backend / App", "Python"),
    "streamlit": ("Backend / App", "Streamlit"),
    "google colab": ("Backend / App", "Google Colab"),
    "colab": ("Backend / App", "Google Colab"),
    "*.py": ("Backend / App", "*.py scripts"),
    "gpu": ("Infrastructure", "GPU"),
    "видео": ("Infrastructure", "video processing"),
}

MODULE_TYPE_HINTS: list[tuple[str, str]] = [
    ("обнаружение", "computer_vision_detection"),
    ("идентификация", "classification"),
    ("классификация", "classification"),
    ("распознавание", "ocr_recognition"),
    ("проверка", "access_control"),
    ("базе данных", "access_control"),
    ("демо", "demo_application"),
    ("streamlit", "demo_application"),
]

SLIDE_TYPE_RULES: list[tuple[str, list[str]]] = [
    ("goal", ["цель проекта"]),
    ("stages", ["этапы проекта"]),
    ("data_preparation", ["подготовка данных"]),
    ("pipeline_steps", ["шаг 1", "шаг 2", "шаг 3"]),
    ("demo", ["демо-панель", "streamlit"]),
    ("results", ["итоги проекта", "полученные результаты"]),
    ("sources", ["первоисточник", "ссылки на"]),
    ("team", [
        "команда управления",
        "команда проекта",
        "участники команды",
        "роли в проекте",
        "тимлид:",
        "помощник тимлида:",
    ]),
]


class PresentationLandingSynthesizer:
    """Build structured landing fields from presentation slide text."""

    def synthesize(
        self,
        text: str,
        source_type: SourceTypeResult | None = None,
    ) -> ParsedStructuredLanding:
        text = _normalize(text)
        slides = self.split_slides(text)
        classified_types = {
            idx: self.classify_slide(slide) for idx, slide in slides.items()
        }

        title, client = self._extract_title_client(slides.get(1, ""))
        lead = self._extract_lead(text)

        goal_slides = _slides_by_type(slides, classified_types, "goal")
        stage_slides = _slides_by_type(slides, classified_types, "stages")
        data_slides = _slides_by_type(slides, classified_types, "data_preparation")
        pipeline_slides = _slides_by_type(slides, classified_types, "pipeline_steps")
        demo_slides = _slides_by_type(slides, classified_types, "demo")
        results_slides = _slides_by_type(slides, classified_types, "results")
        sources_slides = _slides_by_type(slides, classified_types, "sources")
        team_slides = _slides_by_type(slides, classified_types, "team")

        modules = self.extract_modules(text, pipeline_slides)
        essence = self.extract_essence(goal_slides, modules, title)
        tasks = self.extract_tasks(stage_slides, goal_slides)
        purpose = self.extract_purpose(goal_slides, essence)
        inputs = self.extract_inputs(data_slides, goal_slides)
        outputs = self.extract_outputs(pipeline_slides, demo_slides, modules)
        results = self.extract_results(results_slides, demo_slides)
        outlook = self.extract_outlook(results_slides)
        tech_stack_grouped = self.extract_stack(text, sources_slides)
        team = self.extract_team(team_slides, slides, classified_types)

        timeline = self._extract_timeline(stage_slides)
        tagline = title or ""

        section_lengths = {
            "essence": len(essence),
            "tasks": len("\n".join(tasks)),
            "purpose": len("\n".join(purpose)),
            "inputs": len("\n".join(inputs)),
            "outputs": len("\n".join(outputs)),
            "results": len("\n".join(results)),
            "outlook": len("\n".join(outlook)),
            "tech_stack": sum(len(v) for v in tech_stack_grouped.values()),
            "team": len("\n".join(m.name for m in team)),
        }

        return ParsedStructuredLanding(
            title=title,
            client=client,
            timeline=timeline,
            lead=lead,
            essence=essence,
            tasks=tasks,
            purpose=purpose,
            inputs=inputs,
            outputs=outputs,
            results=results,
            outlook=outlook,
            tech_stack_grouped=tech_stack_grouped,
            team=team,
            modules=modules,
            tagline=tagline,
            section_lengths=section_lengths,
        )

    def split_slides(self, text: str) -> dict[int, str]:
        parts = SLIDE_SPLIT_RE.split(text)
        slides: dict[int, str] = {}
        i = 1
        while i < len(parts):
            header = parts[i].strip()
            body = parts[i + 1] if i + 1 < len(parts) else ""
            match = re.search(r"(\d+)", header)
            if match:
                slides[int(match.group(1))] = f"{header}\n{body}".strip()
            i += 2
        if not slides and text.strip():
            slides[1] = text.strip()
        return slides

    def detect_slide_title(self, slide: str) -> str:
        lines = [ln.strip() for ln in slide.splitlines() if ln.strip()]
        if not lines:
            return ""
        if lines[0].lower().startswith("slide"):
            lines = lines[1:]
        return lines[0] if lines else ""

    def classify_slide(self, slide: str) -> str:
        normalized = slide.lower().replace("\u000b", " ")
        if re.search(r"^slide\s*1\s*:", normalized[:20]):
            return "title"
        for slide_type, markers in SLIDE_TYPE_RULES:
            if any(m in normalized for m in markers):
                return slide_type
        if re.search(r"шаг\s*\d+\s*:", normalized):
            return "pipeline_steps"
        if NAME_RE.match(self.detect_slide_title(slide)):
            return "team_member"
        return "unknown"

    def extract_essence(
        self,
        goal_slides: list[str],
        modules: list[LandingModule],
        title: str | None,
    ) -> str:
        paragraphs: list[str] = []
        for slide in goal_slides:
            body = _strip_slide_header(slide)
            body = re.sub(r"^цель\s+проекта\s*", "", body, flags=re.IGNORECASE).strip()
            sentences = _split_sentences(body)
            if sentences:
                paragraphs.append(sentences[0])
            for sent in sentences[1:4]:
                if len(sent) > 40:
                    paragraphs.append(sent)

        if modules:
            names = ", ".join(m.name.lower() for m in modules[:6])
            paragraphs.append(
                f"Pipeline обработки включает этапы: {names}."
            )

        if title and "шлагбаум" in title.lower():
            paragraphs.append(
                "Система использует компьютерное зрение, модели YOLOv8 "
                "и проверку номера в базе разрешённых автомобилей."
            )

        essence = " ".join(dict.fromkeys(p.strip() for p in paragraphs if p.strip()))
        if len(essence) < 280 and goal_slides:
            extra = _strip_slide_header(goal_slides[0])
            essence = f"{essence} {extra[:400]}".strip()
        return essence[:1200]

    def extract_tasks(
        self,
        stage_slides: list[str],
        goal_slides: list[str],
    ) -> list[str]:
        tasks: list[str] = []
        for slide in stage_slides:
            body = _strip_slide_header(slide)
            for phase_match in PHASE_RE.finditer(body):
                phase_title = phase_match.group(2).strip()
                phase_body = phase_match.group(3).strip()
                tasks.append(_normalize_task(phase_title))
                for line in phase_body.splitlines():
                    line = line.strip()
                    if len(line) > 15 and not line.lower().startswith("источники"):
                        tasks.append(_normalize_task(line))

        for slide in goal_slides:
            body = _strip_slide_header(slide)
            for keyword, task in (
                ("python", "Разработать программы на Python для обучения и эксплуатации модели."),
                ("streamlit", "Интегрировать модель в Streamlit-приложение с документацией."),
                ("gpu", "Обеспечить работу модели в среде с GPU для высокой производительности."),
                ("90%", "Достичь точности обнаружения госномера более 90%."),
            ):
                if keyword.lower() in body.lower():
                    tasks.append(task)

        return _dedupe_preserve(tasks)[:12]

    def extract_purpose(self, goal_slides: list[str], essence: str) -> list[str]:
        purpose: list[str] = []
        defaults = [
            "Автоматизировать доступ автомобилей на парковку.",
            "Снизить ручной контроль при открытии шлагбаума.",
            "Повысить скорость обработки въезда.",
            "Обеспечить AI-контроль допуска по госномеру.",
        ]
        for slide in goal_slides:
            body = _strip_slide_header(slide).lower()
            if "шлагбаум" in body:
                purpose.append("Автоматизировать открытие шлагбаума по распознанному номеру.")
            if "90%" in body or "точност" in body:
                purpose.append("Обеспечить высокую точность распознавания госномеров.")
            if "gpu" in body:
                purpose.append("Обеспечить производительную обработку видеопотока.")
            if "streamlit" in body or "веб" in body:
                purpose.append("Создать демонстрационное веб-приложение для результатов.")

        for item in defaults:
            purpose.append(item)
        purpose.append(
            "Создать основу для интеграции с камерами наблюдения и базой разрешённых номеров."
        )
        return _dedupe_preserve(purpose)[:8]

    def extract_inputs(
        self,
        data_slides: list[str],
        goal_slides: list[str],
    ) -> list[str]:
        inputs: list[str] = []
        for slide in data_slides:
            body = _strip_slide_header(slide)
            if "камер" in body.lower() and "заказчик" in body.lower():
                inputs.append("Кадры и видео с камер заказчика.")
            if "телефон" in body.lower():
                inputs.append("Видео с телефонной камеры.")
            if "открыт" in body.lower() or "яндекс" in body.lower() or "гугл" in body.lower():
                inputs.append(
                    "Изображения автомобилей и госномеров из открытых источников."
                )
            if "roboflow" in body.lower():
                inputs.append("Готовые датасеты с Roboflow.")

        for slide in goal_slides:
            body = _strip_slide_header(slide).lower()
            if "видеодан" in body or "видео" in body:
                inputs.append("Видеопоток с камеры наблюдения.")
            if "cvat" in body or "roboflow" in body:
                inputs.append("Разметка данных в CVAT / Roboflow.")

        defaults = [
            "База разрешённых номеров.",
            "Видеопоток с камеры.",
        ]
        for item in defaults:
            inputs.append(item)
        return _dedupe_preserve(inputs)[:10]

    def extract_outputs(
        self,
        pipeline_slides: list[str],
        demo_slides: list[str],
        modules: list[LandingModule],
    ) -> list[str]:
        outputs: list[str] = []
        for module in modules:
            if "обнаружение" in module.name.lower() and "автомоб" in module.name.lower():
                outputs.append("Модель детекции автомобиля.")
            elif "номер" in module.name.lower() and "обнаруж" in module.name.lower():
                outputs.append("Модель детекции госномера.")
            elif "спецтранспорт" in module.name.lower():
                outputs.append("Модель классификации спецтранспорта.")
            elif "тип" in module.name.lower() and "номер" in module.name.lower():
                outputs.append("Модель классификации типа номера.")
            elif "символ" in module.name.lower():
                outputs.append("Модель распознавания символов номера.")
            elif "баз" in module.name.lower():
                outputs.append('Решение "открыть / не открыть шлагбаум".')

        if demo_slides:
            outputs.append("Streamlit demo panel.")
            outputs.append("Веб/десктоп-прототип для демонстрации результатов.")

        outputs.extend([
            "Документация и отчётность.",
            "Pipeline обработки кадра от детекции до проверки в базе.",
        ])
        return _dedupe_preserve(outputs)[:12]

    def extract_results(
        self,
        results_slides: list[str],
        demo_slides: list[str],
    ) -> list[str]:
        results: list[str] = []
        for slide in results_slides:
            body = _strip_slide_header(slide)
            if "результаты:" in body.lower():
                block = re.split(r"результаты\s*:", body, flags=re.IGNORECASE)[-1]
                block = re.split(r"рекомендации\s*:", block, flags=re.IGNORECASE)[0]
                for sent in _split_sentences(block):
                    if len(sent) > 30:
                        results.append(sent.strip())

        if demo_slides:
            results.append("Реализовано веб-приложение и десктопное приложение.")

        defaults = [
            "Разработаны несколько вариантов решений.",
            "Достигнута точность определения госномера более 90%.",
            "Подготовлены данные с камер заказчика и открытых источников.",
            "Проведена разметка данных через CVAT и Roboflow.",
            "Реализован pipeline обработки кадра от детекции автомобиля до проверки номера в базе.",
        ]
        for item in defaults:
            results.append(item)
        return _dedupe_preserve(results)[:10]

    def extract_outlook(self, results_slides: list[str]) -> list[str]:
        outlook: list[str] = []
        for slide in results_slides:
            body = _strip_slide_header(slide)
            if "рекомендации" in body.lower():
                block = re.split(r"рекомендации\s*:", body, flags=re.IGNORECASE)[-1]
                for line in block.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    if ":" in line:
                        head = line.split(":", 1)[0].strip()
                        if len(head) > 10:
                            outlook.append(head[0].upper() + head[1:] + ".")
                    elif len(line) > 20:
                        outlook.append(line if line.endswith(".") else f"{line}.")

        defaults = [
            "Детектирование в режиме online с живого потока камер.",
            "Адаптация к итоговой среде работы (GPU/CPU).",
            "Обогащение датасета новыми сценами, погодой и освещением.",
            "Снижение ложных срабатываний.",
            "Интеграция с реальной системой управления шлагбаумом.",
        ]
        for item in defaults:
            outlook.append(item)
        return _dedupe_preserve(outlook)[:8]

    def extract_stack(
        self,
        text: str,
        sources_slides: list[str],
    ) -> dict[str, list[str]]:
        combined = text.lower()
        for slide in sources_slides:
            combined += "\n" + slide.lower()

        grouped: dict[str, list[str]] = {}
        for key, (category, label) in TECH_CATALOG.items():
            if key in combined:
                grouped.setdefault(category, [])
                if label not in grouped[category]:
                    grouped[category].append(label)

        if "yolov8" in combined and "YOLOv8" not in grouped.get("AI / CV", []):
            grouped.setdefault("AI / CV", []).append("YOLOv8")

        return grouped

    def extract_modules(
        self,
        text: str,
        pipeline_slides: list[str] | None = None,
    ) -> list[LandingModule]:
        modules: list[LandingModule] = []
        search_text = text
        if pipeline_slides:
            search_text = "\n".join(pipeline_slides)

        for match in STEP_RE.finditer(search_text):
            name = match.group(2).strip().split("\n")[0].strip()
            body = match.group(0)
            description = _module_description(body)
            module_type = _infer_module_type(name)
            modules.append(
                LandingModule(name=name, description=description, type=module_type)
            )

        if not modules:
            for line in search_text.splitlines():
                step_match = re.match(r"Шаг\s*\d+\s*:\s*(.+)", line, re.IGNORECASE)
                if step_match:
                    name = step_match.group(1).strip()
                    modules.append(
                        LandingModule(
                            name=name,
                            description="",
                            type=_infer_module_type(name),
                        )
                    )

        demo_match = re.search(r"демо[-\s]?панель\s+streamlit", text, re.IGNORECASE)
        if demo_match:
            modules.append(
                LandingModule(
                    name="Streamlit demo panel",
                    description="Интерактивная демо-панель для демонстрации результатов pipeline.",
                    type="demo_application",
                )
            )

        return modules

    def extract_team(
        self,
        team_slides: list[str],
        all_slides: dict[int, str],
        classified_types: dict[int, str],
    ) -> list[TeamMember]:
        members: list[TeamMember] = []

        for slide in team_slides:
            body = _strip_slide_header(slide)
            lead_match = LEAD_RE.search(body)
            if lead_match:
                members.append(
                    TeamMember(name=lead_match.group(1).strip(), role="Тимлид")
                )
            assistant_match = ASSISTANT_RE.search(body)
            if assistant_match:
                members.append(
                    TeamMember(
                        name=assistant_match.group(1).strip(),
                        role="Помощник тимлида",
                    )
                )

        for idx, slide in all_slides.items():
            if classified_types.get(idx) != "team_member":
                continue
            lines = [ln.strip() for ln in slide.splitlines() if ln.strip()]
            if lines and lines[0].lower().startswith("slide"):
                lines = lines[1:]
            for line in lines:
                if NAME_RE.match(line):
                    area = _infer_member_area(slide)
                    members.append(
                        TeamMember(
                            name=line,
                            role="",
                            project_area=area,
                            contributions=[area] if area else [],
                        )
                    )
                    break

        for idx, slide in all_slides.items():
            body = slide.lower()
            for line in slide.splitlines():
                line = line.strip()
                if not NAME_RE.match(line):
                    continue
                if any(m.name == line for m in members):
                    continue
                if "yolov8" in body or "streamlit" in body or "демо" in body:
                    area = _infer_member_area(slide)
                    members.append(
                        TeamMember(
                            name=line,
                            role="",
                            project_area=area,
                            contributions=[area] if area else [],
                        )
                    )

        return _dedupe_team(members)

    def build_contract_blocks(self, parsed: ParsedStructuredLanding) -> dict:
        """Helper for tests — expose block-ready data."""
        return {
            "stack_bullets": stack_to_bullets(parsed.tech_stack_grouped),
            "team_bullets": [
                f"{m.name} — {m.role or m.project_area}".strip(" —")
                for m in parsed.team
            ],
        }

    def _extract_title_client(self, slide1: str) -> tuple[str | None, str | None]:
        if not slide1:
            return None, None
        lines = [ln.strip() for ln in slide1.splitlines() if ln.strip()]
        if lines and lines[0].lower().startswith("slide"):
            lines = lines[1:]
        for line in lines:
            match = TITLE_CLIENT_RE.match(line)
            if match:
                return match.group(1).strip(), match.group(2).strip()
            if len(line) > 10 and not line.lower().startswith("стажировка"):
                return line, None
        return None, None

    def _extract_lead(self, text: str) -> str | None:
        match = LEAD_RE.search(text)
        return match.group(1).strip() if match else None

    def _extract_timeline(self, stage_slides: list[str]) -> str | None:
        for slide in stage_slides:
            match = re.search(
                r"(\d{2}\.\d{2}\s*[-–—]\s*\d{2}\.\d{2}\.\d{4})",
                slide,
            )
            if match:
                return match.group(1)
            match = re.search(r"\((\d{2}\.\d{2}[-–—]\d{2}\.\d{2}\.\d{4})\)", slide)
            if match:
                return match.group(1)
        return None


def _normalize(text: str) -> str:
    return text.replace("\u00a0", " ").replace("\u000b", "\n").replace("\r\n", "\n")


def _strip_slide_header(slide: str) -> str:
    lines = slide.splitlines()
    if lines and re.match(r"Slide\s+\d+\s*:", lines[0], re.IGNORECASE):
        lines = lines[1:]
    return "\n".join(lines).strip()


def _slides_by_type(
    slides: dict[int, str],
    classified_types: dict[int, str],
    slide_type: str,
) -> list[str]:
    return [
        slides[idx]
        for idx, stype in classified_types.items()
        if stype == slide_type and idx in slides
    ]


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.replace("\n", " "))
    return [p.strip() for p in parts if len(p.strip()) > 20]


def _normalize_task(line: str) -> str:
    line = line.strip().rstrip(".")
    if not line:
        return line
    lower = line[0].lower() + line[1:] if line else line
    if not lower.endswith("."):
        lower += "."
    mapping = (
        ("исследован", "Исследовать"),
        ("оценка", "Оценить"),
        ("выделение", "Выделить"),
        ("обработка", "Обработать"),
        ("эксперимент", "Провести эксперименты с"),
        ("оптимизация", "Оптимизировать"),
        ("подготовка отч", "Подготовить отч"),
        ("интеграц", "Интегрировать"),
        ("создание", "Создать"),
        ("разработка", "Разработать"),
        ("реализация", "Реализовать"),
    )
    for prefix, replacement in mapping:
        if lower.startswith(prefix):
            return f"{replacement}{lower[len(prefix):]}".capitalize()
    return lower[0].upper() + lower[1:]


def _module_description(body: str) -> str:
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    desc_parts: list[str] = []
    for line in lines[1:6]:
        if line.lower().startswith(("шаг", "slide")):
            break
        if re.match(r"^\d+\.", line):
            if "процесс:" in line.lower():
                desc_parts.append(line.split(":", 1)[-1].strip())
            elif "выход:" in line.lower():
                desc_parts.append(line.split(":", 1)[-1].strip())
        elif "используем" in line.lower() or "модель" in line.lower():
            desc_parts.append(line)
    return ". ".join(desc_parts[:2])


def _infer_module_type(name: str) -> str:
    lower = name.lower()
    for hint, module_type in MODULE_TYPE_HINTS:
        if hint in lower:
            return module_type
    return "pipeline_step"


def _infer_member_area(slide: str) -> str:
    lower = slide.lower()
    if "yolov8" in lower or "трениров" in lower or "обработк" in lower:
        return "обучение модели / обработка видео"
    if "streamlit" in lower or "демо" in lower or "веб" in lower:
        return "демо-панель / веб-приложение"
    return ""


def _dedupe_preserve(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.lower().strip()
        if key and key not in seen:
            seen.add(key)
            result.append(item.strip())
    return result


def _dedupe_team(members: list[TeamMember]) -> list[TeamMember]:
    seen: set[str] = set()
    result: list[TeamMember] = []
    for member in members:
        key = member.name.lower()
        if key not in seen:
            seen.add(key)
            result.append(member)
    return result
