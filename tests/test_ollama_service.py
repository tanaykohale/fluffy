import pytest
import requests

from src.services.ollama_service import OllamaError, OllamaService


def test_models_listed(fake_session, fake_response):
    s = fake_session({"/api/tags": fake_response(json_data={"models": [{"name": "llama3"}, {"name": "mistral"}]})})
    assert OllamaService(session=s).get_available_models() == ["llama3", "mistral"]


def test_models_empty_when_ollama_down(fake_session):
    s = fake_session({"/api/tags": requests.ConnectionError("refused")})
    svc = OllamaService(session=s)
    assert svc.get_available_models() == []
    assert svc.is_running() is False


def test_stream_chat_yields_chunks_and_stops_on_done(fake_session, fake_response):
    lines = [
        {"message": {"content": "Hel"}},
        b"",
        {"message": {"content": "lo"}},
        {"message": {"content": ""}, "done": True},
        {"message": {"content": "IGNORED"}},
    ]
    s = fake_session({"/api/chat": fake_response(lines=lines)})
    svc = OllamaService(session=s)
    msgs = [{"role": "user", "content": "hi"}]
    assert list(svc.stream_chat("llama3", msgs)) == ["Hel", "lo"]
    _, url, kw = s.calls[0]
    assert kw["json"] == {"model": "llama3", "messages": msgs, "stream": True}
    assert kw["stream"] is True


def test_chat_joins_stream(fake_session, fake_response):
    s = fake_session({"/api/chat": fake_response(lines=[{"message": {"content": "a"}}, {"message": {"content": "b"}, "done": True}])})
    assert OllamaService(session=s).chat("m", []) == "ab"


def test_stream_chat_surfaces_ollama_error(fake_session, fake_response):
    s = fake_session({"/api/chat": fake_response(lines=[{"error": "model 'x' not found"}])})
    with pytest.raises(OllamaError, match="not found"):
        list(OllamaService(session=s).stream_chat("x", []))


def test_stream_chat_requires_model():
    with pytest.raises(OllamaError):
        list(OllamaService(session=object()).stream_chat(None, []))


def test_stream_chat_connection_error(fake_session):
    s = fake_session({"/api/chat": requests.ConnectionError("refused")})
    with pytest.raises(OllamaError, match="Could not reach"):
        list(OllamaService(session=s).stream_chat("m", []))


def test_embed_new_api(fake_session, fake_response):
    s = fake_session({"/api/embed": fake_response(json_data={"embeddings": [[1, 2], [3, 4]]})})
    assert OllamaService(session=s).embed("nomic-embed-text", ["a", "b"]) == [[1, 2], [3, 4]]


def test_embed_falls_back_to_legacy_api(fake_session, fake_response):
    s = fake_session({
        "/api/embed": fake_response(404),
        "/api/embeddings": fake_response(json_data={"embedding": [0.5, 0.5]}),
    })
    assert OllamaService(session=s).embed("m", "one text") == [[0.5, 0.5]]
