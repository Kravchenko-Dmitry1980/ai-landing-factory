"""Published landings: one row per project in SQLite, the HTML of every version on disk.

The address (slug) is fixed at the first publication, so links keep working after
the title changes or the landing is withdrawn and published again.
"""

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

from app.models.domain import utc_now
from app.repositories.atomic_io import write_text_atomic
from app.repositories.database import Database, iso
from app.services.library.metadata import PublicationMeta, slugify

PublicationStatus = Literal["published", "withdrawn"]


@dataclass(frozen=True)
class Publication:
    project_id: str
    slug: str
    status: PublicationStatus
    version: int
    contract_version: int
    theme: str
    title: str
    summary: str
    customer: str
    lead: str
    people: list[str]
    first_published_at: datetime
    published_at: datetime
    published_by_name: str | None
    withdrawn_at: datetime | None
    body_text: str = field(default="", repr=False)


_SELECT = """
    SELECT p.*, u.name AS published_by_name
    FROM publications p LEFT JOIN users u ON u.id = p.published_by
"""


def _publication(row: sqlite3.Row) -> Publication:
    return Publication(
        project_id=row["project_id"],
        slug=row["slug"],
        status=row["status"],
        version=row["version"],
        contract_version=row["contract_version"],
        theme=row["theme"],
        title=row["title"],
        summary=row["summary"],
        customer=row["customer"],
        lead=row["lead"],
        people=json.loads(row["people"]),
        first_published_at=datetime.fromisoformat(row["first_published_at"]),
        published_at=datetime.fromisoformat(row["published_at"]),
        published_by_name=row["published_by_name"],
        withdrawn_at=datetime.fromisoformat(row["withdrawn_at"]) if row["withdrawn_at"] else None,
        body_text=row["body_text"],
    )


class PublicationRepository:
    def __init__(self, db: Database, published_dir: Path) -> None:
        self._db = db
        self._dir = published_dir

    def _html_path(self, project_id: str, version: int) -> Path:
        return self._dir / project_id / f"v{version}.html"

    def get_for_project(self, project_id: str) -> Publication | None:
        with self._db.read() as conn:
            row = conn.execute(f"{_SELECT} WHERE p.project_id = ?", (project_id,)).fetchone()
        return _publication(row) if row else None

    def get_published(self, slug: str) -> Publication | None:
        with self._db.read() as conn:
            row = conn.execute(f"{_SELECT} WHERE p.slug = ? AND p.status = 'published'", (slug,)).fetchone()
        return _publication(row) if row else None

    def list_all(self) -> list[Publication]:
        """Every project ever published, withdrawn ones too: for the studio's project list."""
        with self._db.read() as conn:
            rows = conn.execute(_SELECT).fetchall()
        return [_publication(row) for row in rows]

    def list_published(self) -> list[Publication]:
        with self._db.read() as conn:
            rows = conn.execute(f"{_SELECT} WHERE p.status = 'published' ORDER BY p.published_at DESC").fetchall()
        return [_publication(row) for row in rows]

    def read_html(self, publication: Publication) -> str:
        return self._html_path(publication.project_id, publication.version).read_text(encoding="utf-8")

    def publish(
        self,
        project_id: str,
        *,
        html: str,
        theme: str,
        contract_version: int,
        meta: PublicationMeta,
        user_id: str | None,
    ) -> Publication:
        now = iso(utc_now())
        with self._db.write() as conn:
            existing = conn.execute(
                "SELECT slug, version FROM publications WHERE project_id = ?", (project_id,)
            ).fetchone()
            version = existing["version"] + 1 if existing else 1
            slug = existing["slug"] if existing else _free_slug(conn, slugify(meta.title))
            # Written inside the transaction: if the file cannot be saved, the row does not change.
            write_text_atomic(self._html_path(project_id, version), html)
            values = {
                "status": "published",
                "version": version,
                "contract_version": contract_version,
                "theme": theme,
                "title": meta.title,
                "summary": meta.summary,
                "customer": meta.customer,
                "lead": meta.lead,
                "people": json.dumps(meta.people, ensure_ascii=False),
                "body_text": meta.body_text,
                "published_at": now,
                "published_by": user_id,
                "withdrawn_at": None,
            }
            if existing:
                assignments = ", ".join(f"{column} = :{column}" for column in values)
                conn.execute(
                    f"UPDATE publications SET {assignments} WHERE project_id = :project_id",
                    {**values, "project_id": project_id},
                )
            else:
                row = {**values, "project_id": project_id, "slug": slug, "first_published_at": now}
                columns = ", ".join(row)
                conn.execute(
                    f"INSERT INTO publications ({columns}) VALUES ({', '.join(':' + c for c in row)})",
                    row,
                )
            return _publication(conn.execute(f"{_SELECT} WHERE p.project_id = ?", (project_id,)).fetchone())

    def withdraw(self, project_id: str) -> Publication | None:
        """Hides the landing from the library and its address; the files stay for a later re-publication."""
        with self._db.write() as conn:
            conn.execute(
                "UPDATE publications SET status = 'withdrawn', withdrawn_at = ? WHERE project_id = ? AND status = 'published'",
                (iso(utc_now()), project_id),
            )
            row = conn.execute(f"{_SELECT} WHERE p.project_id = ?", (project_id,)).fetchone()
        return _publication(row) if row else None


def _free_slug(conn: sqlite3.Connection, base: str) -> str:
    taken = {
        row[0]
        for row in conn.execute(
            "SELECT slug FROM publications WHERE slug = ? OR slug LIKE ?", (base, f"{base}-%")
        ).fetchall()
    }
    if base not in taken:
        return base
    suffix = 2
    while f"{base}-{suffix}" in taken:
        suffix += 1
    return f"{base}-{suffix}"
