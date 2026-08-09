from dataclasses import dataclass
from typing import Any
from contracts.infra import Llm, LlmError
from .domain.rrf import fuse
from .repository import VectorRepository

@dataclass(frozen=True)
class SearchOutcome:
    rows: list[dict[str, Any]]
    degraded: str | None = None
    note: str | None = None

class SearchService:
    def __init__(self, repo: VectorRepository, llm: Llm, top_k: int = 5):
        self.repo, self.llm, self.top_k = repo, llm, top_k
    def search(self, query: str, doc_type: str | None = None, top_k: int | None = None) -> SearchOutcome:
        k = max(1, min(top_k or self.top_k, 20))
        try:
            vector = self.llm.embed(query, kind="query")
        except LlmError:
            return SearchOutcome(self.repo.keyword_only(query, doc_type, k), "keyword_only")
        ranked = fuse(self.repo.vector_ranked(vector, doc_type), self.repo.trigram_ranked(query, doc_type), k)
        if not ranked and doc_type:
            retry = self.search(query, None, k)
            return SearchOutcome(retry.rows, retry.degraded, "문서 유형 필터를 해제하고 재검색했습니다.")
        return SearchOutcome(self.repo.hydrate(ranked))
