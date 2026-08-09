import time
from contracts.tool import AnswerBasis, Provenance, ToolName, ToolResult, ToolStatus, empty_result
from .service import SearchService

class VectorSearchTool:
    name = ToolName.VECTOR_SEARCH
    def __init__(self, service: SearchService): self.service = service
    def input_schema(self) -> dict:
        return {"type":"object", "properties":{"query":{"type":"string","minLength":1},"doc_type":{"type":["string","null"]},"top_k":{"type":"integer","minimum":1,"maximum":20}}, "required":["query"], "additionalProperties":False}
    def health(self) -> bool: return True
    def run(self, **params) -> ToolResult:
        started = time.perf_counter()
        query = params.get("query")
        if not isinstance(query, str) or not query.strip():
            return empty_result(self.name, ToolStatus.EMPTY, unit="문서 청크", note="검색어가 비어 있습니다.")
        try:
            result = self.service.search(query.strip(), params.get("doc_type"), params.get("top_k"))
            rows = [[r.get("doc_id"), r.get("section_title"), r.get("content"), r.get("rrf_score", 0)] for r in result.rows]
            return ToolResult(self.name, ToolStatus.OK if rows else ToolStatus.EMPTY, AnswerBasis(["doc_id","section_title","content","score"], rows, len(rows), "문서 청크", params.get("top_k")), Provenance(query, [str(r[0]) for r in rows], int((time.perf_counter()-started)*1000), result.degraded), notes=[result.note] if result.note else [])
        except Exception as exc:
            return empty_result(self.name, ToolStatus.UPSTREAM_ERROR, unit="문서 청크", note=str(exc))
