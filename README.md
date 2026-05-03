# AI Content Analyzer — TikTok Script Generation Pipeline

> An end-to-end automation pipeline that turns Twitter/X bookmarks into ready-to-record TikTok scripts — no manual effort required.

---

## Background

The manual workflow for creating TikTok content takes **1–3 hours per batch**:
1. Scroll Twitter, find interesting articles or threads
2. Copy-paste content into a Claude/ChatGPT chat
3. Ask it to write a TikTok script (hook, body, CTA)
4. Revise multiple times until it sounds natural
5. Copy the final script → record

This project **automates steps 1–4** entirely.

**Proof of concept:** A Bitcoin-related video generated using the hook formula embedded in this pipeline reached **~900K views**, growing the channel from 80 to 2,000+ followers.

👉 [Watch the video here](https://www.tiktok.com/@taufiqoo/video/7623606514544020756)
---

## How the Pipeline Works

```
Twitter/X Bookmarks or Home Timeline
        │
        ▼
[1. Scraper]        → Headless browser login & tweet fetching via Playwright
        │
        ▼
[2. Extractor]      → Opens article links, strips noise, extracts clean text
        │
        ▼
[3. Relevance AI]   → Gemini/Claude scores content relevance (0.0–1.0)
        │             Passes if score ≥ 0.65
        ▼
[4. Script AI]      → Generates 3 TikTok script angles per piece of content
        │             (Hero, Tips & Tricks, Controversial)
        │             Uses proven FYP hook formulas + strict language rules
        ▼
[5. Dashboard]      → Review, inline edit, approve, copy → record
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router) |
| Backend | Python FastAPI + Celery |
| Database | PostgreSQL |
| Task Queue | Redis + Celery |
| AI | Google Gemini (primary) / Anthropic Claude (optional) |
| Scraping | Playwright (Python) |
| Deployment | Docker Compose |

---

## Getting Started

### Prerequisites

- Docker & Docker Compose **OR** Python 3.9+ & Node.js 18+
- A Twitter/X account for bookmark scraping
- An API key from **Google Gemini** (required) or **Anthropic Claude** (optional)

---

### Option A: Docker (Recommended)

The easiest way to run everything. All services (Backend, Frontend, PostgreSQL, Redis) start automatically.

**1. Clone & configure:**
```bash
git clone <repo-url>
cd ai-content-analyzer
cp .env.example .env
```

**2. Fill in your `.env` file:**
```env
# Twitter credentials used for scraping
TWITTER_USERNAME=your_twitter_username
TWITTER_PASSWORD=your_twitter_password

# LLM — at least one must be set
GEMINI_API_KEY=AIza...          # Free from Google AI Studio
ANTHROPIC_API_KEY=              # Optional, leave blank if not available

# Application secret key (any long random string)
SECRET_KEY=replace-this-with-a-long-random-string
```

**3. Start all services:**
```bash
docker compose up --build
```

**4. Access the app:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs

**5. Stop:**
```bash
docker compose down
```

---

### Option B: Local Development (Without Docker)

Best for development and faster debugging with hot-reload.

**Additional requirements:** PostgreSQL and Redis must already be running locally.

#### Setup PostgreSQL

```bash
psql -U postgres
```
```sql
CREATE ROLE pipeline_user WITH LOGIN PASSWORD 'pipeline_pass';
CREATE DATABASE content_pipeline OWNER pipeline_user;
GRANT ALL PRIVILEGES ON DATABASE content_pipeline TO pipeline_user;
\q
```

#### Setup Redis

```bash
# macOS
brew install redis
brew services start redis

# Or run directly
redis-server
```

#### Backend Setup

```bash
# 1. Create a virtual environment
cd backend
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install the headless browser (required for scraping, one-time only)
playwright install chromium

# 4. Configure your .env at the project root
cp ../.env.example ../.env
# → Edit .env with your credentials

# 5. Run database migrations
alembic upgrade head

# 6. Seed initial niche configs
python scripts/seed.py
```

**Run the backend API:**
```bash
# From the backend folder with venv activated
uvicorn app.main:app --reload --port 8000
```

**Run the Celery worker** (in a separate terminal):
```bash
# From the backend folder with venv activated
celery -A app.celery_app worker --loglevel=info
```

#### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

#### Shortcut: Run Everything at Once

```bash
# From project root
make dev
```

---

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `TWITTER_USERNAME` | Twitter account username for scraping | ✅ |
| `TWITTER_PASSWORD` | Twitter account password | ✅ |
| `GEMINI_API_KEY` | API key from Google AI Studio | ✅ (if no Anthropic key) |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | ⬜ Optional |
| `SECRET_KEY` | Application secret key (min. 32 chars, any string) | ✅ |
| `DATABASE_URL` | PostgreSQL connection URL | ✅ (auto-set in Docker) |
| `REDIS_URL` | Redis connection URL | ✅ (auto-set in Docker) |

**Getting a Gemini API key (free):**
1. Go to https://aistudio.google.com/
2. Click **Get API Key**
3. Copy the key into your `.env`

**LLM selection logic:** The system automatically uses **Anthropic Claude** if `ANTHROPIC_API_KEY` is valid (starts with `sk-ant-`). Otherwise, it falls back to **Google Gemini** automatically.

---

## Useful Commands

```bash
# Start all local services
make dev

# Run only backend + worker
make dev-backend   # terminal 1
make dev-worker    # terminal 2

# Run only frontend
make dev-frontend

# Database migrations
cd backend && alembic upgrade head

# Seed niche configs
cd backend && python scripts/seed.py

# Reset the database (caution: destructive)
cd backend && alembic downgrade base && alembic upgrade head
```

---

## Dashboard Features

| Page | Description |
|---|---|
| **Home / Pipeline** | Trigger the pipeline, monitor real-time progress per step |
| **Tweets** | Browse fetched tweets and their relevance scores |
| **Scripts** | Review, inline-edit, approve, or reject AI-generated scripts |
| **Analytics** | Track FYP rate and which hook formulas perform best |
| **Settings** | Manage niche configs, keywords, and custom script rules |

---

## Troubleshooting

**Pipeline stuck on "Scraping" for a long time:**
- Playwright browser may not be installed: run `playwright install chromium`
- Check the Celery worker terminal for a detailed error message

**Error: `role "pipeline_user" does not exist`:**
- Run the PostgreSQL setup commands in the Backend Setup section above

**Error: `lxml.html.clean` import failed:**
- Run: `pip install lxml_html_clean`

**Twitter login fails:**
- Double-check the username and password in your `.env`
- Try logging in manually first to clear any CAPTCHA or verification challenges
- Twitter may require email/phone verification on a new login

---

## Project Structure

```
ai-content-analyzer/
├── backend/
│   ├── app/
│   │   ├── routers/          # FastAPI route handlers
│   │   ├── services/         # Core business logic
│   │   │   ├── script_generator.py    # LLM prompts + dual-provider logic
│   │   │   ├── twitter_scraper.py     # Playwright-based scraping
│   │   │   └── article_extractor.py  # Trafilatura text extraction
│   │   ├── models.py         # SQLAlchemy ORM models
│   │   ├── tasks.py          # Celery background tasks (the pipeline)
│   │   └── config.py         # Environment & settings
│   ├── alembic/              # Database migrations
│   └── scripts/seed.py       # Initial niche config seeder
├── frontend/
│   └── src/app/              # Next.js pages & components
├── docker-compose.yml
├── Makefile
└── .env.example
```

---

## How the AI Generates Scripts

The script generator uses a carefully crafted system prompt with:

- **Hook formula bank** — 10 proven hook patterns (Formula #1 is responsible for the 900K views result)
- **Strict language rules** — conversational Indonesian, short sentences, no AI-sounding phrases
- **Few-shot examples** — 2 real high-performing scripts embedded as style references
- **Multi-angle generation** — each content piece gets 3 different script angles simultaneously

The same prompt logic that was used manually in Claude chats is now fully automated and called programmatically via API.

---

## License

MIT
