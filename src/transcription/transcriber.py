"""
src/transcription/transcriber.py
==================================
Audio transcription using OpenAI Whisper with speaker diarization simulation.

Production pipeline:
  Audio file → Whisper transcription → Speaker diarization → Formatted transcript

Speaker diarization (who said what) is one of the hardest parts of meeting intelligence.
Options by accuracy/cost:
  1. pyannote.audio       — best quality, local, requires HuggingFace token
  2. AssemblyAI API       — managed diarization, $0.001/min
  3. Simple heuristic     — speaker change detection (implemented here)
"""

import os
import re
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
from loguru import logger


@dataclass
class TranscriptSegment:
    speaker:    str
    text:       str
    start_time: Optional[float] = None
    end_time:   Optional[float] = None


@dataclass
class Transcript:
    segments:     List[TranscriptSegment]
    full_text:    str
    duration_sec: Optional[float] = None
    language:     str = "en"

    def to_formatted_text(self) -> str:
        """Format transcript as 'Speaker: text' lines."""
        return "\n".join(
            f"{s.speaker}: {s.text}"
            for s in self.segments
        )

    @classmethod
    def from_plain_text(cls, text: str) -> "Transcript":
        """Parse a plain text transcript with 'Name: text' format."""
        segments = []
        pattern  = re.compile(r'^([A-Z][^:]{1,30}):\s*(.+)$', re.MULTILINE)
        for match in pattern.finditer(text):
            segments.append(TranscriptSegment(
                speaker = match.group(1).strip(),
                text    = match.group(2).strip(),
            ))
        if not segments:
            segments = [TranscriptSegment(speaker="Unknown", text=text)]
        return cls(segments=segments, full_text=text)


class WhisperTranscriber:
    """
    OpenAI Whisper-based audio transcription.
    Supports: mp3, mp4, wav, m4a, webm, ogg (max 25MB via API)
    """

    SUPPORTED_FORMATS = {'.mp3', '.mp4', '.wav', '.m4a', '.webm', '.ogg', '.flac'}

    def __init__(self, api_key: Optional[str] = None):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))

    def transcribe(self, audio_path: str, language: str = "en") -> Transcript:
        """Transcribe audio file using Whisper API."""
        import pathlib
        ext = pathlib.Path(audio_path).suffix.lower()
        if ext not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {ext}. Supported: {self.SUPPORTED_FORMATS}")

        logger.info(f"Transcribing: {audio_path}")
        with open(audio_path, "rb") as f:
            response = self.client.audio.transcriptions.create(
                model    = "whisper-1",
                file     = f,
                language = language,
                response_format = "verbose_json",  # includes word-level timestamps
            )

        full_text = response.text
        segments  = [
            TranscriptSegment(
                speaker    = f"Speaker {i % 3 + 1}",  # naive assignment; use pyannote for real diarization
                text       = seg.text.strip(),
                start_time = seg.start,
                end_time   = seg.end,
            )
            for i, seg in enumerate(response.segments or [])
        ]

        duration = response.segments[-1].end if response.segments else None
        return Transcript(segments=segments, full_text=full_text,
                          duration_sec=duration, language=language)


class HeuristicDiarizer:
    """
    Simple heuristic speaker diarization based on pause detection.

    Not production-grade — use pyannote.audio or AssemblyAI for real diarization.
    This is useful when you only have a text transcript (no audio).
    """

    def diarize(self, text: str, num_speakers: int = 2) -> List[TranscriptSegment]:
        """Split a monologue into speaker turns based on sentence boundaries."""
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        segments  = []
        speaker_idx = 0

        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
            # Simple turn-taking: change speaker on question marks or after ~3 sentences
            if i > 0 and (sentences[i-1].endswith('?') or i % 4 == 0):
                speaker_idx = (speaker_idx + 1) % num_speakers
            segments.append(TranscriptSegment(
                speaker = f"Speaker {speaker_idx + 1}",
                text    = sentence.strip(),
            ))
        return segments


class TextTranscriptLoader:
    """Load a pre-existing text transcript file."""

    def load(self, path: str) -> Transcript:
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
        return Transcript.from_plain_text(text)
