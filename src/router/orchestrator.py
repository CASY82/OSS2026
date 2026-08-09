from __future__ import annotations
from contracts.infra import Llm, LlmError
from contracts.tool import Tool, ToolResult, ToolStatus
from .domain.composer import fallback_table
from .domain.tacc import compose_context
from .stages import RouteDecision, RuleRouter

class Orchestrator:
    def __init__(self,router:RuleRouter,registry:dict, llm:Llm|None=None):self.router,self.registry,self.llm=router,registry,llm
    def call_tool(self,decision:RouteDecision)->ToolResult:return self.registry[decision.tool].run(**decision.params)
    def answer(self,question:str)->str:
        decisions=self.router.route(question); decisions=decisions if isinstance(decisions,list) else [decisions]
        results=[self.call_tool(d) for d in decisions]
        ranked=sorted(zip(decisions,results),key=lambda pair:(pair[1].status not in (ToolStatus.OK,ToolStatus.EMPTY),-pair[1].answer_basis.row_count))
        decision,result=ranked[0]
        if self.llm:
            try:return self.llm.generate(f"질문: {question}\n{compose_context(result,decision.tacc_profile)}\n근거만 사용해 한국어로 답하세요.")
            except LlmError:pass
        return fallback_table(result)
