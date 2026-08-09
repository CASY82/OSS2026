from __future__ import annotations
from dataclasses import dataclass
import re
from contracts.tool import ToolName

SIGNALS = {
 ToolName.NL2SQL: (("총","합계","평균","개수","몇 개","얼마","상위","순서로","가장 높은","매출","계약","연봉","티켓"),3.0),
 ToolName.VECTOR_SEARCH: (("방법","알려줘","궁금해","어떻게","내용","보여줘","사례","원인","장애","설치","가이드","회의","제안서","매뉴얼","정책","취약점"),3.0),
 ToolName.KNOWLEDGE_GRAPH: (("담당","소속","사용 중인","이끄는","팀장","누구야","관련된","기술 지원 이슈"),3.5),
}
@dataclass(frozen=True)
class ScoredRoute:
    tool: ToolName; score: float; matched: tuple[str,...]
def score_question(question: str, has_entity: bool=False) -> list[ScoredRoute]:
    raw: dict[ToolName,tuple[float,list[str]]] = {}
    for tool,(terms,weight) in SIGNALS.items():
        hits=[term for term in terms if term.lower() in question.lower()]
        value=weight*len(hits)
        if tool is ToolName.NL2SQL and re.search(r"20\d{2}년|\d분기|20\d{2}-Q\d",question,re.I): value+=3.0; hits.append("기간")
        if tool is ToolName.KNOWLEDGE_GRAPH and has_entity: value+=2.0; hits.append("entity")
        if tool is ToolName.VECTOR_SEARCH and not has_entity: value+=1.0; hits.append("no_entity")
        raw[tool]=(value,hits)
    total=sum(value for value,_ in raw.values()) or 1.0
    return sorted((ScoredRoute(tool,value/total,tuple(hits)) for tool,(value,hits) in raw.items()),key=lambda item:(-item.score,item.tool.value))
