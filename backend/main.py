"""
DAY 7 — main.py (updated with Supabase)
=========================================
Same API as Day 6 — but now every research result is saved
to Supabase permanently instead of lost on server restart.

Changes from Day 6:
  - research_store dict → Supabase table (financial_research)
  - save_research()   → inserts a row
  - update_research() → updates status + results when done
  - fetch_research()  → reads from Supabase by ID
"""

import os
import uuid
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client

from orchestrator import run_research

load_dotenv()

# ── Supabase client ───────────────────────────────────────────
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

TABLE = "financial_research"

# ── FastAPI app ───────────────────────────────────────────────
app = FastAPI(
    title="AlphaResearch API",
    description="Multi-agent AI financial research system",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPPORTED_COMPANIES = [
    {"name": "Infosys",      "ticker": "INFY",          "exchange": "NYSE"},
    {"name": "TCS",          "ticker": "TCS.NS",        "exchange": "NSE"},
    {"name": "Wipro",        "ticker": "WIPRO.NS",      "exchange": "NSE"},
    {"name": "HCL Tech",     "ticker": "HCLTECH.NS",    "exchange": "NSE"},
    {"name": "Reliance",     "ticker": "RELIANCE.NS",   "exchange": "NSE"},
    {"name": "HDFC Bank",    "ticker": "HDFCBANK.NS",   "exchange": "NSE"},
    {"name": "Tata Motors",  "ticker": "TATAMOTORS.BO", "exchange": "BSE"},
    {"name": "Zomato",       "ticker": "ZOMATO.NS",     "exchange": "NSE"},
    {"name": "Apple",        "ticker": "AAPL",          "exchange": "NASDAQ"},
    {"name": "Microsoft",    "ticker": "MSFT",          "exchange": "NASDAQ"},
    {"name": "Tesla",        "ticker": "TSLA",          "exchange": "NASDAQ"},
    {"name": "Amazon",       "ticker": "AMZN",          "exchange": "NASDAQ"},
]


# ── Pydantic models ───────────────────────────────────────────
class ResearchRequest(BaseModel):
    question: str
    company:  str

    class Config:
        json_schema_extra = {
            "example": {
                "question": "Is Infosys a good investment right now?",
                "company":  "Infosys"
            }
        }

class ResearchResponse(BaseModel):
    id:         str
    status:     str
    company:    str
    question:   str
    brief:      Optional[str] = None
    sentiment:  Optional[dict] = None
    quant:      Optional[dict] = None
    risk:       Optional[dict] = None
    created_at: str

class StatusResponse(BaseModel):
    id:      str
    status:  str
    message: str


# ── Supabase helpers ──────────────────────────────────────────

def save_research(research_id: str, company: str, question: str):
    row = {
        "id":         research_id,
        "company":    company,
        "question":   question,
        "status":     "queued",
        "created_at": datetime.utcnow().isoformat(),
    }
    supabase.table(TABLE).insert(row).execute()


def update_research(research_id: str, updates: dict):
    supabase.table(TABLE).update(updates).eq("id", research_id).execute()


def fetch_research(research_id: str) -> Optional[dict]:
    result = supabase.table(TABLE).select("*").eq("id", research_id).execute()
    return result.data[0] if result.data else None


def fetch_all_research() -> list:
    result = (
        supabase.table(TABLE)
        .select("id, company, question, status, created_at")
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    return result.data or []


# ── Background task ───────────────────────────────────────────

def run_pipeline_in_background(research_id: str, question: str, company: str):
    try:
        update_research(research_id, {"status": "running"})
        print(f"\n▶ Pipeline running: {research_id}")

        result = run_research(question, company)

        update_research(research_id, {
            "status":    "completed",
            "brief":     result.get("brief", ""),
            "sentiment": result.get("sentiment", {}),
            "quant":     result.get("quant", {}),
            "rag":       result.get("rag", {}),
            "risk":      result.get("risk", {}),
        })
        print(f"✅ Completed: {research_id}")

    except Exception as e:
        update_research(research_id, {"status": "failed", "brief": f"Error: {str(e)}"})
        print(f"❌ Failed {research_id}: {e}")


# ── ENDPOINTS ─────────────────────────────────────────────────

@app.get("/")
def health_check():
    return {
        "status":   "healthy",
        "service":  "AlphaResearch API",
        "version":  "2.0.0",
        "database": "Supabase connected"
    }


@app.get("/companies")
def get_supported_companies():
    return {"companies": SUPPORTED_COMPANIES, "total": len(SUPPORTED_COMPANIES)}


@app.post("/research", response_model=StatusResponse)
def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    if not request.company.strip():
        raise HTTPException(status_code=400, detail="Company cannot be empty")

    research_id = str(uuid.uuid4())
    save_research(research_id, request.company, request.question)

    background_tasks.add_task(
        run_pipeline_in_background,
        research_id,
        request.question,
        request.company
    )

    print(f"\n🚀 Research started: {research_id} | {request.company}")

    return StatusResponse(
        id=research_id,
        status="queued",
        message=f"Research started for {request.company}. Poll GET /research/{research_id} for results."
    )


@app.get("/research/{research_id}", response_model=ResearchResponse)
def get_research_result(research_id: str):
    result = fetch_research(research_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Research job '{research_id}' not found")
    return ResearchResponse(**result)


@app.get("/research")
def list_all_research():
    jobs = fetch_all_research()
    return {"total": len(jobs), "jobs": jobs}


@app.delete("/research/{research_id}")
def delete_research(research_id: str):
    result = fetch_research(research_id)
    if not result:
        raise HTTPException(status_code=404, detail="Research job not found")
    supabase.table(TABLE).delete().eq("id", research_id).execute()
    return {"message": f"Deleted {research_id}"}