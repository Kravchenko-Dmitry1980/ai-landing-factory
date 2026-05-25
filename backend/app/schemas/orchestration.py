"""Orchestrated extraction agent schemas."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentRunStatus(str, Enum):
    OK = "ok"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"


class AgentFinding(BaseModel):
    agent_name: str
    field_name: str = ""
    value_preview: str = ""
    source_id: str = ""
    filename: str = ""
    location: str | None = None
    confidence: float = 0.0
    status: AgentRunStatus = AgentRunStatus.OK
    reason: str = ""


class AgentResult(BaseModel):
    agent_name: str
    status: AgentRunStatus = AgentRunStatus.OK
    findings: list[AgentFinding] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)


class OrchestrationTrace(BaseModel):
    source_count: int = 0
    agents_run: list[str] = Field(default_factory=list)
    results: list[AgentResult] = Field(default_factory=list)
    global_warnings: list[str] = Field(default_factory=list)
    missing_capabilities: list[str] = Field(default_factory=list)
    team_group_expansions: list[dict[str, Any]] = Field(default_factory=list)
