"""Semantic checks for SQL generated from glossary-backed business terms."""

from dataclasses import dataclass
import re


SCHEMA_COLUMNS = {
    "products": {"id", "name", "category", "price_monthly", "status"},
    "contracts": {"id", "client_id", "product_id", "amount", "status"},
    "employees": {"id", "name", "dept_id", "salary"},
    "sales": {"id", "client_id", "product_id", "amount", "quarter", "category", "region"},
}


@dataclass(frozen=True)
class ColumnMapping:
    name: str
    aliases: tuple[str, ...]
    canonical_column: str
    forbidden_columns: tuple[str, ...] = ()


# schema_context.GLOSSARY의 핵심 수치 용어를 코드가 검증 가능한 형태로 옮긴다.
COLUMN_MAPPINGS = (
    ColumnMapping(
        name="매출",
        aliases=("매출", "매출액"),
        canonical_column="sales.amount",
        forbidden_columns=("products.price_monthly", "contracts.amount"),
    ),
    ColumnMapping(
        name="계약금액",
        aliases=("계약금액", "계약 금액"),
        canonical_column="contracts.amount",
        forbidden_columns=("sales.amount", "products.price_monthly"),
    ),
    ColumnMapping(
        name="연봉",
        aliases=("연봉",),
        canonical_column="employees.salary",
        forbidden_columns=("sales.amount", "contracts.amount", "products.price_monthly"),
    ),
)


_TABLE_REF_RE = re.compile(
    r"\b(?:FROM|JOIN)\s+([a-z_][a-z0-9_]*)(?:\s+(?:AS\s+)?([a-z_][a-z0-9_]*))?",
    re.IGNORECASE,
)
_QUALIFIED_COLUMN_RE = re.compile(r"\b([a-z_][a-z0-9_]*)\.([a-z_][a-z0-9_]*)\b", re.IGNORECASE)
_IDENTIFIER_RE = re.compile(r"\b[a-z_][a-z0-9_]*\b", re.IGNORECASE)
_SQL_KEYWORDS = {
    "select",
    "from",
    "join",
    "where",
    "group",
    "by",
    "order",
    "limit",
    "on",
    "as",
    "and",
    "or",
    "sum",
    "avg",
    "count",
    "desc",
    "asc",
}


def check(question: str, sql: str) -> tuple[bool, str | None]:
    """Return False when SQL contradicts a glossary-derived column mapping."""
    if re.search(r"\bquarter\s*=\s*'\d{4}-q(?:\*|)'", sql, re.IGNORECASE):
        return False, "의미 오류: 연도 전체를 불완전한 quarter 값으로 필터링할 수 없습니다. 날짜 범위를 사용하세요."

    matched = [
        mapping
        for mapping in COLUMN_MAPPINGS
        if any(alias in question for alias in mapping.aliases)
    ]
    if not matched:
        return True, None

    context = _SqlContext(sql)
    for mapping in matched:
        for forbidden_column in mapping.forbidden_columns:
            if context.uses_column(forbidden_column):
                return False, _error(mapping, f"{forbidden_column}는 해당 용어의 기준 컬럼이 아닙니다.")

        revenue_count = (
            mapping.name == "매출"
            and any(term in question for term in ("건수", "몇 건", "개수"))
            and "sales" in context.tables
            and "count" in context.identifiers
        )
        if not revenue_count and not context.uses_column(mapping.canonical_column):
            return False, _error(mapping, "생성 SQL에 기준 컬럼이 없습니다.")

    return True, None


def _error(mapping: ColumnMapping, detail: str) -> str:
    return (
        f"의미 오류: '{mapping.name}'은 {mapping.canonical_column} 기준으로 해석해야 합니다. "
        f"{detail}"
    )


class _SqlContext:
    def __init__(self, sql: str) -> None:
        self.sql = sql.lower()
        self.alias_to_table = self._extract_aliases()
        self.tables = set(self.alias_to_table.values())
        self.qualified_columns = self._extract_qualified_columns()
        self.identifiers = set(_IDENTIFIER_RE.findall(self.sql))

    def uses_column(self, canonical_column: str) -> bool:
        table, column = canonical_column.lower().split(".", 1)
        if canonical_column.lower() in self.qualified_columns:
            return True
        if table not in self.tables or column not in self.identifiers:
            return False

        candidate_tables = [
            table_name
            for table_name in self.tables
            if column in SCHEMA_COLUMNS.get(table_name, set())
        ]
        return set(candidate_tables) == {table}

    def _extract_aliases(self) -> dict[str, str]:
        aliases = {}
        for table, alias in _TABLE_REF_RE.findall(self.sql):
            table = table.lower()
            if table not in SCHEMA_COLUMNS:
                continue
            aliases[table] = table
            if alias:
                alias = alias.lower()
                if alias not in _SQL_KEYWORDS:
                    aliases[alias] = table
        return aliases

    def _extract_qualified_columns(self) -> set[str]:
        columns = set()
        for qualifier, column in _QUALIFIED_COLUMN_RE.findall(self.sql):
            table = self.alias_to_table.get(qualifier.lower())
            if table and column.lower() in SCHEMA_COLUMNS.get(table, set()):
                columns.add(f"{table}.{column.lower()}")
        return columns
