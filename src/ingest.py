from __future__ import annotations

import argparse
import json
from pathlib import Path
from zipfile import ZipFile

import httpx
import psycopg

from infra.settings import Settings
from vector.domain.chunker import split_by_h2
from vector.domain.enricher import enrich


def _documents(archive: ZipFile) -> list[dict[str, object]]:
    index = json.loads(archive.read("documents/index.json"))
    chunks: list[dict[str, object]] = []
    for doc in index:
        markdown = archive.read(f"documents/{doc['filename']}").decode()
        for position, section in enumerate(split_by_h2(markdown)):
            content = enrich(section, {
                "doc_id": doc["id"], "doc_type": doc["type"], "title": doc["title"],
            })
            chunks.append({
                "chunk_id": f"{doc['id']}:{position:02d}", "doc_id": doc["id"],
                "doc_type": doc["type"], "section_title": section.title,
                "content": content, "metadata": doc,
            })
    return chunks


def _embed(chunks: list[dict[str, object]], cfg: Settings) -> list[list[float]]:
    inputs = [f"search_document: {chunk['content']}" for chunk in chunks]
    response = httpx.post(
        f"{cfg.OLLAMA_URL.rstrip('/')}/api/embed",
        json={"model": cfg.EMBED_MODEL, "input": inputs}, timeout=600,
    )
    response.raise_for_status()
    embeddings = response.json()["embeddings"]
    if len(embeddings) != len(chunks) or any(len(vector) != 768 for vector in embeddings):
        raise RuntimeError("embedding contract violation: expected one 768d vector per chunk")
    return embeddings


def ingest(dataset: Path, cfg: Settings) -> dict[str, int]:
    with ZipFile(dataset) as archive:
        chunks = _documents(archive)
        nodes = json.loads(archive.read("graph/nodes.json"))
        edges = json.loads(archive.read("graph/edges.json"))
    if len(chunks) != 202 or len(nodes) != 133 or len(edges) != 354:
        raise RuntimeError("dataset cardinality contract violation")
    embeddings = _embed(chunks, cfg)
    with psycopg.connect(cfg.PG_DSN, autocommit=False) as conn:
        from pgvector.psycopg import register_vector
        register_vector(conn)
        with conn.cursor() as cur:
            for chunk, embedding in zip(chunks, embeddings):
                cur.execute(
                    """INSERT INTO document_chunks
                    (chunk_id,doc_id,doc_type,section_title,content,metadata,embedding)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (chunk_id) DO UPDATE SET content=EXCLUDED.content,
                    metadata=EXCLUDED.metadata,embedding=EXCLUDED.embedding""",
                    (chunk["chunk_id"],chunk["doc_id"],chunk["doc_type"],
                     chunk["section_title"],chunk["content"],json.dumps(chunk["metadata"]),embedding),
                )
            for node in nodes:
                cur.execute(
                    """INSERT INTO kg_nodes(node_id,node_type,name,properties)
                    VALUES(%s,%s,%s,%s) ON CONFLICT(node_id) DO UPDATE SET
                    node_type=EXCLUDED.node_type,name=EXCLUDED.name,properties=EXCLUDED.properties""",
                    (node["id"],node["type"],node["name"],json.dumps(node.get("properties",{}))),
                )
            for edge in edges:
                cur.execute(
                    """INSERT INTO kg_edges(source_id,target_id,relation_type,properties)
                    VALUES(%s,%s,%s,%s) ON CONFLICT(source_id,target_id,relation_type) DO UPDATE
                    SET properties=EXCLUDED.properties""",
                    (edge["source"],edge["target"],edge["relation"],json.dumps(edge.get("properties",{}))),
                )
            cur.execute(
                """INSERT INTO ingest_meta(pipeline,chunk_count,embed_dim)
                VALUES('companyx-v1',%s,768) ON CONFLICT(pipeline) DO UPDATE SET
                chunk_count=EXCLUDED.chunk_count,embed_dim=EXCLUDED.embed_dim,updated_at=now()""",
                (len(chunks),),
            )
        conn.commit()
    return {"chunks":len(chunks),"nodes":len(nodes),"edges":len(edges)}


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("dataset",type=Path)
    args=parser.parse_args()
    print(json.dumps(ingest(args.dataset,Settings.from_env()),ensure_ascii=False))

if __name__ == "__main__": main()
