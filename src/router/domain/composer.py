from contracts.tool import ToolResult
def fallback_table(result:ToolResult)->str:
    if not result.answer_basis.rows: return result.notes[0] if result.notes else "조건에 맞는 결과가 없습니다."
    columns=result.answer_basis.columns; lines=[" | ".join(columns)," | ".join(["---"]*len(columns))]
    lines.extend(" | ".join(str(value) for value in row) for row in result.answer_basis.rows)
    lines.append(f"단위: {result.answer_basis.unit}")
    return "\n".join(lines)
