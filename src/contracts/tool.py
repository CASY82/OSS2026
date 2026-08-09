from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable


class ToolName(StrEnum):
    VECTOR_SEARCH = "vector_search"
    NL2SQL = "nl2sql"
    KNOWLEDGE_GRAPH = "knowledge_graph"


class ToolStatus(StrEnum):
    OK = "ok"
    EMPTY = "empty"
    ENTITY_NOT_FOUND = "entity_not_found"
    GUARD_REJECTED = "guard_rejected"
    TIMEOUT = "timeout"
    UPSTREAM_ERROR = "upstream_error"


@dataclass(frozen=True)
class AnswerBasis:
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    unit: str
    requested_limit: int | None = None

    def __post_init__(self) -> None:
        if not self.unit.strip():
            raise ValueError("unit must not be empty")
        if self.row_count != len(self.rows):
            raise ValueError("row_count must equal len(rows)")


@dataclass(frozen=True)
class Provenance:
    query: str
    sources: list[str] = field(default_factory=list)
    elapsed_ms: int = 0
    degraded: str | None = None


@dataclass(frozen=True)
class CandidateAction:
    tool: ToolName
    reason: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolResult:
    tool: ToolName
    status: ToolStatus
    answer_basis: AnswerBasis
    provenance: Provenance
    candidate_actions: list[CandidateAction] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    candidates: list[str] = field(default_factory=list)


@runtime_checkable
class Tool(Protocol):
    name: ToolName
    def input_schema(self) -> dict[str, Any]: ...
    def run(self, **params: Any) -> ToolResult: ...
    def health(self) -> bool: ...


def empty_result(tool: ToolName, status: ToolStatus, *, unit: str, note: str = "", candidates: list[str] | None = None) -> ToolResult:
    return ToolResult(tool, status, AnswerBasis([], [], 0, unit), Provenance(""), notes=[note] if note else [], candidates=candidates or [])

