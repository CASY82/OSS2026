from nl2sql.guardrail import check, enforce_limit
from router.domain.rules import score_question
from contracts.tool import ToolName
from vector.domain.chunker import split_by_h2
from vector.domain.enricher import enrich
from vector.domain.rrf import fuse
from kg.domain.ontology import NodeType
from kg.domain.planner import PlanError,plan

def test_chunk_enrichment_and_rrf():
    sections=split_by_h2("## 원인 분석\n"+"장애 원인을 분석했습니다. "*8+"\n## 조치\n"+"재시작했습니다. "*10)
    assert "client=Client-A" in enrich(sections[0],{"client":"Client-A","product":"Product-C1"})
    assert fuse(["a","b"],["b","c"],2)[0][0]=="b"

def test_companyx_chunk_contract():
    from pathlib import Path
    import json, zipfile
    archive=Path("data/companyx-dataset-v1.0.zip")
    if not archive.exists(): return
    with zipfile.ZipFile(archive) as source:
        index=json.loads(source.read("documents/index.json"))
        count=sum(len(split_by_h2(source.read("documents/"+meta["filename"]).decode())) for meta in index)
    assert count==202
def test_sql_guard_negative_cases_and_limit():
    assert not check("SELECT * FROM clients; DROP TABLE clients")[0]
    assert not check("DROP TABLE clients")[0]
    assert enforce_limit("SELECT * FROM clients",5).endswith("LIMIT 5;")
    assert enforce_limit("SELECT * FROM clients LIMIT 100",5).endswith("LIMIT 5;")
    assert enforce_limit("SELECT * FROM clients LIMIT 3",5).endswith("LIMIT 3;")
def test_graph_plan_reachability():
    assert plan("client-a",NodeType.CLIENT,["USES","HAS_PROJECT"],["project"],2).max_hops==2
    try:plan("product-a",NodeType.PRODUCT,["BELONGS_TO"],["department"],1)
    except PlanError:return
    assert False,"unreachable plan must fail"
def test_router_signal_priority():
    assert score_question("기술 지원 이슈가 가장 많은 제품은?")[0].tool is ToolName.KNOWLEDGE_GRAPH
