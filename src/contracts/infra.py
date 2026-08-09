from __future__ import annotations
from typing import Any, ContextManager, Literal, Protocol, Sequence

class DbError(RuntimeError): pass
class DbTimeout(DbError): pass
class DbQueryError(DbError): pass
class DbUnavailable(DbError): pass
class LlmError(RuntimeError): pass
class LlmTimeout(LlmError): pass

class Db(Protocol):
    def fetch(self, sql: str, params: Sequence[Any] = ()) -> list[tuple[Any, ...]]: ...
    def fetch_dicts(self, sql: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]: ...

class Llm(Protocol):
    def embed(self, text: str, *, kind: Literal["document", "query"]) -> list[float]: ...
    def generate(self, prompt: str, *, stop: list[str] | None = None, max_tokens: int = 300, timeout_s: float = 30) -> str: ...

class Tracer(Protocol):
    def span(self, name: str, **attrs: Any) -> ContextManager[None]: ...

