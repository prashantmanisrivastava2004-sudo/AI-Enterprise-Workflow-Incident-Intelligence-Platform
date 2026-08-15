from fastapi import FastAPI
from pydantic import BaseModel

from src.pipeline import analyze_ticket


app = FastAPI(
    title="AI Enterprise Workflow & Incident Intelligence Platform",
    description="AI-powered support ticket analysis and incident intelligence API",
    version="1.0.0"
)


class TicketRequest(BaseModel):
    ticket: str
    type: str = "Incident"


@app.get("/")
def root():
    return {
        "message": "AI Enterprise Workflow & Incident Intelligence API is running"
    }


@app.post("/analyze-ticket")
def analyze(ticket: TicketRequest):
    result = analyze_ticket(ticket.ticket)
    return result