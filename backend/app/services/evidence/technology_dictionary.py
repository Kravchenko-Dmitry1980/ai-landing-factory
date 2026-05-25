"""Known technology tokens for evidence extraction."""

from __future__ import annotations

TECHNOLOGY_ENTRIES: dict[str, tuple[str, str]] = {
    "yolov8": ("AI / ML / CV", "YOLOv8"),
    "yolo": ("AI / ML / CV", "YOLO"),
    "opencv": ("AI / ML / CV", "OpenCV"),
    "computer vision": ("AI / ML / CV", "Computer Vision"),
    "ocr": ("AI / ML / CV", "OCR"),
    "whisper": ("AI / ML / CV", "Whisper"),
    "faster-whisper": ("AI / ML / CV", "Faster-Whisper"),
    "pyannote": ("AI / ML / CV", "pyannote"),
    "bertopic": ("AI / ML / CV", "BERTopic"),
    "llm": ("AI / ML / CV", "LLM"),
    "rag": ("AI / ML / CV", "RAG"),
    "embeddings": ("AI / ML / CV", "Embeddings"),
    "qwen": ("AI / ML / CV", "Qwen"),
    "openai": ("AI / ML / CV", "OpenAI"),
    "gpt": ("AI / ML / CV", "GPT"),
    "faiss": ("Data / Search / Graph", "FAISS"),
    "qdrant": ("Data / Search / Graph", "Qdrant"),
    "neo4j": ("Data / Search / Graph", "Neo4j"),
    "postgresql": ("Data / Search / Graph", "PostgreSQL"),
    "postgres": ("Data / Search / Graph", "PostgreSQL"),
    "redis": ("Data / Search / Graph", "Redis"),
    "pgvector": ("Data / Search / Graph", "pgvector"),
    "elasticsearch": ("Data / Search / Graph", "Elasticsearch"),
    "python": ("Backend / App", "Python"),
    "fastapi": ("Backend / App", "FastAPI"),
    "django": ("Backend / App", "Django"),
    "streamlit": ("Backend / App", "Streamlit"),
    "flask": ("Backend / App", "Flask"),
    "websocket": ("Backend / App", "WebSocket"),
    "rest api": ("Backend / App", "REST API"),
    "react": ("Frontend", "React"),
    "next.js": ("Frontend", "Next.js"),
    "typescript": ("Frontend", "TypeScript"),
    "tailwind": ("Frontend", "Tailwind"),
    "html": ("Frontend", "HTML"),
    "css": ("Frontend", "CSS"),
    "cvat": ("Annotation / CV tools", "CVAT"),
    "roboflow": ("Annotation / CV tools", "Roboflow"),
    "supervision": ("Annotation / CV tools", "Supervision"),
    "google colab": ("Annotation / CV tools", "Google Colab"),
    "colab": ("Annotation / CV tools", "Google Colab"),
    "docker": ("Infra", "Docker"),
    "docker compose": ("Infra", "Docker Compose"),
    "gpu": ("Infra", "GPU"),
    "cuda": ("Infra", "CUDA"),
    "nginx": ("Infra", "Nginx"),
    "cloudflare tunnel": ("Infra", "Cloudflare Tunnel"),
    "spacy": ("AI / ML / CV", "spaCy"),
    "pyrogram": ("Backend / App", "Pyrogram"),
    "sentence transformers": ("AI / ML / CV", "Sentence Transformers"),
    "huey": ("Backend / App", "Huey"),
    "jwt": ("Backend / App", "JWT"),
    "bcrypt": ("Backend / App", "bcrypt"),
}


def extract_technologies(text: str) -> list[str]:
    """Return canonical technology names found in text."""
    normalized = text.lower().replace("\u00a0", " ")
    found: list[str] = []
    seen: set[str] = set()
    keys = sorted(TECHNOLOGY_ENTRIES.keys(), key=len, reverse=True)
    for key in keys:
        if key in normalized:
            canonical = TECHNOLOGY_ENTRIES[key][1]
            if canonical not in seen:
                seen.add(canonical)
                found.append(canonical)
    return found


def technologies_to_grouped(technologies: list[str]) -> dict[str, list[str]]:
    """Group canonical tech names by category."""
    grouped: dict[str, list[str]] = {}
    lower_map = {v[1].lower(): v[0] for v in TECHNOLOGY_ENTRIES.values()}
    for tech in technologies:
        category = "Other"
        for key, (cat, canonical) in TECHNOLOGY_ENTRIES.items():
            if canonical.lower() == tech.lower():
                category = cat
                break
        grouped.setdefault(category, [])
        if tech not in grouped[category]:
            grouped[category].append(tech)
    return grouped
