from dataclasses import asdict
from contracts.tool import ToolName, ToolResult
TACC_PROFILES={"structured_aggregate":{"K","A"},"document_semantic":{"K","A","G"},"relation_traversal":{"K","A"},"fallback_ambiguous":{"K","A","D","G"}}
PROFILE_BY_TOOL={ToolName.NL2SQL:"structured_aggregate",ToolName.VECTOR_SEARCH:"document_semantic",ToolName.KNOWLEDGE_GRAPH:"relation_traversal"}
GUIDELINES={ToolName.VECTOR_SEARCH:"검색 본문에만 근거하고 출처를 표시하세요.",ToolName.NL2SQL:"조회 결과와 단위를 함께 답하세요.",ToolName.KNOWLEDGE_GRAPH:"그래프 경로의 방향과 단위를 명시하세요."}
def compose_context(result:ToolResult,profile_name:str)->str:
    profile=TACC_PROFILES[profile_name]; parts=[]
    if "K" in profile: parts.append(f"[K] columns={result.answer_basis.columns}\nrows={result.answer_basis.rows}\nunit={result.answer_basis.unit}")
    if "A" in profile: parts.append(f"[A] {', '.join(a.tool.value+': '+a.reason for a in result.candidate_actions) or 'none'}")
    if "D" in profile: parts.append(f"[D] {asdict(result.provenance)}")
    if "G" in profile: parts.append(f"[G] {GUIDELINES[result.tool]}")
    return "\n\n".join(parts)
