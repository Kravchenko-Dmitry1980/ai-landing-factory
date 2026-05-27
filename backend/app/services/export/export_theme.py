"""Export theme identifiers for HTML export."""

from __future__ import annotations

from enum import StrEnum


class ExportTheme(StrEnum):
    ENTERPRISE_DARK = "enterprise_dark"
    UNIVERSITY_PLATFORM = "university_platform"

    @classmethod
    def from_query(cls, theme: str | None) -> ExportTheme:
        if theme in (cls.UNIVERSITY_PLATFORM, None, ""):
            return cls.UNIVERSITY_PLATFORM
        if theme == cls.ENTERPRISE_DARK:
            return cls.ENTERPRISE_DARK
        return cls.UNIVERSITY_PLATFORM
