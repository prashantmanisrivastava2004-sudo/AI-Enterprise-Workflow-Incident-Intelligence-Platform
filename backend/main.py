from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.pipeline import analyze_ticket


app = FastAPI(
    title="AI Enterprise Workflow & Incident Intelligence Platform",
    description="AI-powered support ticket analysis and incident intelligence API",
    version="1.0.0"
)


# Allow React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
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
    result = analyze_ticket(ticket.ticket)
    return result