DO $$ BEGIN CREATE ROLE mcp_reader LOGIN PASSWORD 'mcp_reader'; EXCEPTION WHEN duplicate_object THEN NULL; END $$;
GRANT CONNECT ON DATABASE companyx TO mcp_reader;
GRANT USAGE ON SCHEMA public TO mcp_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO mcp_reader;
ALTER ROLE mcp_reader SET statement_timeout='5s';
ALTER ROLE mcp_reader SET default_transaction_read_only=on;
