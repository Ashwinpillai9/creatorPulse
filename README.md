# CreatorPulse MVP (FastAPI + React + Supabase)

## Local Dev
### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # fill in keys
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env.local
npm run dev
```

## Deploy (Hugging Face Spaces)
- Create Space with FastAPI (Docker) or SDK: FastAPI
- Set environment secrets (SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY, GEMINI_API_KEY, EMAIL_FROM, SMTP_USER, SMTP_PASS)
- Point frontend to the Space URL via `VITE_API_URL`

## GitHub Action (Scheduler)
- Update `.github/workflows/daily.yml` with your Space URL.
