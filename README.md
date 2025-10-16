# CreatorPulse

CreatorPulse is a lightweight newsroom assistant that curates stories from your Supabase feeds, summarizes them with Gemini/OpenAI, and ships a polished HTML email via Gmail SMTP. The frontend pairs the workflow down to a single minimal dashboard so you can add sources, generate a draft, preview the exact email markup, and send it in a few clicks.

## Features
- **Source management** — Add RSS feeds, trigger ingestion, and review the active list backed by Supabase.
- **AI summarization** — Generate concise bulletproof summaries with Gemini (preferred) or OpenAI as fallback.
- **HTML email generation** — Render a responsive multi-part email (HTML + plain text) ready for modern mail clients.
- **Minimal React UI** — One-page dashboard with draft preview, status messaging, and clean typography.
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
1. **Load sources** — The app fetches existing feeds from Supabase. Use “Add source” to register new RSS URLs and “Ingest” to pull the latest items.
2. **Generate draft** — Clicking “Generate draft” hits `/newsletter/generate`, returning HTML + text. The preview frame renders the HTML email exactly as recipients will see it.
3. **Send email** — “Send email” posts to `/newsletter/send`, which rebuilds the email, wraps it in multipart MIME, and delivers via Gmail SMTP.

## Deployment
- **Hugging Face Spaces**: Create a FastAPI Space, add the environment variables listed above, and deploy the backend. Point your frontend build (or Vite dev server) to the Space URL via `VITE_API_URL`.
- **Static frontend hosting**: Build with `npm run build` and serve the `frontend/dist` folder on any static host, configured with the same API base URL.

## Automation
`./.github/workflows/daily.yml` contains a scheduled GitHub Action that can hit your deployed backend each morning. Update the webhook URL to your hosted FastAPI endpoint and enable the workflow to keep newsletters flowing automatically.
