"""
src/search/meeting_search.py
Semantic search across meeting history using embeddings.
Lets you ask: "What did we decide about the pricing model in Q3?"
"""
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from loguru import logger

class MeetingSearchIndex:
    """
    Stores meeting insights and enables semantic search.
    Uses cosine similarity on embeddings of summaries + action items.
    """

    def __init__(self, embedder=None):
        self.embedder = embedder
        self.meetings: List[Dict] = []
        self.embeddings: Optional[np.ndarray] = None

    def add_meeting(self, insights_dict: Dict):
        """Add a processed meeting to the index."""
        self.meetings.append(insights_dict)
        # Rebuild embeddings
        if self.embedder:
            texts = [self._meeting_to_text(m) for m in self.meetings]
            self.embeddings = self.embedder.encode(texts, normalize_embeddings=True)
        logger.info(f"Index now has {len(self.meetings)} meetings")

    def search(self, query: str, top_k: int = 5) -> List[Tuple[Dict, float]]:
        """Search meetings by semantic similarity."""
        if not self.meetings:
            return []
        if self.embedder is None or self.embeddings is None:
            return self._keyword_search(query, top_k)
        q_emb = self.embedder.encode([query], normalize_embeddings=True)[0]
        sims  = self.embeddings @ q_emb
        idxs  = np.argsort(sims)[::-1][:top_k]
        return [(self.meetings[i], float(sims[i])) for i in idxs]

    def _keyword_search(self, query: str, top_k: int) -> List[Tuple[Dict, float]]:
        """Fallback: keyword search when no embedder available."""
        q_lower = query.lower()
        scored  = []
        for m in self.meetings:
            text  = self._meeting_to_text(m).lower()
            score = sum(1 for word in q_lower.split() if word in text) / max(len(q_lower.split()), 1)
            scored.append((m, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def _meeting_to_text(self, m: Dict) -> str:
        parts = [m.get("title",""), m.get("summary","")]
        parts += [a.get("description","") for a in m.get("action_items",[])]
        parts += [d.get("description","") for d in m.get("decisions",[])]
        parts += m.get("topics",[])
        return " ".join(filter(None, parts))

    def save(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.meetings, f, indent=2, default=str)

    def load(self, path: str):
        if Path(path).exists():
            with open(path) as f:
                self.meetings = json.load(f)