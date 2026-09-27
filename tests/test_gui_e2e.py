"""End-to-end: real Tk window + a fake Ollama HTTP server on localhost.

Skipped automatically when there is no display (run under `xvfb-run` on Linux CI).
"""
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

tk = pytest.importorskip("tkinter")
ctk = pytest.importorskip("customtkinter")

SEEN = {}


class FakeOllama(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._json({"models": [{"name": "fake-model"}]})

    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.path == "/api/embed":
            self._json({"embeddings": [[t.count("fluffy") + 0.1, 1.0] for t in data["input"]]})
            return
        SEEN["last_chat"] = data
        self.send_response(200)
        self.end_headers()
        for word in ["Hello ", "from ", "fake!"]:
            self.wfile.write(json.dumps({"message": {"content": word}}).encode() + b"\n")
        self.wfile.write(json.dumps({"done": True, "message": {"content": ""}}).encode() + b"\n")


@pytest.fixture
def server():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), FakeOllama)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


@pytest.fixture
def root():
    try:
        r = ctk.CTk()
    except tk.TclError:
        pytest.skip("no display")
    yield r
    r.destroy()


def pump(root, until, timeout=10):
    end = time.time() + timeout
    while time.time() < end:
        root.update()
        if until():
            return True
        time.sleep(0.02)
    return False


def test_send_message_streams_reply_and_uses_rag(server, root, tmp_path):
    from src.services.chat_manager import ChatManager
    from src.services.ollama_service import OllamaService
    from src.services.rag import RagIndex
    from src.services.system_monitor import SystemMonitor
    from src.ui.main_window import FluffyMainWindow

    ollama = OllamaService(server)
    rag = RagIndex(lambda t: ollama.embed("e", t), path=str(tmp_path / "rag.json"))
    chats = ChatManager(store_path=str(tmp_path / "chats.json"), log=False)
    mon = SystemMonitor(interval=0.1)
    win = FluffyMainWindow(root, ollama, chats, rag, mon, "e")

    assert win.sidebar.get_current_model() == "fake-model"
    assert pump(root, lambda: "CPU: --" not in win.sidebar.cpu_label.cget("text"))

    # plain chat
    win.display.entry.insert(0, "hi")
    win.display.send_btn.invoke()
    assert pump(root, lambda: len(chats.get_messages()) == 2)
    assert chats.get_messages()[-1]["message"] == "Hello from fake!"
    assert "Hello from fake!" in win.display.text.get("1.0", "end")

    # RAG: index a file, enable switch, ask again -> system prompt carries the file
    note = tmp_path / "notes.md"
    note.write_text("fluffy is a local LLM desktop app")
    win.on_add_files([str(note)])
    assert pump(root, lambda: rag.sources() == ["notes.md"])
    win.sidebar.rag_switch.select()
    win.display.entry.insert(0, "what is fluffy?")
    win.display.send_btn.invoke()
    assert pump(root, lambda: len(chats.get_messages()) == 4)
    sent = SEEN["last_chat"]["messages"]
    assert sent[0]["role"] == "system" and "[notes.md]" in sent[0]["content"]
    assert sent[-1] == {"role": "user", "content": "what is fluffy?"}
    mon.stop_monitoring()
