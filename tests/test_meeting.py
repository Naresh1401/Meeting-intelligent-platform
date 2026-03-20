"""tests/test_meeting.py"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.analysis.meeting_analyzer import MeetingAnalyzer, MeetingInsights, ActionItem, Decision
from src.transcription.transcriber import Transcript, TranscriptSegment

SAMPLE_TRANSCRIPT = """
Sarah: Let's start the Q3 planning meeting.
James: We need to prioritize the onboarding redesign. I think it should be priority one.
Sarah: Agreed. The dashboard reporting moves to Q4 — it's too large for Q3.
James: Tom will own the API rate limit increase. Due by end of September.
Lisa: Decided — onboarding is priority one. James, can you write a scope doc by Friday?
James: Yes, will do.
Sarah: Next meeting is October 16th.
"""

class MockLLM:
    def generate(self, system, user):
        import json
        return json.dumps({
            "title": "Q3 Planning",
            "date": "2024-09-18",
            "duration_mins": 35,
            "participants": ["Sarah", "James", "Tom", "Lisa"],
            "summary": "Team aligned on Q3 priorities: onboarding redesign as P1, reporting moved to Q4.",
            "action_items": [
                {"description": "Write scope doc for infrastructure", "owner": "James", "due_date": "Friday", "priority": "high"},
                {"description": "Circulate roadmap doc", "owner": "Sarah", "due_date": "Tomorrow", "priority": "medium"},
            ],
            "decisions": [
                {"description": "Onboarding redesign is Q3 priority one", "made_by": "Lisa", "rationale": "Highest customer impact"},
                {"description": "Reporting dashboard moves to Q4", "made_by": "Lisa", "rationale": "Too large for Q3"},
            ],
            "open_questions": ["How to staff infrastructure without impacting onboarding?"],
            "topics": ["Q3 roadmap", "onboarding", "reporting", "API limits"],
            "key_quotes": ["The onboarding improvements are gold — Tom"],
            "next_meeting": "October 16th — Q3 progress check-in",
            "sentiment": "positive"
        })

def test_analyze_returns_insights():
    analyzer = MeetingAnalyzer(MockLLM())
    insights = analyzer.analyze(SAMPLE_TRANSCRIPT, "Q3 Planning")
    assert isinstance(insights, MeetingInsights)
    assert insights.title == "Q3 Planning"
    assert len(insights.action_items) == 2
    assert len(insights.decisions) == 2
    print("✅ analyze returns structured insights")

def test_action_items_have_owners():
    analyzer = MeetingAnalyzer(MockLLM())
    insights = analyzer.analyze(SAMPLE_TRANSCRIPT)
    owners = [a.owner for a in insights.action_items if a.owner]
    assert len(owners) >= 1
    print(f"✅ action items have owners: {owners}")

def test_decisions_extracted():
    analyzer = MeetingAnalyzer(MockLLM())
    insights = analyzer.analyze(SAMPLE_TRANSCRIPT)
    assert len(insights.decisions) >= 1
    assert any("onboarding" in d.description.lower() for d in insights.decisions)
    print("✅ decisions extracted correctly")

def test_email_digest_format():
    analyzer = MeetingAnalyzer(MockLLM())
    insights = analyzer.analyze(SAMPLE_TRANSCRIPT, "Q3 Planning")
    digest   = insights.to_summary_email()
    assert "Q3 Planning" in digest
    assert "Action Items" in digest
    assert "Decisions Made" in digest
    assert "James" in digest   # Owner appears in action items
    print("✅ email digest formatted correctly")

def test_to_dict_serializable():
    import json
    analyzer = MeetingAnalyzer(MockLLM())
    insights = analyzer.analyze(SAMPLE_TRANSCRIPT)
    d = insights.to_dict()
    s = json.dumps(d)  # Should not raise
    assert isinstance(d["action_items"], list)
    assert isinstance(d["decisions"], list)
    print("✅ insights serializable to JSON")

def test_transcript_from_plain_text():
    text = "Alice: Hello everyone.\nBob: Hi Alice, let's get started.\nAlice: First agenda item is the budget."
    t    = Transcript.from_plain_text(text)
    assert len(t.segments) == 3
    assert t.segments[0].speaker == "Alice"
    assert t.segments[1].speaker == "Bob"
    print(f"✅ transcript parsed: {len(t.segments)} segments")

def test_transcript_formatted():
    segs = [
        TranscriptSegment("Alice", "Good morning."),
        TranscriptSegment("Bob", "Morning! Ready to start?"),
    ]
    t    = Transcript(segments=segs, full_text="...")
    fmt  = t.to_formatted_text()
    assert "Alice: Good morning." in fmt
    assert "Bob: Morning!" in fmt
    print("✅ transcript formats correctly")

def test_sentiment_field():
    analyzer = MeetingAnalyzer(MockLLM())
    insights = analyzer.analyze(SAMPLE_TRANSCRIPT)
    assert insights.sentiment in ["positive","negative","neutral","mixed"]
    print(f"✅ sentiment extracted: {insights.sentiment}")

if __name__ == "__main__":
    tests = [
        test_analyze_returns_insights, test_action_items_have_owners,
        test_decisions_extracted, test_email_digest_format,
        test_to_dict_serializable, test_transcript_from_plain_text,
        test_transcript_formatted, test_sentiment_field,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"❌ {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} tests passed")
