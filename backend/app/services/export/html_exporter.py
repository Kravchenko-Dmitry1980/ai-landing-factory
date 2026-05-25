from html import escape
from uuid import UUID

from app.repositories.contract_repository import ContractRepository


class HtmlExporter:
    def __init__(self, repository: ContractRepository) -> None:
        self._repo = repository

    async def to_html(self, project_id: UUID) -> str:
        landing = await self._repo.get_landing(project_id)
        if not landing:
            return "<html><body><p>Landing not generated yet.</p></body></html>"

        sections = []
        for block in landing.blocks:
            bullets = "".join(f"<li>{escape(b)}</li>" for b in block.bullets)
            list_html = f"<ul>{bullets}</ul>" if bullets else ""
            body = f"<p>{escape(block.body)}</p>" if block.body else ""
            sections.append(
                f"<section id='{escape(block.key)}'>"
                f"<h2>{escape(block.title)}</h2>{body}{list_html}</section>"
            )

        return (
            "<!DOCTYPE html><html lang='ru'><head>"
            "<meta charset='utf-8'><title>Project Landing</title>"
            "<style>body{font-family:system-ui;max-width:720px;margin:2rem auto;"
            "padding:0 1rem}section{margin:2rem 0}</style></head><body>"
            + "".join(sections)
            + "</body></html>"
        )
