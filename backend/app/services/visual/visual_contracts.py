"""Marker sets and scoring weights for visual source classification."""

from __future__ import annotations

from app.schemas.visual_evidence import VisualContentType

MARKER_SETS: dict[VisualContentType, tuple[str, ...]] = {
    VisualContentType.team_slide: (
        "команда проекта",
        "участники команды",
        "тимлид",
        "помощник тимлида",
        "разработчики",
        "команда управления",
        "состав команды",
        "роли в проекте",
    ),
    VisualContentType.tech_stack_slide: (
        "стек",
        "технологии",
        "tech stack",
        "используемые технологии",
        "технологический стек",
        "qdrant",
        "neo4j",
        "fastapi",
        "react",
        "postgresql",
        "docker",
        "bertopic",
        "streamlit",
        "yolov",
    ),
    VisualContentType.architecture_diagram: (
        "архитектура",
        "pipeline",
        "пайплайн",
        "схема",
        "поток данных",
        "data flow",
        "компоненты",
        "backend",
        "frontend",
        "database",
        "мультиагент",
        "агент ",
    ),
    VisualContentType.goals_slide: (
        "цель проекта",
        "цели проекта",
        "задачи",
        "проблема",
        "контекст",
        "цель:",
    ),
    VisualContentType.metrics_slide: (
        "метрики",
        "результаты",
        "accuracy",
        "precision",
        "recall",
        "latency",
        "uptime",
        "точность",
        "показател",
        "%",
    ),
    VisualContentType.roadmap_slide: (
        "roadmap",
        "дорожная карта",
        "направления развития",
        "перспектив",
        "планы по расширению",
        "этапы проекта",
    ),
    VisualContentType.table_or_matrix: (
        "таблица",
        "матрица",
        "сравнение",
        "matrix",
    ),
    VisualContentType.ui_screenshot: (
        "интерфейс",
        "dashboard",
        "экран",
        "demo",
        "streamlit",
        "web-приложен",
        "web приложен",
        "демо-панел",
        "панель",
    ),
}

VLM_HEAVY_TYPES: frozenset[VisualContentType] = frozenset(
    {
        VisualContentType.architecture_diagram,
        VisualContentType.ui_screenshot,
        VisualContentType.table_or_matrix,
        VisualContentType.metrics_slide,
    }
)

CHART_LIKE_MARKERS: tuple[str, ...] = (
    "график",
    "chart",
    "диаграмм",
    "визуализац",
)

DIAGRAM_HEAVY_MARKERS: tuple[str, ...] = (
    "схема",
    "pipeline",
    "пайплайн",
    "архитектур",
    "поток",
    "flow",
)

LOW_TEXT_THRESHOLD = 40
