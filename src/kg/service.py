from dataclasses import dataclass, field
from typing import Any
from contracts.resolver import EntityResolver
from contracts.tool import ToolStatus
from .domain.ontology import NodeType, Relation
from .domain.planner import PlanError, aggregate_unit, plan
from .repository import KgRepository

@dataclass(frozen=True)
class GraphOutcome:
    status: ToolStatus; rows: list[dict[str,Any]]=field(default_factory=list); unit: str="그래프 경로"; query: str=""; candidates: list[str]=field(default_factory=list); reason: str|None=None
class GraphService:
    def __init__(self, repo: KgRepository, resolver: EntityResolver): self.repo,self.resolver=repo,resolver
    def traverse(self,start_entity:str,relations:list[str],target_types:list[str],max_hops:int,aggregate:str|None=None)->GraphOutcome:
        resolved=self.resolver.resolve(start_entity)
        if resolved.node_id is None: return GraphOutcome(ToolStatus.ENTITY_NOT_FOUND,candidates=resolved.candidates,reason="개체를 찾지 못했습니다")
        try: traversal=plan(resolved.node_id,NodeType(resolved.node_type or "client"),relations,target_types,max_hops,aggregate)
        except (PlanError,ValueError) as exc: return GraphOutcome(ToolStatus.GUARD_REJECTED,reason=str(exc))
        rows=self.repo.traverse(traversal.start_id,[r.value for r in traversal.relations],[t.value for t in traversal.target_types],traversal.max_hops)
        unit=aggregate_unit(traversal.relations[-1] if traversal.relations else None,aggregate)
        return GraphOutcome(ToolStatus.OK if rows else ToolStatus.EMPTY,rows,unit,f"start={resolved.node_id}; relations={relations}; max_hops={max_hops}")
