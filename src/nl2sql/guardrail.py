"""쓰기 방지 가드레일: SELECT 전용 검증 + LIMIT 강제.

ADR 4번 결정(검증 계층) 중 쓰기 방지 가드레일 파트를 구현한다.
파서가 아닌 정규식 기반 검증이라는 한계를 인지하고 있으며, MVP 범위에서는
"신뢰할 수 없는 SQL을 실행하기 전 최소한의 방어선"으로만 사용한다.
"""

import re

FORBIDDEN_KEYWORDS = (
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "CREATE", "GRANT", "REVOKE", "MERGE", "EXECUTE", "CALL", "COPY",
)
_FORBIDDEN_RE = re.compile(
    r"\b(" + "|".join(FORBIDDEN_KEYWORDS) + r")\b", re.IGNORECASE
)
_LEADING_KEYWORD_RE = re.compile(r"^\s*(SELECT|WITH)\b", re.IGNORECASE)
_LIMIT_RE = re.compile(r"\bLIMIT\s+(\d+)\b", re.IGNORECASE)

DEFAULT_LIMIT = 200


def check(sql: str) -> tuple[bool, str | None]:
    """SELECT(또는 WITH ... SELECT) 단일 문장인지 검증한다.

    Returns:
        (True, None)         - 통과
        (False, reason)      - 차단, reason은 사용자/재시도 프롬프트에 노출 가능한 문구
    """
    stripped = sql.strip()
    if not stripped:
        return False, "빈 SQL은 실행할 수 없습니다."

    body = stripped[:-1] if stripped.endswith(";") else stripped
    if ";" in body:
        return False, "세미콜론으로 구분된 다중 SQL 문장은 허용되지 않습니다."

    if not _LEADING_KEYWORD_RE.match(body):
        return False, "SELECT (또는 WITH ... SELECT) 문만 허용됩니다."

    if _FORBIDDEN_RE.search(body):
        return False, "DML/DDL 키워드가 포함되어 있어 실행할 수 없습니다."

    return True, None


def enforce_limit(sql: str, default_limit: int = DEFAULT_LIMIT) -> str:
    """LIMIT 절을 강제하고 이미 존재하는 LIMIT도 상한 이하로 제한한다."""
    stripped = sql.strip()
    body = stripped[:-1] if stripped.endswith(";") else stripped
    limit = max(1, int(default_limit))

    matches = list(_LIMIT_RE.finditer(body))
    if not matches:
        body = f"{body} LIMIT {limit}"
    else:
        match = matches[-1]
        if int(match.group(1)) > limit:
            body = f"{body[:match.start(1)]}{limit}{body[match.end(1):]}"

    return f"{body};"
