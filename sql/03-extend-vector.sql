CREATE TABLE IF NOT EXISTS document_chunks (
 chunk_id text PRIMARY KEY, doc_id text NOT NULL, doc_type text NOT NULL,
 section_title text NOT NULL, content text NOT NULL, metadata jsonb NOT NULL DEFAULT '{}',
 embedding vector(768) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON document_chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_chunks_content_trgm ON document_chunks USING gin (content gin_trgm_ops);
CREATE TABLE IF NOT EXISTS ingest_meta (pipeline text PRIMARY KEY, chunk_count int NOT NULL, embed_dim int NOT NULL, updated_at timestamptz NOT NULL DEFAULT now());
