# ML Digest

A real-time machine learning research dashboard that fetches papers from arXiv, generates AI-powered summaries using Groq, and displays them through an interactive web interface.

## Features

- 📚 **Automated Paper Fetching** - Scrapes latest ML/AI papers from arXiv
- 🤖 **AI Summaries** - Uses Groq's llama-3.3-70b model to generate concise paper summaries
- 💾 **Cloudflare D1** - Managed SQLite storage with full-text search for fast keyword queries
- ⚡ **Cloudflare Pages Functions** - API for paper retrieval, search, and trending velocity, same-origin with the frontend
- 🎨 **Interactive Frontend** - Clean, responsive web interface with filters, trending cards, and AdSense slot
- 📊 **Statistics** - Aggregated insights on paper categories, date trends, and momentum

## Project Structure

```
ml-papers/
├── functions/api/            # Cloudflare Pages Functions (API)
│   ├── papers.js             # GET /api/papers
│   ├── stats.js              # GET /api/stats
│   ├── ingest.js             # POST /api/ingest (authenticated, used by CI)
│   └── _shared.js            # Shared helpers
├── pipeline/                 # Data processing pipeline
│   ├── arxiv_pipeline.py     # arXiv scraper & Groq integration
│   └── ingest.py             # One-shot: run pipeline, POST results to /api/ingest
├── frontend/                 # Web frontend
│   └── index.html            # Self-contained dashboard (inline CSS/JS)
├── schema.sql                # D1 schema (papers table + FTS5 index)
├── wrangler.toml             # Cloudflare Pages + D1 binding config
├── package.json              # wrangler devDependency + local dev script
├── requirements.txt          # Python dependencies (ingestion pipeline)
└── README.md                 # This file
```

See `DEPLOYMENT.md` for full Cloudflare setup and deployment instructions.

## Local development

### Prerequisites

- Python 3.11+ and Node.js (for `wrangler`)
- Groq API key (free tier available at https://console.groq.com)

### Setup

```bash
git clone <repository-url>
cd ml-papers

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

npm install
npx wrangler d1 execute ml-papers-db --local --file=./schema.sql   # one-time
```

### Run the app

```bash
npm run dev
```

Serves the dashboard and API together (same-origin) at `http://localhost:8788`.

### Ingest papers locally

```bash
export GROQ_API_KEY=your_key_here
export INGEST_URL=http://localhost:8788/api/ingest
export INGEST_TOKEN=dev-secret   # must match the local Functions env
python pipeline/ingest.py
```

This fetches the latest papers from arXiv (cs.LG, stat.ML, cs.AI), summarizes
each with Groq, and POSTs the results to `/api/ingest`, which upserts them
into D1.

## Automated Daily Ingestion (GitHub Actions)

The workflow in `.github/workflows/daily-ingestion.yml` runs the full
ingestion (fetch → summarize → POST to the deployed `/api/ingest` endpoint)
every day at 06:00 UTC, and can also be triggered manually from the Actions
tab via **Run workflow**. See `DEPLOYMENT.md` for the required repo secrets
(`GROQ_API_KEY`, `INGEST_URL`, `INGEST_TOKEN`).

## API Endpoints

- `GET /api/papers` - List papers with pagination
  - Query params: `task`, `difficulty`, `search`, `limit` (max 200), `offset`
- `GET /api/stats` - Aggregated statistics, task/date breakdowns, and trending papers
- `POST /api/ingest` - Authenticated upsert endpoint used by the daily CI job (`X-Ingest-Token` header required)

## Configuration

Edit `pipeline/arxiv_pipeline.py` to customize:
- `CATEGORIES` - arXiv categories to fetch (default: cs.LG, stat.ML, cs.AI)
- `MAX_PAPERS` - Number of papers per run (default: 20)
- `MODEL` - Groq model (default: llama-3.3-70b-versatile)
- `SLEEP_SEC` - Rate limiting delay between requests

## Database Schema

**papers table** (see `schema.sql`):
- `id` - arXiv paper ID (primary key)
- `title` - Paper title
- `abstract` - Paper abstract
- `authors` - JSON array of authors
- `published` - Publication date (YYYY-MM-DD)
- `categories` - JSON array of arXiv categories
- `summary`, `tldr`, `task`, `difficulty`, `methods` - Groq-generated fields
- `inserted_at` - Last upsert timestamp

Full-text search runs against the `papers_fts` FTS5 virtual table
(id, title, abstract, summary, tldr).

## Backups

D1 has built-in Time Travel (30-day point-in-time recovery) — see
`DEPLOYMENT.md`. Do not run `wrangler d1 export` against this database
(known to break with FTS5 virtual tables present).

## Troubleshooting

**No Groq API key error:**
```bash
export GROQ_API_KEY=your_key_here
```

**Ingestion POST fails with 401:** `INGEST_TOKEN` doesn't match between the
client and the Pages Functions environment — see `DEPLOYMENT.md`.

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please submit pull requests or open issues for bugs/features.

---

Built with ❤️ for ML researchers
