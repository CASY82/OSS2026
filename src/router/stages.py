from dataclasses import dataclass
from typing import Any, Literal
from contracts.resolver import EntityResolver, Resolution
from contracts.tool import ToolName
from .domain.rules import score_question
from .domain.tacc import PROFILE_BY_TOOL

@dataclass(frozen=True)
class RouteDecision:
    tool:ToolName; params:dict[str,Any]; confidence:float; stage:Literal["A","B","C"]; runner_up:tuple[ToolName,float]|None; tacc_profile:str; entities:list[Resolution]
class RuleRouter:
    DELTA=.15
    def __init__(self,resolver:EntityResolver,tau:float=.55):self.resolver,self.tau=resolver,tau
    def route(self,question:str)->RouteDecision|list[RouteDecision]:
        entities=self.resolver.find_all(question); scores=score_question(question,bool(entities)); best,second=scores[:2]
        stage="A" if best.score>=self.tau and best.score-second.score>=self.DELTA else "C"
        selected=scores[:1] if stage=="A" else scores
        return [self._decision(item.tool,question,item.score,stage,(second.tool,second.score),entities) for item in selected] if stage=="C" else self._decision(best.tool,question,best.score,"A",(second.tool,second.score),entities)
    def _decision(self,tool:ToolName,question:str,confidence:float,stage:Literal["A","B","C"],runner_up,entities)->RouteDecision:
        if tool is ToolName.VECTOR_SEARCH: params={"query":question}
        elif tool is ToolName.NL2SQL: params={"question":question,"max_rows":100}
        else:
            start=next((e.name for e in entities if e.name),question)
            relations=[]
            mapping={"소속":"BELONGS_TO","팀장":"HEAD_IS","사용":"USES","담당":"MANAGES_ACCOUNT","프로젝트":"HAS_PROJECT","이끄":"LEADS","이슈":"REPORTED_ISSUE"}
            relations=[rel for keyword,rel in mapping.items() if keyword in question] or ["USES","HAS_PROJECT"]
            targets=["project"] if "프로젝트" in question else []
            params={"start_entity":start,"relations":relations,"target_types":targets,"max_hops":2}
        return RouteDecision(tool,params,confidence,stage,runner_up,PROFILE_BY_TOOL[tool] if stage!="C" else "fallback_ambiguous",entities)
