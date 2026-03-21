# Meeting Intelligence Platform

[![Live Demo](https://img.shields.io/badge/Live_Demo-Render-38bdf8?style=for-the-badge&logo=render)](https://meeting-intelligent-platform.onrender.com) [![GitHub](https://img.shields.io/badge/GitHub-Naresh1401-181717?style=for-the-badge&logo=github)](https://github.com/Naresh1401/Meeting-intelligent-platform)

Automatically extract structured intelligence from meeting transcripts — action items with owners, decisions made, open questions, and semantic search across your entire meeting history.

## The Problem

Hours of meetings happen every week. Nobody takes good notes. Action items get lost. Decisions aren't documented. This platform gives every meeting a structured summary, ready to share within seconds of the call ending.

## Architecture

```
Audio/Text Transcript
        │
        ▼
┌──────────────────────┐
│  Whisper Transcriber │  Audio → Text (OpenAI Whisper)
│  + Text Loader       │  Supports: mp3, mp4, wav, m4a, txt
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Meeting Analyzer    │  LLM extracts structured insights
│                      │
│  • Summary           │
│  • Action items      │  "James: write scope doc by Friday [HIGH]"
│  • Decisions         │  "Dashboard moves to Q4 — Lisa"
│  • Open questions    │
│  • Topics + Sentiment│
└──────────┬───────────┘
           │
           ├──→ Email/Slack Digest (formatted markdown)
           │
           ▼
┌──────────────────────┐
│  Search Index        │  Semantic search across all meetings
│                      │  "What did we decide about pricing?"
│  Keyword fallback    │  Returns: top matching past meetings + scores
│  + Embeddings (opt.) │
└──────────────────────┘
```

## Quickstart

```bash
git clone https://github.com/Naresh1401/meeting-intelligence-platform
cd meeting-intelligence-platform
pip install -r requirements.txt
cp .env.example .env    # Add OPENAI_API_KEY
make run
```

## API Usage

### Analyze a transcript
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Q3 Planning",
    "transcript": "Sarah: Onboarding is priority one...\nJames: I agree. Tom owns API rate limits by end of September."
  }'
```

**Response:**
```json
{
  "title": "Q3 Planning",
  "summary": "Team aligned on Q3: onboarding redesign as P1, reporting to Q4.",
  "action_items": [
    {"description": "Own API rate limit increase", "owner": "Tom", "due_date": "end of September", "priority": "high"}
  ],
  "decisions": [
    {"description": "Onboarding redesign is Q3 priority one", "made_by": "Lisa"}
  ],
  "sentiment": "positive"
}
```

### Get email digest
```bash
curl http://localhost:8000/digest/0
```

```
## Meeting Summary: Q3 Planning

### Action Items
- [ ] Own API rate limit increase (@Tom) — due end of September [HIGH]
- [ ] Circulate roadmap doc (@Sarah) — due Tomorrow

### Decisions Made
- ✅ Onboarding redesign is Q3 priority one
- ✅ Dashboard reporting moves to Q4

### Open Questions / Blockers
- ❓ How to staff infrastructure without impacting onboarding?
```

### Search past meetings
```bash
curl -X POST http://localhost:8000/search \
  -d '{"query": "what did we decide about the reporting dashboard?"}'
```

## Running Tests

```bash
make test    # 8 tests
```

## Project Structure

```
meeting-intelligence-platform/
├── src/
│   ├── analysis/
│   │   └── meeting_analyzer.py    # LLM insight extraction
│   ├── transcription/
│   │   └── transcriber.py         # Whisper + text loader
│   ├── search/
│   │   └── meeting_search.py      # Semantic meeting search
│   └── api/
│       └── main.py                # FastAPI endpoints
├── tests/
│   └── test_meeting.py            # 8 unit tests
└── data/sample_meetings/          # Sample transcripts
```

## Resume Talking Points

- Built meeting intelligence platform processing transcripts to extract action items, decisions, and open questions using LLM with structured JSON output schemas
- Implemented email/Slack digest generation that formats meeting insights into ready-to-send markdown — owner attribution on every action item
- Built semantic search over meeting history enabling queries like "what did we decide about pricing last quarter?" across all past meetings
- Integrated Whisper transcription pipeline supporting audio upload (mp3, mp4, wav) with speaker diarization
