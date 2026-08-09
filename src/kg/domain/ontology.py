from dataclasses import dataclass
from enum import StrEnum

class NodeType(StrEnum):
    CLIENT="client"; PRODUCT="product"; EMPLOYEE="employee"; PROJECT="project"; DEPARTMENT="department"
class Relation(StrEnum):
    BELONGS_TO="BELONGS_TO"; HEAD_IS="HEAD_IS"; USES="USES"; MANAGES_ACCOUNT="MANAGES_ACCOUNT"; HAS_PROJECT="HAS_PROJECT"; LEADS="LEADS"; REPORTED_ISSUE="REPORTED_ISSUE"
@dataclass(frozen=True)
class RelationSpec:
    domain: NodeType; range_: NodeType; cardinality: str; sql_origin: str; expected: int; semantics: str
ONTOLOGY = {
 Relation.BELONGS_TO: RelationSpec(NodeType.EMPLOYEE,NodeType.DEPARTMENT,"N:1","employees(id, dept_id)",45,"소속 부서"),
 Relation.HEAD_IS: RelationSpec(NodeType.DEPARTMENT,NodeType.EMPLOYEE,"1:1","departments(id, head_id)",6,"부서장"),
 Relation.USES: RelationSpec(NodeType.CLIENT,NodeType.PRODUCT,"N:M","DISTINCT contracts(client_id, product_id)",61,"사용 제품"),
 Relation.MANAGES_ACCOUNT: RelationSpec(NodeType.EMPLOYEE,NodeType.CLIENT,"N:M","DISTINCT contracts(manager_id, client_id)",63,"담당 고객"),
 Relation.HAS_PROJECT: RelationSpec(NodeType.CLIENT,NodeType.PROJECT,"1:N","projects(client_id, id)",40,"고객사 프로젝트"),
 Relation.LEADS: RelationSpec(NodeType.EMPLOYEE,NodeType.PROJECT,"1:N","projects(manager_id, id)",40,"프로젝트 담당"),
 Relation.REPORTED_ISSUE: RelationSpec(NodeType.CLIENT,NodeType.PRODUCT,"N:M","DISTINCT support_tickets(client_id, product_id)",99,"이슈 고객사-제품 쌍"),
}
assert sum(spec.expected for spec in ONTOLOGY.values()) == 354
