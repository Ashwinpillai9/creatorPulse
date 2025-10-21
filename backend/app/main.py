from dotenv import load_dotenv

load_dotenv()  # Ensure environment variables from .env are available before other imports

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import feedback, newsletter, sources

app = FastAPI(title="CreatorPulse API", version="0.1.0")

allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
allowed_origins = [
    origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()
]
if not allowed_origins:
    allowed_origins = ["*"]

allow_credentials = os.getenv("ALLOW_CREDENTIALS", "true").lower() == "true"
if allowed_origins == ["*"]:
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sources.router, prefix="/sources", tags=["Sources"])
app.include_router(newsletter.router, prefix="/newsletter", tags=["Newsletter"])
app.include_router(feedback.router, prefix="/feedback", tags=["Feedback"])


@app.get("/health")
def health():
    return {"status": "ok"}
