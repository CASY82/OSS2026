from contracts.tool import ToolName
from infra.settings import Settings
from kg import KgEntityResolver, KnowledgeGraphTool
from kg.repository import KgRepository
from kg.service import GraphService
from nl2sql import Nl2SqlTool
from nl2sql.repository import SqlRepository
from nl2sql.service import SqlService
from vector import VectorSearchTool
from vector.repository import VectorRepository
from vector.service import SearchService
def build_registry(db,llm,cfg:Settings):
    kg_repo=KgRepository(db); resolver=KgEntityResolver(kg_repo)
    return {ToolName.VECTOR_SEARCH:VectorSearchTool(SearchService(VectorRepository(db),llm,cfg.TOP_K)),ToolName.NL2SQL:Nl2SqlTool(SqlService(SqlRepository(db),llm)),ToolName.KNOWLEDGE_GRAPH:KnowledgeGraphTool(GraphService(kg_repo,resolver))}
