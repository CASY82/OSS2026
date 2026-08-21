"""OSS2026 router와 원본 NL2SQL 서비스 사이의 계약 어댑터."""

import time

from contracts.tool import AnswerBasis, Provenance, ToolName, ToolResult, ToolStatus, empty_result

from .service import answer


class Nl2SqlTool:
    name = ToolName.NL2SQL

    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {"question": {"type": "string", "minLength": 1}},
            "required": ["question"],
            "additionalProperties": False,
        }

    def health(self) -> bool:
        return True

    def run(self, **params) -> ToolResult:
        question = params.get("question")
        if not isinstance(question, str) or not question.strip():
            return empty_result(self.name, ToolStatus.EMPTY, unit="조회 행", note="질문이 비어 있습니다.")

        started = time.perf_counter()
        try:
            result = answer(question)
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            sql = str(result.get("sql") or "")
            if "error" in result:
                return ToolResult(
                    self.name,
                    ToolStatus.UPSTREAM_ERROR,
                    AnswerBasis([], [], 0, "조회 행"),
                    Provenance(sql, [], elapsed_ms),
                    notes=[str(result["error"])],
                )

            columns = [str(column) for column in result.get("columns", [])]
            rows = [list(row) for row in result.get("rows", [])]
            status = ToolStatus.OK if rows else ToolStatus.EMPTY
            return ToolResult(
                self.name,
                status,
                AnswerBasis(columns, rows, len(rows), "조회 행"),
                Provenance(sql, [], elapsed_ms),
            )
        except Exception as exc:
            return empty_result(self.name, ToolStatus.UPSTREAM_ERROR, unit="조회 행", note=str(exc))
