# CreatorPulse Backend

FastAPI application that ingests creator news from Supabase, summarizes articles with AI, and produces a polished HTML newsletter ready to email.

## Getting Started
```bash
python -m venv .venv
. .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # populate the variables listed below
uvicorn app.main:app --reload --port 8000
```

### Required Environment Variables
| Key | Description |
| --- | --- |
| `SUPABASE_URL` | Supabase project REST URL |
| `SUPABASE_KEY` | Service role key for Supabase |
| `GEMINI_API_KEY` | (Optional) Preferred model for summaries |
| `OPENAI_API_KEY` | (Optional) Fallback summarization model |
| `EMAIL_FROM` | From address used for outbound email |
| `SMTP_USER` | SMTP account username |
| `SMTP_PASS` | SMTP account password |

### Core Endpoints
| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Health probe |
| `GET` | `/sources` | List sources from Supabase |
| `POST` | `/sources` | Add a source (`name`, `url`, `type`) |
| `DELETE` | `/sources?url=` | Remove a source |
| `POST` | `/newsletter/generate` | Returns newsletter HTML + text preview |
| `POST` | `/newsletter/send` | Sends newsletter email (HTML + plain text) |
| `POST` | `/feedback` | Store reader feedback payloads |

### Email Delivery
`app/core/emailer.py` sends multipart MIME messages (plain + HTML) via Gmail SMTP on port 587. Swap in another SMTP host by adjusting the connection settings if needed.

### Summaries
`app/core/llm_utils.py` prefers Gemini 1.5 Flash (if configured) and falls back to OpenAI GPT-4o-mini. When neither key is present, the raw article snippet is truncated as a last resort.
