"""src/api/main.py — FastAPI for Meeting Intelligence Platform"""
import os, time, json
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger

app = FastAPI(title="Meeting Intelligence Platform", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_search_index = None
_stats = {"meetings_processed": 0, "total_action_items": 0}

def get_analyzer():
    from openai import OpenAI
    class LLM:
        def __init__(self):
            self.client = OpenAI()
            self.model  = os.getenv("LLM_MODEL","gpt-4o-mini")
        def generate(self, system, user):
            r = self.client.chat.completions.create(
                model=self.model, temperature=0.0, max_tokens=2048,
                messages=[{"role":"system","content":system},{"role":"user","content":user}],
                response_format={"type":"json_object"})
            return r.choices[0].message.content
    from src.analysis.meeting_analyzer import MeetingAnalyzer
    return MeetingAnalyzer(LLM())

def get_search():
    global _search_index
    if _search_index is None:
        from src.search.meeting_search import MeetingSearchIndex
        _search_index = MeetingSearchIndex()
    return _search_index

@app.get("/health")
def health(): return {"status":"ok","timestamp":time.time()}

@app.get("/stats")
def stats(): return {**_stats, "indexed_meetings": len(get_search().meetings)}

class TranscriptRequest(BaseModel):
    transcript: str
    title: str = "Meeting"

@app.post("/analyze")
def analyze_transcript(request: TranscriptRequest):
    """Analyze a text transcript and extract structured insights."""
    analyzer = get_analyzer()
    insights = analyzer.analyze(request.transcript, request.title)
    d = insights.to_dict()
    get_search().add_meeting(d)
    _stats["meetings_processed"] += 1
    _stats["total_action_items"] += len(insights.action_items)
    return d

@app.post("/analyze/upload")
async def analyze_file(file: UploadFile = File(...), title: str = Form("Meeting")):
    """Upload a transcript .txt file for analysis."""
    text = (await file.read()).decode("utf-8", errors="ignore")
    analyzer = get_analyzer()
    insights = analyzer.analyze(text, title or file.filename)
    d = insights.to_dict()
    get_search().add_meeting(d)
    _stats["meetings_processed"] += 1
    _stats["total_action_items"] += len(insights.action_items)
    return d

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

@app.post("/search")
def search_meetings(request: SearchRequest):
    """Semantic search across all analyzed meetings."""
    results = get_search().search(request.query, request.top_k)
    return {"query": request.query, "results": [
        {"meeting": m, "score": round(s, 4)} for m, s in results
    ]}

@app.get("/digest/{meeting_idx}")
def get_digest(meeting_idx: int):
    """Get email/Slack digest for a meeting."""
    idx = get_search()
    if meeting_idx >= len(idx.meetings):
        raise HTTPException(404, "Meeting not found")
    from src.analysis.meeting_analyzer import MeetingInsights, ActionItem, Decision
    d = idx.meetings[meeting_idx]
    insights = MeetingInsights(
        title=d.get("title",""), date=d.get("date"), duration_mins=d.get("duration_mins"),
        participants=d.get("participants",[]), summary=d.get("summary",""),
        action_items=[ActionItem(**a) for a in d.get("action_items",[])],
        decisions=[Decision(**dec) for dec in d.get("decisions",[])],
        open_questions=d.get("open_questions",[]), topics=d.get("topics",[]),
        key_quotes=d.get("key_quotes",[]), next_meeting=d.get("next_meeting"),
        sentiment=d.get("sentiment","neutral"),
    )
    return {"digest": insights.to_summary_email()}