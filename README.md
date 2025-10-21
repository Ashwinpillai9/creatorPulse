# CreatorPulse

CreatorPulse is a lightweight newsroom assistant that curates stories from your Supabase feeds, summarizes them with Gemini/OpenAI, and ships a polished HTML email via Gmail SMTP. The refreshed dashboard guides you through a pipeline that ingests data, curates the top ten stories, generates newsroom-style headlines and summaries, previews the HTML draft, and sends after approval.

## Features
- **Source management** - Add RSS feeds, trigger ingestion, and review the active list backed by Supabase.
- **Automated pipeline** - Optional source input -> ingest feeds -> curate top ten stories -> summarize with newsroom headlines -> preview -> approve & send.
- **Editable drafts** - Tune the HTML and plain text newsletter before sending.
- **AI summarization** - Gemini (preferred) or OpenAI produce two-sentence briefs with a Why it matters line plus an editor-style headline.
- **HTML email generation** - Render a responsive multi-part email (HTML + plain text) ready for modern mail clients.
- **Guided React UI** - One-page dashboard with pipeline status, story lineup, HTML preview, and approval controls.
- **Automated delivery** - Optional GitHub Action (.github/workflows/daily.yml) to ping your deployed backend on a schedule.

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
| `ALLOWED_ORIGINS` | Comma-separated list of frontend origins (defaults to `*`) |
| `ALLOW_CREDENTIALS` | Set to `true` if you need cookies/bearer auth when `ALLOWED_ORIGINS` is not `*` |

## Frontend Setup
```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env.local
npm run dev
```

The dev server runs at http://localhost:5173. The dashboard automatically calls the FastAPI backend using `VITE_API_URL`.

## Sending the Newsletter
1. **Run the pipeline** - Optionally supply a new RSS feed, choose whether to re-ingest existing sources, and trigger the automated flow. The backend fetches entries, downloads article bodies, generates newsroom headlines and summaries, curates the top ten stories, and composes the HTML draft.
2. **Review the lineup** - The UI lists each story with its headline, summary, and source link, and renders the exact HTML email preview.
3. **Approve & send** - Click 'Approve & Send' to post to /newsletter/send, which wraps the content in multipart MIME and delivers it via Gmail SMTP.

## Deployment

### Backend (Docker)
The repo ships with a `Dockerfile` that serves the FastAPI app with Uvicorn.

```bash
docker build -t creatorpulse-backend .
docker run -p 7860:7860 \
  -e SUPABASE_URL=... \
  -e SUPABASE_KEY=... \
  -e EMAIL_FROM=... \
  -e SMTP_USER=... \
  -e SMTP_PASS=... \
  -e GEMINI_API_KEY=... \
  -e OPENAI_API_KEY=... \
  -e ALLOWED_ORIGINS=https://your-frontend.app \
  creatorpulse-backend
```

The container listens on `$PORT` (default `7860`). Adjust `ALLOWED_ORIGINS` to the exact frontend domain; leave it blank to allow all origins during local testing (credentials will automatically be disabled when `*` is used).

#### Hugging Face Spaces
1. Create a **Docker** Space with the *Blank* template.
2. Upload the repository (or the `backup` folder that includes the `Dockerfile`).
3. Add secrets in the Space settings for the environment variables above.
4. After the build completes, verify `https://<space>.hf.space/health` returns a 200 response.

#### Render / Railway / Fly.io
Use the same container or configure a Python build step:

- Install command: `pip install -r backend/requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Frontend (Static hosting)
1. Set `VITE_API_URL` to the deployed backend URL.
2. Build the React app:
   ```bash
   cd frontend
   npm ci
   npm run build
   ```
3. Deploy `frontend/dist` to any static host:
   - **Vercel / Netlify**: import the project, set the `VITE_API_URL` env variable, and use `npm run build`.
   - **Hugging Face Spaces**: Create a *Static → React* Space, upload the `frontend/` directory, and set `VITE_API_URL` in the Space variables.

Once both services are live, update `ALLOWED_ORIGINS` (backend) and `VITE_API_URL` (frontend) so they point to each other.

## Automation
`./.github/workflows/daily.yml` contains a scheduled GitHub Action that can hit your deployed backend each morning. Update the webhook URL to your hosted FastAPI endpoint and enable the workflow to keep newsletters flowing automatically.

