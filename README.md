# CreatorPulse

CreatorPulse is a lightweight newsroom assistant that curates stories from your Supabase feeds, summarizes them with Gemini/OpenAI, and ships a polished HTML email via Gmail SMTP. The refreshed dashboard guides you through a pipeline that ingests data, curates the top ten stories, generates newsroom-style headlines and summaries, previews the HTML draft, and sends after approval.

## Features
- **Source management** — Add RSS feeds, trigger ingestion, and review the active list backed by Supabase.
- **Automated pipeline** — Optional source input → ingest feeds → curate top ten stories → summarize with newsroom headlines → preview → approve & send.
- **AI summarization** — Gemini (preferred) or OpenAI produce two-sentence briefs with a `Why it matters` line plus an editor-style headline.
- **HTML email generation** — Render a responsive multi-part email (HTML + plain text) ready for modern mail clients.
- **Guided React UI** — One-page dashboard with pipeline status, story lineup, HTML preview, and approval controls.
- **Automated delivery** — Optional GitHub Action (`.github/workflows/daily.yml`) to ping your deployed backend on a schedule.

## Tech Stack
- FastAPI, Python 3.12
- React + Vite
- Supabase (PostgreSQL + storage)
- Gemini 1.5 Flash / OpenAI GPT-4o-mini
- Gmail SMTP (or compatible provider)

## Prerequisites
- Python 3.12+
- Node.js 20+ and npm
- Supabase project with the expected schemas (`sources`, `items`, `history`)
- API keys: `SUPABASE_URL`, `SUPABASE_KEY`, `GEMINI_API_KEY` (optional), `OPENAI_API_KEY` (optional), `EMAIL_FROM`, `SMTP_USER`, `SMTP_PASS`

## Backend Setup
```bash
cd backend
python -m venv .venv
. .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # fill in the variables listed below
uvicorn app.main:app --reload --port 8000
```

### Backend Environment Variables
| Variable | Purpose |
| --- | --- |
| `SUPABASE_URL` | Supabase project REST endpoint |
| `SUPABASE_KEY` | Service role key for Supabase |
| `GEMINI_API_KEY` | (Optional) Used for primary summarization model |
| `OPENAI_API_KEY` | (Optional) Fallback summarization model |
| `EMAIL_FROM` | From address for outbound email |
| `SMTP_USER` / `SMTP_PASS` | Credentials for the SMTP account |

## Frontend Setup
```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env.local
npm run dev
```

The dev server runs at http://localhost:5173. The dashboard automatically calls the FastAPI backend using `VITE_API_URL`.

## Sending the Newsletter
1. **Run the pipeline** — Optionally supply a new RSS feed, choose whether to re-ingest existing sources, and trigger the automated flow. Behind the scenes the backend fetches feed entries, downloads article bodies, generates newsroom headlines and summaries, curates the top ten stories, and composes the HTML draft.
2. **Review the lineup** — The UI lists each story with its headline, summary, and source link, and renders the exact HTML email preview.
3. **Approve & send** — Click “Approve & Send” to fire `/newsletter/send`, which rebuilds the top-ten newsletter, wraps it in multipart MIME, and delivers via Gmail SMTP.

## Deployment
- **Hugging Face Spaces**: Create a FastAPI Space, add the environment variables listed above, and deploy the backend. Point your frontend build (or Vite dev server) to the Space URL via `VITE_API_URL`.
- **Static frontend hosting**: Build with `npm run build` and serve the `frontend/dist` folder on any static host, configured with the same API base URL.

## Automation
`./.github/workflows/daily.yml` contains a scheduled GitHub Action that can hit your deployed backend each morning. Update the webhook URL to your hosted FastAPI endpoint and enable the workflow to keep newsletters flowing automatically.
