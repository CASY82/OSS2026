from dataclasses import asdict

from contracts.tool import ToolName
from infra.db import PostgresDb
from infra.llm import OllamaClient
from infra.settings import Settings
from router.registry import build_registry


def create_server():
    from mcp.server.mcpserver import MCPServer

    cfg = Settings.from_env()
    llm = OllamaClient(cfg.OLLAMA_URL, generate_model=cfg.GENERATE_MODEL, embed_model=cfg.EMBED_MODEL)
    registry = build_registry(PostgresDb(cfg.PG_DSN), llm, cfg)
    server = MCPServer("companyx", version="0.1.0")

    @server.tool(name="vector_search", description="Search CompanyX documents with pgvector and trigram RRF")
    def vector_search(query: str, doc_type: str | None = None, top_k: int | None = None) -> dict:
        return asdict(registry[ToolName.VECTOR_SEARCH].run(query=query, doc_type=doc_type, top_k=top_k))

    @server.tool(name="nl2sql", description="Answer a structured CompanyX question using guarded read-only SQL")
    def nl2sql(question: str, hint_tables: list[str] | None = None, max_rows: int = 100) -> dict:
        return asdict(registry[ToolName.NL2SQL].run(question=question, hint_tables=hint_tables or [], max_rows=max_rows))

    @server.tool(name="knowledge_graph", description="Traverse the CompanyX ontology graph")
    def knowledge_graph(
        start_entity: str,
        relations: list[str],
        target_types: list[str],
        max_hops: int = 2,
        aggregate: str | None = None,
    ) -> dict:
        return asdict(registry[ToolName.KNOWLEDGE_GRAPH].run(
            start_entity=start_entity, relations=relations, target_types=target_types,
            max_hops=max_hops, aggregate=aggregate,
        ))

    return server


def main() -> None:
    create_server().run(transport="stdio")


if __name__ == "__main__":
    main()
