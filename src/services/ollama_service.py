"""Thin, synchronous client for the local Ollama HTTP API.

Everything goes through one ``requests.Session`` so tests can swap it for a fake.
"""
import json

import requests


class OllamaError(RuntimeError):
    """Raised when Ollama is unreachable or returns an error."""


class OllamaService:
    DEFAULT_URL = "http://localhost:11434"

    def __init__(self, base_url=DEFAULT_URL, session=None, timeout=120):
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.timeout = timeout

    # ---------- models ----------
    def get_available_models(self):
        """Return installed model names, or [] if Ollama is not reachable."""
        try:
            r = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            r.raise_for_status()
            return [m["name"] for m in r.json().get("models", [])]
        except (requests.RequestException, ValueError, KeyError):
            return []

    def is_running(self):
        try:
            self.session.get(f"{self.base_url}/api/tags", timeout=2).raise_for_status()
            return True
        except requests.RequestException:
            return False

    # ---------- generation ----------
    def stream_chat(self, model, messages):
        """Yield response text chunks from /api/chat (streaming).

        ``messages`` is a list of {"role": "system"|"user"|"assistant", "content": str}.
        """
        if not model:
            raise OllamaError("No model selected.")
        payload = {"model": model, "messages": messages, "stream": True}
        try:
            with self.session.post(
                f"{self.base_url}/api/chat", json=payload, stream=True, timeout=self.timeout
            ) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    if "error" in data:
                        raise OllamaError(data["error"])
                    chunk = data.get("message", {}).get("content", "")
                    if chunk:
                        yield chunk
                    if data.get("done"):
                        break
        except requests.RequestException as e:
            raise OllamaError(f"Could not reach Ollama at {self.base_url}: {e}") from e

    def chat(self, model, messages):
        """Non-streaming convenience wrapper: returns the full reply text."""
        return "".join(self.stream_chat(model, messages))

    # ---------- embeddings (used by RAG) ----------
    def embed(self, model, texts):
        """Return one embedding vector per input text."""
        if isinstance(texts, str):
            texts = [texts]
        try:
            r = self.session.post(
                f"{self.base_url}/api/embed",
                json={"model": model, "input": texts},
                timeout=self.timeout,
            )
            if r.status_code == 404:  # older Ollama: one text per call
                return [self._embed_legacy(model, t) for t in texts]
            r.raise_for_status()
            return r.json()["embeddings"]
        except requests.RequestException as e:
            raise OllamaError(f"Embedding failed: {e}") from e

    def _embed_legacy(self, model, text):
        r = self.session.post(
            f"{self.base_url}/api/embeddings",
            json={"model": model, "prompt": text},
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()["embedding"]
