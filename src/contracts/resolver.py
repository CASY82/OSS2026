from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal, Protocol

@dataclass(frozen=True)
class Resolution:
    node_id: str | None
    name: str | None
    node_type: str | None
    confidence: float
    method: Literal["exact", "alias", "fuzzy", "not_found"]
    candidates: list[str] = field(default_factory=list)

class EntityResolver(Protocol):
    def resolve(self, text: str) -> Resolution: ...
    def find_all(self, question: str) -> list[Resolution]: ...
