-- D1 schema for the arXiv ML papers dashboard.
-- Apply with:
--   npx wrangler d1 execute ml-papers-db --remote --file=./schema.sql
--   npx wrangler d1 execute ml-papers-db --local  --file=./schema.sql

CREATE TABLE IF NOT EXISTS papers (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    abstract    TEXT NOT NULL,
    authors     TEXT NOT NULL,
    published   TEXT NOT NULL,
    categories  TEXT NOT NULL,
    summary     TEXT,
    tldr        TEXT,
    task        TEXT,
    difficulty  TEXT,
    methods     TEXT,
    inserted_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_published  ON papers(published);
CREATE INDEX IF NOT EXISTS idx_task       ON papers(task);
CREATE INDEX IF NOT EXISTS idx_difficulty ON papers(difficulty);

CREATE VIRTUAL TABLE IF NOT EXISTS papers_fts
    USING fts5(id UNINDEXED, title, abstract, summary, tldr);
