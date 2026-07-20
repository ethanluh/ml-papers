# arXiv ML Dashboard

A real-time machine learning research dashboard that fetches papers from arXiv, generates AI-powered summaries using Groq, and displays them through an interactive web interface.

## Features

- 📚 **Automated Paper Fetching** - Scrapes latest ML/AI papers from arXiv
- 🤖 **AI Summaries** - Uses Groq's llama-3.3-70b model to generate concise paper summaries
- 💾 **Local Database** - SQLite storage with full-text search for fast keyword queries
- ⚡ **FastAPI Backend** - RESTful API for paper retrieval, search, and trending velocity
- 🎨 **Interactive Frontend** - Clean, responsive web interface with filters, trending cards, and AdSense slot
- 📊 **Statistics** - Aggregated insights on paper categories, date trends, and momentum

## Project Structure

```
arxiv-ml-dashboard/
├── api/                      # FastAPI backend
│   ├── main.py              # API routes and server
│   └── models.py            # Pydantic data models
├── pipeline/                 # Data processing pipeline
│   ├── arxiv_pipeline.py    # arXiv scraper & Groq integration
│   ├── backup.py            # Local SQLite backup workflow
│   ├── db.py                # SQLite database interface
│   └── scheduler.py         # Periodic task scheduling
├── frontend/                 # Web frontend
│   ├── index.html           # Main page
│   ├── app.js               # Application logic
│   └── style.css            # Styling
├── db/                       # Database directory
│   └── papers.db            # SQLite database (auto-created)
├── requirements.txt         # Python dependencies
├── .env                     # Environment configuration
└── README.md               # This file
```

## Installation

### Prerequisites

- Python 3.10+
- pip or conda
- Groq API key (free tier available at https://console.groq.com)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd arxiv-ml-dashboard
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your Groq API key:
   ```
   GROQ_API_KEY=your_api_key_here
   ```

## Usage

### 1. Fetch and Summarize Papers

```bash
python pipeline/arxiv_pipeline.py
```

This will:
- Fetch latest papers from arXiv categories (cs.LG, stat.ML, cs.AI)
- Generate summaries using Groq
- Store papers in SQLite database
- Create an automatic local backup before the scheduler runs

### 2. Backup the local database

```bash
python pipeline/backup.py
```

This saves `db/papers.db` to `db/backups/papers_backup_YYYYMMDD_HHMMSS.db`.

### 3. Start the API Server

```bash
uvicorn api.main:app --reload --port 8000
```

Server runs on `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Redoc: `http://localhost:8000/redoc`

### 3. Open the Frontend

Open `frontend/index.html` in your browser or serve with:
```bash
python -m http.server 3000 --directory frontend
```

Access at `http://localhost:3000`

## Automated Daily Ingestion (GitHub Actions)

The workflow in `.github/workflows/daily-ingestion.yml` runs the full ingestion
(fetch → summarize → store in SQLite) every day at 06:00 UTC, and can also be
triggered manually from the Actions tab via **Run workflow**.

Setup:
1. In your GitHub repository, go to **Settings → Secrets and variables → Actions**
2. Add a repository secret named `GROQ_API_KEY` with your Groq API key

Each run restores the SQLite database from the previous run's Actions cache, so
papers accumulate day over day. The raw results JSON and updated `papers.db`
are also uploaded as workflow artifacts (30-day retention).

## API Endpoints

- `GET /papers` - List all papers with pagination
  - Query params: `task`, `difficulty`, `search`, `limit`, `offset`
- `GET /papers/{paper_id}` - Get specific paper details
- `GET /stats` - Get aggregated statistics and trending paper hotness

## Configuration

Edit `pipeline/arxiv_pipeline.py` to customize:
- `CATEGORIES` - arXiv categories to fetch (default: cs.LG, stat.ML, cs.AI)
- `MAX_PAPERS` - Number of papers per category (default: 20)
- `MODEL` - Groq model (default: llama-3.3-70b-versatile)
- `SLEEP_SEC` - Rate limiting delay between requests

## Database Schema

**papers table:**
- `id` - arXiv paper ID (primary key)
- `title` - Paper title
- `abstract` - Paper abstract
- `authors` - JSON array of authors
- `published` - Publication date (YYYY-MM-DD)
- `categories` - JSON array of arXiv categories
- `arxiv_url` - Link to arXiv page
- `summary` - AI-generated summary from Groq
- `updated_at` - Last update timestamp

## Development

### Dependencies

- **FastAPI** - Modern web framework
- **Uvicorn** - ASGI server
- **Groq** - LLM API client
- **Requests** - HTTP library
- **Pydantic** - Data validation

### Code Style

Follow PEP 8 conventions. Format with:
```bash
pip install black pylint
black pipeline/ api/
```

## Troubleshooting

**No Groq API key error:**
```bash
export GROQ_API_KEY=your_key_here
```

**Port 8000 already in use:**
```bash
uvicorn api.main:app --port 8001
```

**Database locked error:**
- Ensure only one instance of the pipeline is running
- Delete `db/papers.db` and restart if corrupted

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please submit pull requests or open issues for bugs/features.

---

Built with ❤️ for ML researchers
