"""Minimal local RAG: chunk your files, embed them with an Ollama embedding model,
and retrieve the most similar chunks for a question. No vector DB, no internet.

The index is a JSON file (default ~/.fluffy/rag_index.json).
"""
import json
import math
import os

TEXT_EXTENSIONS = {".txt", ".md", ".py", ".csv", ".json", ".html", ".js", ".rst", ".log"}


def chunk_text(text, size=800, overlap=150):
    """Split text into overlapping character windows, breaking on whitespace when possible."""
    if size <= overlap:
        raise ValueError("size must be larger than overlap")
    text = " ".join(text.split())
    if not text:
        return []
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            space = text.rfind(" ", start + size // 2, end)
            if space != -1:
                end = space
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return [c for c in chunks if c]


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def read_file(path):
    """Read a text-like file (or a PDF if pypdf is installed)."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as e:
            raise ValueError("Install 'pypdf' to index PDF files") from e
        return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    if ext not in TEXT_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}")
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()


class RagIndex:
    """``embed_fn(list[str]) -> list[list[float]]`` is injected so tests need no Ollama."""

    def __init__(self, embed_fn, path=None):
        self.embed_fn = embed_fn
        self.path = path
        self.chunks = []  # [{"source", "text", "vector"}]
        if path and os.path.exists(path):
            self.load()

    # ---------- build ----------
    def add_text(self, text, source="text"):
        pieces = chunk_text(text)
        if not pieces:
            return 0
        vectors = self.embed_fn(pieces)
        self.chunks.extend(
            {"source": source, "text": t, "vector": v} for t, v in zip(pieces, vectors)
        )
        return len(pieces)

    def add_file(self, path):
        self.remove_source(os.path.basename(path))
        return self.add_text(read_file(path), source=os.path.basename(path))

    def remove_source(self, source):
        self.chunks = [c for c in self.chunks if c["source"] != source]

    def sources(self):
        return sorted({c["source"] for c in self.chunks})

    def clear(self):
        self.chunks = []

    # ---------- query ----------
    def search(self, query, k=4, min_score=0.0):
        if not self.chunks:
            return []
        qv = self.embed_fn([query])[0]
        scored = [(cosine(qv, c["vector"]), c) for c in self.chunks]
        scored.sort(key=lambda s: s[0], reverse=True)
        return [
            {"score": s, "source": c["source"], "text": c["text"]}
            for s, c in scored[:k]
            if s >= min_score
        ]

    @staticmethod
    def build_prompt(question, hits):
        """Wrap retrieved chunks into a grounded system message."""
        if not hits:
            return None
        context = "\n\n".join(f"[{h['source']}]\n{h['text']}" for h in hits)
        return (
            "Answer using the context from the user's files below. "
            "Cite the file name in brackets when you use it. "
            "If the context does not contain the answer, say so.\n\n"
            f"CONTEXT:\n{context}"
        )

    # ---------- persistence ----------
    def save(self):
        if not self.path:
            return
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f)

    def load(self):
        with open(self.path, encoding="utf-8") as f:
            self.chunks = json.load(f)
