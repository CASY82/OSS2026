"""OSS2026 router와 원본 NL2SQL 서비스 사이의 계약 어댑터."""

import time
import requests

from contracts.tool import AnswerBasis, Provenance, ToolName, ToolResult, ToolStatus, empty_result

from .service import answer


class Nl2SqlTool:
    name = ToolName.NL2SQL

    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "question": {"type": "string", "minLength": 1},
                "max_rows": {"type": "integer", "minimum": 1, "maximum": 1000},
            },
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
            requested_max_rows = params.get("max_rows", 100)
            max_rows = max(1, min(requested_max_rows, 1000)) if isinstance(requested_max_rows, int) else 100
            result = answer(question, max_rows=max_rows)
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            sql = str(result.get("sql") or "")
            if "error" in result:
                status_by_error = {
                    "guard_rejected": ToolStatus.GUARD_REJECTED,
                    "timeout": ToolStatus.TIMEOUT,
                    "upstream_error": ToolStatus.UPSTREAM_ERROR,
                }
                return ToolResult(
                    self.name,
                    status_by_error.get(result.get("error_type"), ToolStatus.UPSTREAM_ERROR),
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
        except (requests.Timeout, TimeoutError) as exc:
            return empty_result(self.name, ToolStatus.TIMEOUT, unit="조회 행", note=str(exc))
        except Exception as exc:
            return empty_result(self.name, ToolStatus.UPSTREAM_ERROR, unit="조회 행", note=str(exc))
