"""NL2SQL 도구의 단일 진입점.

MCP 서버/라우터가 아직 정해지지 않았으므로, 이 모듈은 순수 함수
`answer(question)` 하나로 도구 전체를 캡슐화한다. 나중에 MCP 툴로 감쌀 때는
이 함수를 그대로 등록하면 된다.

흐름: 프롬프트 조립 -> LLM 생성 -> 가드레일 검증 -> 실행
      실패 시(가드레일 차단 또는 실행 에러) 에러 메시지를 LLM에 되먹여 1회 재시도.
      재시도도 실패하면 실패 결과를 반환한다(무한 재시도 금지, ADR 4번 결정).
"""

from . import executor, guardrail, llm_client, schema_context, semantic_validator


def generate_sql(question: str) -> str:
    """질문 하나에 대해 SQL을 1회 생성한다 (검증/실행 없음)."""
    prompt = f"{schema_context.build_system_context()}\n질문: {question}\nSQL:"
    return llm_client.generate_sql(prompt)


def _generate_sql_with_feedback(question: str, previous_sql: str, error_message: str) -> str:
    prompt = (
        f"{schema_context.build_system_context()}\n"
        "이전 시도에서 아래 SQL을 생성했으나 문제가 있었습니다.\n"
        f"실패한 SQL: {previous_sql}\n"
        f"오류 메시지: {error_message}\n"
        "위 오류를 반영하여 올바른 SQL을 다시 생성하세요.\n\n"
        f"질문: {question}\nSQL:"
    )
    return llm_client.generate_sql(prompt)


def _validate_and_run(question: str, sql: str, max_rows: int) -> dict:
    ok, reason = guardrail.check(sql)
    if not ok:
        return {"sql": sql, "error": reason, "error_type": "guard_rejected"}

    ok, reason = semantic_validator.check(question, sql)
    if not ok:
        return {"sql": sql, "error": reason, "error_type": "guard_rejected"}

    final_sql = guardrail.enforce_limit(sql, max_rows)
    result = executor.run(final_sql)
    if "error" in result and "error_type" not in result:
        result = {**result, "error_type": "upstream_error"}
    return {"sql": final_sql, **result}


def answer(question: str, max_rows: int = guardrail.DEFAULT_LIMIT) -> dict:
    """질문을 받아 SQL 생성 -> 검증 -> 실행까지 마친 결과를 반환한다.

    성공 시: {"question", "sql", "columns", "rows"}
    실패 시(1회 재시도 후에도 실패): {"question", "sql", "error"}
    """
    raw_sql = generate_sql(question)
    result = _validate_and_run(question, raw_sql, max_rows)
    if "error" not in result:
        return {"question": question, **result}

    retry_sql = _generate_sql_with_feedback(question, raw_sql, result["error"])
    retry_result = _validate_and_run(question, retry_sql, max_rows)
    return {"question": question, **retry_result}
