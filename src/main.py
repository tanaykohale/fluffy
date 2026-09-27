import argparse
import os

import customtkinter as ctk

from src.services.chat_manager import ChatManager
from src.services.ollama_service import OllamaService
from src.services.rag import RagIndex
from src.services.system_monitor import SystemMonitor
from src.ui.main_window import FluffyMainWindow

DEFAULT_EMBED_MODEL = os.environ.get("FLUFFY_EMBED_MODEL", "nomic-embed-text")


def main():
    parser = argparse.ArgumentParser(description="Fluffy - chat with local LLMs via Ollama")
    parser.add_argument("--ollama-url", default=os.environ.get("OLLAMA_HOST", OllamaService.DEFAULT_URL))
    parser.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL)
    args = parser.parse_args()

    ollama = OllamaService(args.ollama_url)
    rag = RagIndex(
        embed_fn=lambda texts: ollama.embed(args.embed_model, texts),
        path=os.path.expanduser("~/.fluffy/rag_index.json"),
    )

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    root.title("Fluffy AI Chat")
    root.geometry("1050x720")

    monitor = SystemMonitor()
    FluffyMainWindow(root, ollama, ChatManager(), rag, monitor, args.embed_model)
    root.protocol("WM_DELETE_WINDOW", lambda: (monitor.stop_monitoring(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()
