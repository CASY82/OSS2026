import time
from contracts.tool import AnswerBasis, Provenance, ToolName, ToolResult, ToolStatus, empty_result
from .service import SqlService

class Nl2SqlTool:
    name = ToolName.NL2SQL
    def __init__(self, service: SqlService): self.service = service
    def input_schema(self) -> dict:
        return {"type":"object","properties":{"question":{"type":"string","minLength":1},"hint_tables":{"type":"array","items":{"type":"string"}},"max_rows":{"type":"integer","minimum":1,"maximum":1000}},"required":["question"],"additionalProperties":False}
    def health(self) -> bool: return True
    def run(self, **params) -> ToolResult:
        question = params.get("question")
        if not isinstance(question, str) or not question.strip(): return empty_result(self.name, ToolStatus.EMPTY, unit="조회 행", note="질문이 비어 있습니다.")
        started = time.perf_counter()
        try:
            out = self.service.answer(question, params.get("hint_tables") or [], params.get("max_rows") or 100)
            notes = [out.reason] if out.reason else []
            if out.requested_limit and len(out.rows) < out.requested_limit: notes.append(f"요청 {out.requested_limit}건 중 {len(out.rows)}건만 존재합니다.")
            return ToolResult(self.name, out.status, AnswerBasis(out.columns, out.rows, len(out.rows), out.unit, out.requested_limit), Provenance(out.sql, [], int((time.perf_counter()-started)*1000)), notes=notes)
        except Exception as exc: return empty_result(self.name, ToolStatus.UPSTREAM_ERROR, unit="조회 행", note=str(exc))
