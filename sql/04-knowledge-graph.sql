CREATE TABLE IF NOT EXISTS kg_nodes (node_id text PRIMARY KEY,node_type varchar(20) NOT NULL,name text NOT NULL,properties jsonb NOT NULL DEFAULT '{}');
CREATE INDEX IF NOT EXISTS idx_kg_node_name_type ON kg_nodes(lower(name),node_type);
CREATE INDEX IF NOT EXISTS idx_kg_node_name_trgm ON kg_nodes USING gin(name gin_trgm_ops);
CREATE TABLE IF NOT EXISTS kg_edges (edge_id bigserial PRIMARY KEY,source_id text NOT NULL REFERENCES kg_nodes,target_id text NOT NULL REFERENCES kg_nodes,relation_type varchar(30) NOT NULL,properties jsonb NOT NULL DEFAULT '{}',UNIQUE(source_id,target_id,relation_type));
CREATE INDEX IF NOT EXISTS idx_kg_edges_source ON kg_edges(source_id,relation_type);
CREATE INDEX IF NOT EXISTS idx_kg_edges_target ON kg_edges(target_id,relation_type);
