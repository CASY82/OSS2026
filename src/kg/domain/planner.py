from dataclasses import dataclass
from .ontology import NodeType, ONTOLOGY, Relation

class PlanError(ValueError): pass
@dataclass(frozen=True)
class TraversalPlan:
    start_id: str; relations: tuple[Relation, ...]; target_types: tuple[NodeType, ...]; max_hops: int; aggregate: str | None = None

def plan(start_id: str, start_type: NodeType, relations: list[str], target_types: list[str], max_hops: int, aggregate: str | None = None) -> TraversalPlan:
    if not start_id: raise PlanError("start node is required")
    if not 1 <= max_hops <= 2: raise PlanError("max_hops must be between 1 and 2")
    try:
        rels = tuple(Relation(item) for item in relations)
        targets = tuple(NodeType(item) for item in target_types)
    except ValueError as exc: raise PlanError(str(exc)) from exc
    reachable = {start_type}
    for _ in range(max_hops):
        next_types = set(reachable)
        for rel in rels:
            spec = ONTOLOGY[rel]
            if spec.domain in reachable: next_types.add(spec.range_)
            if spec.range_ in reachable: next_types.add(spec.domain)
        reachable = next_types
    if targets and not set(targets) & reachable: raise PlanError("target type is unreachable with selected relations")
    return TraversalPlan(start_id, rels, targets, max_hops, aggregate)

def aggregate_unit(relation: Relation | None, mode: str | None) -> str:
    if relation is Relation.REPORTED_ISSUE: return "기술지원 이슈를 제기한 고유 고객사 수"
    if mode == "count": return "연결 개체 수"
    return "그래프 경로"
