# CreatorPulse Frontend

Minimal React + Vite dashboard for managing newsletter sources, generating AI summaries, previewing the HTML email, and triggering delivery.

## Scripts
```bash
npm install          # install dependencies
npm run dev          # start Vite dev server on http://localhost:5173
npm run build        # production build in dist/
npm run preview      # preview built assets locally
```

Set the API base in `.env.local` (defaults to `http://localhost:8000`):
```
VITE_API_URL=http://localhost:8000
```

## UI Overview
- **Add Source** — Register a new RSS feed; the list updates immediately.
- **Sources** — View existing feeds and trigger ingestion per source.
- **Newsletter** — Generate an AI-produced HTML draft and review the exact markup before sending.
- **Send Email** — Calls the FastAPI backend to rebuild the HTML + plain text email and deliver it via SMTP.

All calls proxy to the FastAPI API defined by `VITE_API_URL`.
