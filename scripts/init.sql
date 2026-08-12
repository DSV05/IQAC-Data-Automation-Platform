-- Run once on first database initialization

-- UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Full-text search support (used by global search module)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Vector similarity (used by AI module — optional)
-- CREATE EXTENSION IF NOT EXISTS vector;  -- requires pgvector image

COMMENT ON DATABASE iqac_db IS 'IQAC Data Automation Platform — Ganpat University';
