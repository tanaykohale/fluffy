import queue
import threading

import customtkinter as ctk

from src.services.ollama_service import OllamaError
from src.ui.chat_display import ChatDisplay
from src.ui.sidebar import Sidebar


class FluffyMainWindow:
    """Wires the UI to the services. Long work runs on threads; UI updates go through root.after."""

    def __init__(self, root, ollama, chats, rag, monitor, embed_model):
        self.root, self.ollama, self.chats, self.rag = root, ollama, chats, rag
        self.embed_model = embed_model
        self._ui_queue = queue.Queue()  # worker threads -> Tk main thread

        main = ctk.CTkFrame(root)
        main.pack(fill="both", expand=True, padx=10, pady=10)
        self.sidebar = Sidebar(main, self)
        self.display = ChatDisplay(main, self.on_send)
        self.sidebar.frame.pack(side="left", fill="y", padx=(0, 10))
        self.display.frame.pack(side="right", fill="both", expand=True)

        for cid, chat in self.chats.chats.items():
            self.sidebar.add_chat_button(cid, chat["name"])
        if self.chats.current_chat:
            self.on_chat_selected(self.chats.current_chat)

        self._drain_ui_queue()
        monitor.start_monitoring(lambda c, r: self.ui(self.sidebar.update_system_stats, c, r))

    def ui(self, fn, *args):
        """Thread-safe: queue fn to run on the Tk main thread (Tk itself is not thread-safe)."""
        self._ui_queue.put((fn, args))

    def _drain_ui_queue(self):
        try:
            while True:
                fn, args = self._ui_queue.get_nowait()
                fn(*args)
        except queue.Empty:
            pass
        try:
            self.root.after(30, self._drain_ui_queue)
        except Exception:  # window closed
            pass

    # ---------- chats ----------
    def on_new_chat(self):
        cid = self.chats.create_new_chat()
        self.sidebar.add_chat_button(cid, self.chats.chats[cid]["name"])
        self.on_chat_selected(cid)

    def on_chat_selected(self, cid):
        self.chats.current_chat = cid
        self.display.show_chat(self.chats.chats[cid]["name"], self.chats.get_messages(cid))

    def on_delete_chat(self, cid):
        self.chats.delete_chat(cid)
        self.sidebar.remove_chat_button(cid)
        if self.chats.current_chat:
            self.on_chat_selected(self.chats.current_chat)
        else:
            self.display.show_chat("New chat", [])

    # ---------- sending ----------
    def on_send(self, message):
        if not message:
            return
        model = self.sidebar.get_current_model()
        if not model:
            self.display.append_message("assistant", "No model found. Start Ollama and pull a model, then click 'Refresh models'.")
            return
        if not self.chats.current_chat:
            self.on_new_chat()
        use_rag = self.sidebar.rag_enabled()
        history_msgs = self.chats.build_messages(message)
        self.chats.add_message("user", message)
        self.display.append_message("user", message)
        self.display.set_busy(True)
        threading.Thread(
            target=self._generate, args=(model, message, history_msgs, use_rag), daemon=True
        ).start()

    def _generate(self, model, message, msgs, use_rag):
        reply = ""
        try:
            if use_rag and self.rag.chunks:
                system = self.rag.build_prompt(message, self.rag.search(message))
                if system:
                    msgs = [{"role": "system", "content": system}] + msgs
            self.ui(self.display.start_stream)
            for chunk in self.ollama.stream_chat(model, msgs):
                reply += chunk
                self.ui(self.display.stream_chunk, chunk)
        except OllamaError as e:
            reply = reply or f"[error] {e}"
            self.ui(self.display.stream_chunk, f"[error] {e}")
        finally:
            self.ui(self._finish, reply)

    def _finish(self, reply):
        self.display.end_stream()
        if reply:
            self.chats.add_message("assistant", reply)
        self.display.set_busy(False)

    # ---------- RAG ----------
    def on_add_files(self, paths):
        self.sidebar.update_rag_label("Indexing...")

        def work():
            errors = []
            for p in paths:
                try:
                    self.rag.add_file(p)
                except (OllamaError, ValueError, OSError) as e:
                    errors.append(f"{p.split('/')[-1]}: {e}")
            self.rag.save()
            self.ui(self.sidebar.update_rag_label)
            for err in errors:
                self.ui(self.display.append_message, "assistant", f"[RAG] {err}")

        threading.Thread(target=work, daemon=True).start()
