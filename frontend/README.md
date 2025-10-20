# CreatorPulse Frontend

React + Vite dashboard that orchestrates the CreatorPulse pipeline: optional source intake, feed ingestion, top-ten curation, AI summarization, HTML preview, and approval to send the newsletter.

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

## UI Flow
1. **Pipeline controls** — Optionally provide a new RSS feed and choose whether to re-ingest existing sources.
2. **Run pipeline** — The app calls `/newsletter/pipeline`, which ingests data, curates the top ten stories, and returns HTML + text drafts.
3. **Story lineup** — Review the newsroom-style headlines, summaries, and source links for each curated article.
4. **Preview draft** — Inspect the HTML email exactly as it will appear in clients.
5. **Approve & send** — Trigger `/newsletter/send` to deliver the multi-part email via SMTP.

All API calls target the FastAPI backend configured by `VITE_API_URL`.
