from __future__ import annotations
from typing import Any
from contracts.infra import Db

class VectorRepository:
    def __init__(self, db: Db): self.db = db
    def vector_ranked(self, embedding: list[float], doc_type: str | None, limit: int = 20) -> list[str]:
        where = "WHERE doc_type = %s" if doc_type else ""
        params: tuple[Any, ...] = (doc_type, embedding, limit) if doc_type else (embedding, limit)
        rows = self.db.fetch(f"SELECT chunk_id FROM document_chunks {where} ORDER BY embedding <=> %s LIMIT %s", params)
        return [str(row[0]) for row in rows]
    def trigram_ranked(self, query: str, doc_type: str | None, limit: int = 20) -> list[str]:
        where = "AND doc_type = %s" if doc_type else ""
        params: tuple[Any, ...] = (query, doc_type, query, limit) if doc_type else (query, query, limit)
        rows = self.db.fetch(
            f"SELECT chunk_id FROM document_chunks WHERE content %% %s {where} "
            "ORDER BY similarity(content, %s) DESC LIMIT %s",
            params,
        )
        return [str(row[0]) for row in rows]
    def keyword_only(self, query: str, doc_type: str | None, limit: int) -> list[dict[str, Any]]:
        ids = self.trigram_ranked(query, doc_type, limit)
        return self.hydrate([(item, 0.0) for item in ids])
    def hydrate(self, ranked: list[tuple[str, float]]) -> list[dict[str, Any]]:
        if not ranked: return []
        ids = [item[0] for item in ranked]
        rows = self.db.fetch_dicts("SELECT chunk_id, doc_id, section_title, content FROM document_chunks WHERE chunk_id = ANY(%s)", (ids,))
        by_id = {str(row["chunk_id"]): row for row in rows}
        return [{**by_id[cid], "rrf_score": score} for cid, score in ranked if cid in by_id]
