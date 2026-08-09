import time
from contracts.tool import AnswerBasis, Provenance, ToolName, ToolResult, ToolStatus, empty_result
from .service import GraphService
class KnowledgeGraphTool:
    name=ToolName.KNOWLEDGE_GRAPH
    def __init__(self,service:GraphService): self.service=service
    def input_schema(self)->dict:
        return {"type":"object","properties":{"start_entity":{"type":"string","minLength":1},"relations":{"type":"array","items":{"enum":["BELONGS_TO","HEAD_IS","USES","MANAGES_ACCOUNT","HAS_PROJECT","LEADS","REPORTED_ISSUE"]}},"target_types":{"type":"array","items":{"enum":["client","product","employee","project","department"]}},"max_hops":{"type":"integer","minimum":1,"maximum":2},"aggregate":{"type":["string","null"]}},"required":["start_entity","relations","target_types"],"additionalProperties":False}
    def health(self)->bool:return True
    def run(self,**params)->ToolResult:
        start=params.get("start_entity")
        if not isinstance(start,str) or not start.strip(): return empty_result(self.name,ToolStatus.ENTITY_NOT_FOUND,unit="그래프 경로",note="시작 개체가 비어 있습니다",candidates=["Client-A","Product-A1","영업팀"])
        began=time.perf_counter()
        try:
            out=self.service.traverse(start,params.get("relations") or [],params.get("target_types") or [],params.get("max_hops") or 2,params.get("aggregate"))
            columns=list(out.rows[0]) if out.rows else []
            rows=[[row.get(c) for c in columns] for row in out.rows]
            return ToolResult(self.name,out.status,AnswerBasis(columns,rows,len(rows),out.unit),Provenance(out.query,[str(row[0]) for row in rows if row],int((time.perf_counter()-began)*1000)),notes=[out.reason] if out.reason else [],candidates=out.candidates)
        except Exception as exc:return empty_result(self.name,ToolStatus.UPSTREAM_ERROR,unit="그래프 경로",note=str(exc))
