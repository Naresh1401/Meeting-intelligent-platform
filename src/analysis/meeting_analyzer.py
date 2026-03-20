"""
src/analysis/meeting_analyzer.py
==================================
Extracts structured intelligence from meeting transcripts:
  - Executive summary
  - Action items with owners and due dates
  - Key decisions made
  - Open questions / blockers
  - Topics discussed
  - Sentiment analysis per speaker

This solves the real problem: 80% of meeting insights are lost within 24 hours.
"""

import re
import json
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class ActionItem:
    description: str
    owner:       Optional[str]  = None
    due_date:    Optional[str]  = None
    priority:    str            = "medium"  # high / medium / low


@dataclass
class Decision:
    description: str
    made_by:     Optional[str] = None
    rationale:   Optional[str] = None


@dataclass
class MeetingInsights:
    """Full structured intelligence extracted from a meeting."""
    title:           str
    date:            Optional[str]
    duration_mins:   Optional[int]
    participants:    List[str]
    summary:         str
    action_items:    List[ActionItem]
    decisions:       List[Decision]
    open_questions:  List[str]
    topics:          List[str]
    key_quotes:      List[str]
    next_meeting:    Optional[str]
    sentiment:       str  # positive / neutral / negative / mixed

    def to_dict(self) -> Dict:
        return {
            "title":          self.title,
            "date":           self.date,
            "duration_mins":  self.duration_mins,
            "participants":   self.participants,
            "summary":        self.summary,
            "action_items":   [{"description": a.description, "owner": a.owner,
                                "due_date": a.due_date, "priority": a.priority}
                               for a in self.action_items],
            "decisions":      [{"description": d.description, "made_by": d.made_by,
                                "rationale": d.rationale} for d in self.decisions],
            "open_questions": self.open_questions,
            "topics":         self.topics,
            "key_quotes":     self.key_quotes,
            "next_meeting":   self.next_meeting,
            "sentiment":      self.sentiment,
        }

    def to_summary_email(self) -> str:
        """Format insights as a ready-to-send email digest."""
        lines = [
            f"## Meeting Summary: {self.title}",
            f"**Date:** {self.date or 'Unknown'} | **Duration:** {self.duration_mins or '?'} mins",
            f"**Attendees:** {', '.join(self.participants) if self.participants else 'Unknown'}",
            "",
            "### Summary",
            self.summary,
            "",
        ]
        if self.action_items:
            lines += ["### Action Items"]
            for a in self.action_items:
                owner    = f" (@{a.owner})" if a.owner else ""
                due      = f" — due {a.due_date}" if a.due_date else ""
                priority = f" [{a.priority.upper()}]" if a.priority != "medium" else ""
                lines.append(f"- [ ] {a.description}{owner}{due}{priority}")
            lines.append("")
        if self.decisions:
            lines += ["### Decisions Made"]
            for d in self.decisions:
                lines.append(f"- ✅ {d.description}")
            lines.append("")
        if self.open_questions:
            lines += ["### Open Questions / Blockers"]
            for q in self.open_questions:
                lines.append(f"- ❓ {q}")
            lines.append("")
        if self.next_meeting:
            lines += [f"### Next Meeting", self.next_meeting, ""]
        return "\n".join(lines)


ANALYSIS_SYSTEM_PROMPT = """You are an expert meeting analyst. Extract structured insights from meeting transcripts.

Return ONLY valid JSON with this exact structure:
{
  "title": "Meeting title or topic inferred from content",
  "date": "Date if mentioned, else null",
  "duration_mins": estimated duration as integer or null,
  "participants": ["list", "of", "participant", "names"],
  "summary": "2-3 sentence executive summary of what was discussed and decided",
  "action_items": [
    {"description": "specific task", "owner": "person name or null", "due_date": "date or null", "priority": "high|medium|low"}
  ],
  "decisions": [
    {"description": "what was decided", "made_by": "who decided or null", "rationale": "why or null"}
  ],
  "open_questions": ["unanswered questions or blockers"],
  "topics": ["main", "topics", "discussed"],
  "key_quotes": ["notable quotes verbatim, max 3"],
  "next_meeting": "next meeting details if mentioned, else null",
  "sentiment": "positive|neutral|negative|mixed"
}"""


class MeetingAnalyzer:
    """Analyzes meeting transcripts using LLM to extract structured insights."""

    def __init__(self, llm):
        self.llm = llm

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5))
    def analyze(self, transcript: str, title: str = "Meeting") -> MeetingInsights:
        """Extract structured insights from a transcript."""
        prompt = f"""Analyze this meeting transcript and extract all structured insights.

Meeting Title: {title}

Transcript:
---
{transcript[:8000]}
---

Extract all action items, decisions, open questions, and key information. Return JSON only."""

        raw  = self.llm.generate(ANALYSIS_SYSTEM_PROMPT, prompt)
        data = self._parse(raw)
        return self._hydrate(data, title)

    def generate_digest(self, insights: MeetingInsights) -> str:
        """Generate a formatted Slack/email digest."""
        return insights.to_summary_email()

    def _parse(self, raw: str) -> Dict:
        clean = re.sub(r"```(?:json)?|```", "", raw).strip()
        try:
            return json.loads(clean)
        except:
            match = re.search(r'\{.*\}', clean, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
        logger.warning("Failed to parse LLM response, returning empty")
        return {}

    def _hydrate(self, data: Dict, fallback_title: str) -> MeetingInsights:
        action_items = [
            ActionItem(
                description = a.get("description", ""),
                owner       = a.get("owner"),
                due_date    = a.get("due_date"),
                priority    = a.get("priority", "medium"),
            )
            for a in data.get("action_items", [])
            if a.get("description")
        ]
        decisions = [
            Decision(
                description = d.get("description", ""),
                made_by     = d.get("made_by"),
                rationale   = d.get("rationale"),
            )
            for d in data.get("decisions", [])
            if d.get("description")
        ]
        return MeetingInsights(
            title          = data.get("title", fallback_title),
            date           = data.get("date"),
            duration_mins  = data.get("duration_mins"),
            participants   = data.get("participants", []),
            summary        = data.get("summary", "No summary available."),
            action_items   = action_items,
            decisions      = decisions,
            open_questions = data.get("open_questions", []),
            topics         = data.get("topics", []),
            key_quotes     = data.get("key_quotes", []),
            next_meeting   = data.get("next_meeting"),
            sentiment      = data.get("sentiment", "neutral"),
        )
