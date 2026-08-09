"""Run inside the application container to verify MCP stdio list/call."""
import anyio
import json
import os
from mcp.client import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def main() -> None:
    params = StdioServerParameters(
        command="python", args=["-m", "adapters.mcp_sdk_server"], env=dict(os.environ),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
            names = sorted(tool.name for tool in listed.tools)
            assert names == ["knowledge_graph", "nl2sql", "vector_search"], names
            called = await session.call_tool("knowledge_graph", {
                "start_entity":"Client-A", "relations":["USES"],
                "target_types":["product"], "max_hops":1,
            })
            assert not called.is_error, called
            payload = called.structured_content or json.loads(called.content[0].text)
            assert payload.get("status") == "ok", payload
            assert payload.get("answer_basis", {}).get("row_count") == 2, payload
            print({"tools":names, "knowledge_graph_call":"ok"})


if __name__ == "__main__":
    anyio.run(main)
