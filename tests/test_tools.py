import pytest
from contracts.tool import ToolResult,ToolStatus
from kg.adapter import KnowledgeGraphTool
from kg.repository import KgRepository
from kg.resolver import KgEntityResolver
from kg.service import GraphService
from nl2sql.adapter import Nl2SqlTool
from nl2sql.repository import SqlRepository
from nl2sql.service import SqlService
from vector.adapter import VectorSearchTool
from vector.repository import VectorRepository
from vector.service import SearchService
from .fakes import FakeDb,FakeLlm

def tools():
    db=FakeDb([]);llm=FakeLlm();kg_repo=KgRepository(db)
    return [VectorSearchTool(SearchService(VectorRepository(db),llm)),Nl2SqlTool(SqlService(SqlRepository(db),llm)),KnowledgeGraphTool(GraphService(kg_repo,KgEntityResolver(kg_repo)))]
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
def test_nl2sql_self_corrects():
    llm=FakeLlm(["DROP TABLE clients","SELECT id FROM clients"])
    result=Nl2SqlTool(SqlService(SqlRepository(FakeDb([{"id":"client-a"}])),llm)).run(question="고객 목록")
    assert result.status is ToolStatus.OK
