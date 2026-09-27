import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class FakeResponse:
    def __init__(self, status=200, json_data=None, lines=None):
        self.status_code = status
        self._json = json_data
        self._lines = lines or []

    def json(self):
        return self._json

    def raise_for_status(self):
        import requests
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def iter_lines(self):
        for l in self._lines:
            yield json.dumps(l).encode() if isinstance(l, dict) else l

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeSession:
    """Records requests and replays canned responses keyed by URL suffix."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def _resp(self, method, url, **kw):
        self.calls.append((method, url, kw))
        for suffix, resp in self.routes.items():
            if url.endswith(suffix):
                if isinstance(resp, Exception):
                    raise resp
                return resp
        return FakeResponse(404)

    def get(self, url, **kw):
        return self._resp("GET", url, **kw)

    def post(self, url, **kw):
        return self._resp("POST", url, **kw)


@pytest.fixture
def fake_session():
    return FakeSession


@pytest.fixture
def fake_response():
    return FakeResponse


def keyword_embed(texts):
    """Deterministic toy embedder: bag of a few keywords."""
    vocab = ["cat", "dog", "invoice", "python", "rain"]
    return [[t.lower().count(w) + 0.01 for w in vocab] for t in texts]


@pytest.fixture
def embed():
    return keyword_embed
