from .schema_card import SCHEMA_CARD
def build_prompt(question: str, hint_tables: list[str]) -> str:
    hints = ", ".join(hint_tables) if hint_tables else "없음"
    return f"{SCHEMA_CARD}\n힌트 테이블: {hints}\n질문: {question}\nSQL:"
def append_correction(prompt: str, rejected: str, reason: str) -> str:
    return f"{prompt}\n이전 SQL: {rejected}\n거부 사유: {reason}\n규칙을 지켜 다시 SQL만 출력:"
