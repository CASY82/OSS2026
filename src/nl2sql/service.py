from dataclasses import dataclass, field
from contracts.infra import DbQueryError, DbTimeout, DbUnavailable, Llm, LlmError
from contracts.tool import ToolStatus
from .domain.guard import extract_limit, guard, infer_unit
from .domain.normalizer import normalize_korean_enums
from .domain.prompt import append_correction, build_prompt
from .repository import SqlRepository

@dataclass(frozen=True)
class SqlOutcome:
    status: ToolStatus
    rows: list[list[object]] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    sql: str = ""
    unit: str = "조회 행"
    requested_limit: int | None = None
    reason: str | None = None

class SqlService:
    MAX_RETRY = 1
    def __init__(self, repo: SqlRepository, llm: Llm): self.repo, self.llm = repo, llm
    def answer(self, question: str, hint_tables: list[str], max_rows: int) -> SqlOutcome:
        prompt = build_prompt(normalize_korean_enums(question), hint_tables)
        for attempt in range(self.MAX_RETRY + 1):
            try: raw = self.llm.generate(prompt, stop=[";\n\n"], max_tokens=300)
            except LlmError as exc: return SqlOutcome(ToolStatus.UPSTREAM_ERROR, reason=str(exc))
            checked = guard(raw, max_rows)
            if not checked.ok:
                if attempt < self.MAX_RETRY:
                    prompt = append_correction(prompt, raw, checked.reason or "guard rejected"); continue
                return SqlOutcome(ToolStatus.GUARD_REJECTED, reason=checked.reason)
            try: rows, columns = self.repo.execute(checked.sql or "")
            except DbTimeout: return SqlOutcome(ToolStatus.TIMEOUT, sql=checked.sql or "")
            except (DbQueryError, DbUnavailable) as exc:
                if attempt < self.MAX_RETRY:
                    prompt = append_correction(prompt, checked.sql or "", str(exc)); continue
                return SqlOutcome(ToolStatus.UPSTREAM_ERROR, sql=checked.sql or "", reason=str(exc))
            requested = extract_limit(question)
            return SqlOutcome(ToolStatus.OK if rows else ToolStatus.EMPTY, rows, columns, checked.sql or "", infer_unit(checked.sql or ""), requested)
        return SqlOutcome(ToolStatus.UPSTREAM_ERROR, reason="unexpected retry exhaustion")
