from dataclasses import asdict
from infra.db import PostgresDb
from infra.llm import OllamaClient
from infra.settings import Settings
from router.registry import build_registry

def create_server():
    from mcp.server.fastmcp import FastMCP
    cfg=Settings.from_env(); registry=build_registry(PostgresDb(cfg.PG_DSN),OllamaClient(cfg.OLLAMA_URL),cfg); server=FastMCP("companyx")
    for tool in registry.values():
        def bind(current):
            @server.tool(name=current.name.value,description=f"CompanyX {current.name.value} tool")
            def call(**params): return asdict(current.run(**params))
            return call
        bind(tool)
    return server

def main(): create_server().run(transport="stdio")
if __name__=="__main__":main()
