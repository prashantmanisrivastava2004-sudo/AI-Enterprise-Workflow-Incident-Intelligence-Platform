import os
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def get_analyzer():
    """Import the ML pipeline lazily so startup stays fast."""
    from src.pipeline import analyze_ticket
    return analyze_ticket


app = FastAPI(
    title="AI Enterprise Workflow & Incident Intelligence Platform",
    description="AI-powered support ticket analysis and incident intelligence API",
    version="1.0.0"
)


frontend_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)
allowed_origins = [
    origin.strip()
    for origin in frontend_origins.split(",")
    if origin.strip()
]

# Allow React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TicketRequest(BaseModel):
    ticket: str


@app.get("/")
def root():
    return {
        "message": "AI Enterprise Workflow & Incident Intelligence API is running"
    }


@app.post("/analyze-ticket")
def analyze(ticket: TicketRequest):
    analyzer = get_analyzer()
    result = analyzer(ticket.ticket)
    return result


if __name__ == "__main__":
    import os
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))