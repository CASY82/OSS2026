from typing import Any
from contracts.infra import Db

class KgRepository:
    def __init__(self, db: Db): self.db = db
    def exact_by_name(self, text: str) -> dict[str, Any] | None:
        rows = self.db.fetch_dicts("SELECT node_id, name, node_type FROM kg_nodes WHERE lower(name)=lower(%s) LIMIT 1", (text,)); return rows[0] if rows else None
    def by_id(self, node_id: str) -> dict[str, Any] | None:
        rows = self.db.fetch_dicts("SELECT node_id, name, node_type FROM kg_nodes WHERE node_id=%s", (node_id,)); return rows[0] if rows else None
    def trigram_top(self, text: str, k: int = 3) -> list[dict[str, Any]]:
        return self.db.fetch_dicts("SELECT node_id,name,node_type,similarity(name,%s) AS sim FROM kg_nodes ORDER BY sim DESC LIMIT %s", (text,k))
    def traverse(self, start_id: str, relations: list[str], target_types: list[str], max_hops: int) -> list[dict[str, Any]]:
        return self.db.fetch_dicts("""WITH RECURSIVE walk(node_id,path,depth) AS (
 SELECT %s::text, ARRAY[%s::text], 0 UNION ALL
 SELECT CASE WHEN e.source_id=w.node_id THEN e.target_id ELSE e.source_id END,
 w.path || CASE WHEN e.source_id=w.node_id THEN e.target_id ELSE e.source_id END,w.depth+1
 FROM walk w JOIN kg_edges e ON (e.source_id=w.node_id OR e.target_id=w.node_id)
 WHERE w.depth < %s AND e.relation_type=ANY(%s) AND NOT (CASE WHEN e.source_id=w.node_id THEN e.target_id ELSE e.source_id END)=ANY(w.path))
 SELECT n.node_id,n.name,n.node_type,w.path,w.depth FROM walk w JOIN kg_nodes n USING(node_id)
 WHERE w.depth>0 AND (cardinality(%s::text[],1) IS NULL OR n.node_type=ANY(%s)) ORDER BY w.depth,n.name""", (start_id,start_id,max_hops,relations,target_types,target_types))
