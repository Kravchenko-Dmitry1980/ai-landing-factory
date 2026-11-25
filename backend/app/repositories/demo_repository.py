"""One demo video per project: a studio draft and the copy the intern link plays.

The files live under data/demos and are not part of the downloaded HTML page.
"""

from __future__ import annotations

import hashlib
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.models.domain import utc_now
from app.repositories.atomic_io import write_bytes_atomic
from app.repositories.database import Database, iso
from app.schemas.demo import DemoInfo

logger = logging.getLogger(__name__)

_VIDEO = "draft.mp4"
_PUBLISHED_VIDEO = "published.mp4"


@dataclass(frozen=True)
class _DemoRow:
    project_id: str
    draft_sha256: str | None
    draft_poster_ext: str | None
    draft_updated_at: datetime | None
    published_sha256: str | None
    published_poster_ext: str | None
    published_version: int | None
    draft_mark: str | None
    published_mark: str | None


class DemoRepository:
    def __init__(self, db: Database, demos_dir: Path) -> None:
        self._db = db
        self._dir = demos_dir

    def info_for(self, project_id: str, *, status: str | None, version: int | None) -> DemoInfo:
        row = self._row(project_id)
        published = status == "published"
        link_sha = (
            row.published_sha256
            if row and published and row.published_version == version and row.published_sha256
            else None
        )
        draft_sha = row.draft_sha256 if row else None
        marks_differ = bool(row) and row.draft_mark != row.published_mark
        return DemoInfo(
            has_draft=draft_sha is not None,
            has_poster=bool(row and row.draft_poster_ext),
            on_link=link_sha is not None,
            pending=published and (draft_sha != link_sha or marks_differ),
            updated_at=row.draft_updated_at if row else None,
        )

    def project_ids_on_link(self) -> set[str]:
        with self._db.read() as conn:
            rows = conn.execute(
                """
                SELECT d.project_id FROM demos d
                JOIN publications p ON p.project_id = d.project_id
                WHERE p.status = 'published'
                  AND d.published_version = p.version
                  AND d.published_sha256 IS NOT NULL
                """
            ).fetchall()
        return {row[0] for row in rows}

    def has_published(self, project_id: str, version: int) -> bool:
        row = self._row(project_id)
        return bool(row and row.published_sha256 and row.published_version == version)

    def draft_video(self, project_id: str) -> Path | None:
        row = self._row(project_id)
        path = self._folder(project_id) / _VIDEO
        if row and row.draft_sha256 and path.is_file():
            return path
        return None

    def draft_poster(self, project_id: str) -> Path | None:
        row = self._row(project_id)
        if not row or not row.draft_poster_ext:
            return None
        path = self._folder(project_id) / f"draft-poster{row.draft_poster_ext}"
        return path if path.is_file() else None

    def published_video(self, project_id: str, version: int) -> Path | None:
        row = self._row(project_id)
        path = self._folder(project_id) / _PUBLISHED_VIDEO
        if row and row.published_sha256 and row.published_version == version and path.is_file():
            return path
        return None

    def published_poster(self, project_id: str, version: int) -> Path | None:
        row = self._row(project_id)
        if not row or not row.published_poster_ext or row.published_version != version:
            return None
        path = self._folder(project_id) / f"published-poster{row.published_poster_ext}"
        return path if path.is_file() else None

    def save_draft(self, project_id: str, video: bytes, poster: tuple[bytes, str] | None) -> None:
        """Stores a new draft. A missing poster keeps the previous cover."""
        folder = self._folder(project_id)
        folder.mkdir(parents=True, exist_ok=True)
        write_bytes_atomic(folder / _VIDEO, video)
        previous = self._row(project_id)
        poster_ext = previous.draft_poster_ext if previous else None
        if poster is not None:
            poster_bytes, poster_ext = poster
            self._remove_posters(folder, "draft-poster")
            write_bytes_atomic(folder / f"draft-poster{poster_ext}", poster_bytes)
        now = utc_now()
        self._upsert_draft(project_id, hashlib.sha256(video).hexdigest(), poster_ext, now, _mark())
        logger.info("Stored demo draft for %s (%d bytes)", project_id, len(video))

    def save_poster(self, project_id: str, poster: bytes, ext: str) -> None:
        row = self._row(project_id)
        if row is None or not row.draft_sha256:
            raise FileNotFoundError(project_id)
        folder = self._folder(project_id)
        self._remove_posters(folder, "draft-poster")
        write_bytes_atomic(folder / f"draft-poster{ext}", poster)
        with self._db.write() as conn:
            conn.execute(
                "UPDATE demos SET draft_poster_ext = ?, draft_updated_at = ?, draft_mark = ? WHERE project_id = ?",
                (ext, iso(utc_now()), _mark(), project_id),
            )

    def clear_poster(self, project_id: str) -> None:
        self._remove_posters(self._folder(project_id), "draft-poster")
        with self._db.write() as conn:
            conn.execute(
                "UPDATE demos SET draft_poster_ext = NULL, draft_mark = ? WHERE project_id = ?",
                (_mark(), project_id),
            )

    def clear_draft(self, project_id: str) -> None:
        folder = self._folder(project_id)
        self._remove(folder / _VIDEO)
        self._remove_posters(folder, "draft-poster")
        with self._db.write() as conn:
            conn.execute(
                """
                UPDATE demos
                SET draft_sha256 = NULL, draft_poster_ext = NULL, draft_updated_at = ?, draft_mark = ?
                WHERE project_id = ?
                """,
                (iso(utc_now()), _mark(), project_id),
            )
        logger.info("Removed demo draft for %s", project_id)

    def snapshot(self, project_id: str, version: int) -> None:
        """Copies the current draft onto this publication, or clears the link if there is no draft."""
        row = self._row(project_id)
        folder = self._folder(project_id)
        if row is None or not row.draft_sha256:
            if row is not None:
                self._clear_published(project_id, folder)
                with self._db.write() as conn:
                    conn.execute(
                        """
                        UPDATE demos
                        SET published_sha256 = NULL, published_poster_ext = NULL,
                            published_version = ?, published_mark = draft_mark
                        WHERE project_id = ?
                        """,
                        (version, project_id),
                    )
            return
        source = folder / _VIDEO
        if not source.is_file():
            raise FileNotFoundError(source)
        write_bytes_atomic(folder / _PUBLISHED_VIDEO, source.read_bytes())
        self._remove_posters(folder, "published-poster")
        if row.draft_poster_ext:
            poster = folder / f"draft-poster{row.draft_poster_ext}"
            if poster.is_file():
                write_bytes_atomic(folder / f"published-poster{row.draft_poster_ext}", poster.read_bytes())
        with self._db.write() as conn:
            conn.execute(
                """
                UPDATE demos
                SET published_sha256 = ?, published_poster_ext = ?, published_version = ?,
                    published_mark = draft_mark
                WHERE project_id = ?
                """,
                (row.draft_sha256, row.draft_poster_ext, version, project_id),
            )
        logger.info("Attached demo to publication %s v%d", project_id, version)

    def _clear_published(self, project_id: str, folder: Path) -> None:
        self._remove(folder / _PUBLISHED_VIDEO)
        self._remove_posters(folder, "published-poster")

    def _folder(self, project_id: str) -> Path:
        folder = (self._dir / project_id).resolve()
        root = self._dir.resolve()
        if folder != root and root not in folder.parents:
            raise ValueError(project_id)
        return folder

    def _row(self, project_id: str) -> _DemoRow | None:
        with self._db.read() as conn:
            row = conn.execute("SELECT * FROM demos WHERE project_id = ?", (project_id,)).fetchone()
        return _from_row(row) if row else None

    def _upsert_draft(
        self, project_id: str, sha256: str, poster_ext: str | None, updated_at: datetime, mark: str
    ) -> None:
        with self._db.write() as conn:
            conn.execute(
                """
                INSERT INTO demos (project_id, draft_sha256, draft_poster_ext, draft_updated_at, draft_mark)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (project_id) DO UPDATE SET
                    draft_sha256 = excluded.draft_sha256,
                    draft_poster_ext = excluded.draft_poster_ext,
                    draft_updated_at = excluded.draft_updated_at,
                    draft_mark = excluded.draft_mark
                """,
                (project_id, sha256, poster_ext, iso(updated_at), mark),
            )

    @staticmethod
    def _remove(path: Path) -> None:
        try:
            path.unlink()
        except FileNotFoundError:
            return

    @staticmethod
    def _remove_posters(folder: Path, stem: str) -> None:
        if not folder.is_dir():
            return
        for path in folder.glob(f"{stem}.*"):
            try:
                path.unlink()
            except FileNotFoundError:
                continue


def _from_row(row: sqlite3.Row) -> _DemoRow:
    updated = row["draft_updated_at"]
    return _DemoRow(
        project_id=row["project_id"],
        draft_sha256=row["draft_sha256"],
        draft_poster_ext=row["draft_poster_ext"],
        draft_updated_at=datetime.fromisoformat(updated) if updated else None,
        published_sha256=row["published_sha256"],
        published_poster_ext=row["published_poster_ext"],
        published_version=row["published_version"],
        draft_mark=row["draft_mark"],
        published_mark=row["published_mark"],
    )


def _mark() -> str:
    return iso(utc_now())
