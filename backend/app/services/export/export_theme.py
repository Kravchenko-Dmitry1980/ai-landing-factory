"""Export theme identifiers for HTML export."""

from __future__ import annotations

from enum import StrEnum


class ExportTheme(StrEnum):
    ENTERPRISE_DARK = "enterprise_dark"
    UNIVERSITY_PLATFORM = "university_platform"

    @classmethod
    def from_query(cls, theme: str | None) -> ExportTheme:
        if theme == cls.UNIVERSITY_PLATFORM:
            return cls.UNIVERSITY_PLATFORM
        return cls.ENTERPRISE_DARK
