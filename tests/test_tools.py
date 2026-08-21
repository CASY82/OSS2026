import pytest
from contracts.tool import ToolResult,ToolStatus
from kg.adapter import KnowledgeGraphTool
from kg.repository import KgRepository
from kg.resolver import KgEntityResolver
from kg.service import GraphService
from nl2sql.adapter import Nl2SqlTool
from vector.adapter import VectorSearchTool
from vector.repository import VectorRepository
from vector.service import SearchService
from .fakes import FakeDb,FakeLlm

def tools():
    db=FakeDb([]);llm=FakeLlm();kg_repo=KgRepository(db)
    return [VectorSearchTool(SearchService(VectorRepository(db),llm)),Nl2SqlTool(),KnowledgeGraphTool(GraphService(kg_repo,KgEntityResolver(kg_repo)))]
@pytest.mark.parametrize("tool",tools())
def test_contract_never_raises(tool):
    result=tool.run(unexpected=None)
    assert isinstance(result,ToolResult);assert result.status in ToolStatus;assert result.answer_basis.unit
    assert result.answer_basis.row_count==len(result.answer_basis.rows)
@pytest.mark.parametrize("tool",tools())
def test_json_schema(tool):
    try:
        import jsonschema
        jsonschema.Draft202012Validator.check_schema(tool.input_schema())
    except ImportError: pass
def test_vector_degrades_without_embedding():
    result=VectorSearchTool(SearchService(VectorRepository(FakeDb([])),FakeLlm(fail_embed=True))).run(query="장애 원인")
    assert result.provenance.degraded=="keyword_only"
def test_nl2sql_adapter_maps_original_result(monkeypatch):
    called={}
    def fake_answer(question,max_rows):
        called.update(question=question,max_rows=max_rows)
        return {"question":question,"sql":"SELECT id FROM clients LIMIT 25;","columns":["id"],"rows":[(1,)]}
    monkeypatch.setattr("nl2sql.adapter.answer",fake_answer)
    result=Nl2SqlTool().run(question="고객 목록",max_rows=25)
    assert result.status is ToolStatus.OK
    assert result.answer_basis.rows == [[1]]
    assert called == {"question":"고객 목록","max_rows":25}

def test_nl2sql_adapter_maps_guard_error(monkeypatch):
    monkeypatch.setattr("nl2sql.adapter.answer",lambda question,max_rows:{"question":question,"sql":"DROP TABLE clients","error":"DML/DDL","error_type":"guard_rejected"})
    result=Nl2SqlTool().run(question="고객 삭제")
    assert result.status is ToolStatus.GUARD_REJECTED
