from dotenv import load_dotenv
load_dotenv()  # Ensure environment variables from .env are available before other imports

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import sources, newsletter, feedback

app = FastAPI(title="CreatorPulse API", version="0.1.0")

# CORS for local dev (adjust in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sources.router, prefix="/sources", tags=["Sources"])
app.include_router(newsletter.router, prefix="/newsletter", tags=["Newsletter"])
app.include_router(feedback.router, prefix="/feedback", tags=["Feedback"])

@app.get("/health")
def health():
    return {"status": "ok"}
