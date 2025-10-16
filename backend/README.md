# CreatorPulse Backend (FastAPI)

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export $(cat .env | xargs)  # or set variables manually
uvicorn app.main:app --reload --port 8000
```

## Endpoints
- `GET /health`
- `GET /sources`
- `POST /sources` (name, url, type)
- `DELETE /sources?url=...`
- `POST /newsletter/generate`
- `POST /newsletter/send`
- `POST /feedback`

## Environment
Copy `.env.example` → `.env` and fill keys.
