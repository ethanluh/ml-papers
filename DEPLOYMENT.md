# Deployment Guide: Cloudflare Pages + D1

The app runs entirely on Cloudflare: static frontend + API on **Pages** (with
Pages Functions for the API routes), data in **D1** (Cloudflare's managed
SQLite). Daily ingestion runs as a **GitHub Actions** cron job that POSTs
new papers to an authenticated API route, which upserts them into D1.

There is no long-running worker/scheduler process to deploy or pay for —
GitHub Actions is the only ingestion trigger.

## Architecture

- `frontend/` — static dashboard (`index.html`, self-contained), served as
  Pages' static assets.
- `functions/api/papers.js`, `functions/api/stats.js` — read-only API
  routes, implemented as Pages Functions with a native D1 binding (`env.DB`).
  Same-origin as the frontend, so no CORS configuration is needed.
- `functions/api/ingest.js` — authenticated write route
  (`POST /api/ingest`, gated by an `X-Ingest-Token` header checked against
  the `INGEST_TOKEN` environment secret) used by the daily GitHub Actions
  job. Uses D1's bound prepared statements — no manual SQL escaping.
- `pipeline/arxiv_pipeline.py` — fetches + summarizes papers (unchanged).
- `pipeline/ingest.py` — one-shot script that runs the pipeline and POSTs
  results to `/api/ingest`. Run daily by
  `.github/workflows/daily-ingestion.yml`.
- `schema.sql` — D1 schema (papers table + FTS5 full-text index).

## One-time setup

### 1. Create the D1 database
```bash
npx wrangler d1 create ml-papers-db
```
Copy the printed `database_id` into `wrangler.toml`'s `[[d1_databases]]`
block.

### 2. Apply the schema
```bash
npx wrangler d1 execute ml-papers-db --remote --file=./schema.sql
```

### 3. Create the Pages project
Connect the GitHub repository via the Cloudflare dashboard
(Workers & Pages → Create → Pages → Connect to Git), or via CLI:
```bash
npx wrangler pages project create ml-papers-dashboard
npx wrangler pages deploy frontend
```
Cloudflare auto-detects `functions/` and deploys the API routes alongside
the static site.

### 4. Bind D1 to the Pages project
If your installed `wrangler` version doesn't apply the `[[d1_databases]]`
block in `wrangler.toml` to a Pages project automatically, bind it manually:
Pages project → Settings → Functions → D1 database bindings → add
variable name `DB` → select `ml-papers-db`.

### 5. Set secrets
- **Pages project** (Settings → Environment variables, as a secret):
  `INGEST_TOKEN` — a random shared secret the ingestion job authenticates with.
- **GitHub repo secrets** (Settings → Secrets and variables → Actions):
  - `GROQ_API_KEY` — for paper summarization.
  - `INGEST_URL` — e.g. `https://ml-papers-dashboard.pages.dev/api/ingest`.
  - `INGEST_TOKEN` — must match the value set on the Pages project.

### 6. Trigger ingestion
Run the workflow manually once (Actions tab → Daily arXiv Ingestion →
Run workflow) to verify papers show up on the live site, then let the
06:00 UTC daily cron take over.

## Local development

```bash
npm install
npx wrangler d1 execute ml-papers-db --local --file=./schema.sql   # one-time
npm run dev   # serves the dashboard + API at http://localhost:8788
```

To ingest into the local D1 instance, run the Python pipeline against a
locally running `wrangler pages dev` (set `INGEST_URL=http://localhost:8788/api/ingest`
and any `INGEST_TOKEN` matching a local `.dev.vars` file):
```bash
export GROQ_API_KEY=your_key_here
export INGEST_URL=http://localhost:8788/api/ingest
export INGEST_TOKEN=dev-secret
python pipeline/ingest.py
```

## Backups

D1 has built-in **Time Travel** (30-day point-in-time recovery) — no manual
backup step is required:
```bash
npx wrangler d1 time-travel restore ml-papers-db --timestamp=<ISO8601>
```

**Do not run `wrangler d1 export`** against this database — Cloudflare has an
open issue where export crashes/corrupts databases that contain FTS5 virtual
tables (this database's `papers_fts` table). Use Time Travel for any
recovery needs instead.

## Troubleshooting

**API returns empty results / 500s**: confirm the D1 binding is named `DB`
in both `wrangler.toml` and the Pages dashboard, and that `schema.sql` has
been applied to the `--remote` database.

**Ingestion job fails with 401**: `INGEST_TOKEN` in the GitHub repo secrets
doesn't match the Pages project's `INGEST_TOKEN` environment variable.

**Search returns nothing**: full-text search matches `papers_fts`; if papers
were inserted before the FTS table existed, they'll be present in `papers`
but not searchable — re-run ingestion to backfill via the upsert path in
`functions/api/ingest.js`.
