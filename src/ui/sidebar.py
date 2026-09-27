import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk

NO_MODELS = "No models found"


class Sidebar:
    def __init__(self, parent, app):
        self.app = app  # FluffyMainWindow: owns services + callbacks
        self.frame = ctk.CTkFrame(parent, width=260)
        self.chat_buttons = {}

        self._section("Model")
        self.model_menu = ctk.CTkOptionMenu(self.frame, values=[NO_MODELS])
        self.model_menu.pack(padx=10, pady=5)
        ctk.CTkButton(self.frame, text="Refresh models", command=self.refresh_models).pack(
            padx=10, pady=(0, 5)
        )

        self._section("System")
        self.cpu_label = ctk.CTkLabel(self.frame, text="CPU: --")
        self.cpu_label.pack()
        self.ram_label = ctk.CTkLabel(self.frame, text="RAM: --")
        self.ram_label.pack()

        self._section("Chats")
        ctk.CTkButton(self.frame, text="+ New chat", command=app.on_new_chat).pack(padx=10, pady=5)
        self.chat_list_frame = ctk.CTkScrollableFrame(self.frame, height=180)
        self.chat_list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self._section("Options")
        self.context_switch = ctk.CTkSwitch(
            self.frame, text="Keep context", command=self._on_context_toggle
        )
        self.context_switch.select()
        self.context_switch.pack(pady=3)

        self.rag_switch = ctk.CTkSwitch(self.frame, text="Use my files (RAG)")
        self.rag_switch.pack(pady=3)
        ctk.CTkButton(self.frame, text="Add files to knowledge", command=self._add_files).pack(
            padx=10, pady=3
        )
        self.rag_label = ctk.CTkLabel(self.frame, text="", wraplength=220, justify="left")
        self.rag_label.pack(padx=10, pady=(0, 8))

        self.refresh_models()
        self.update_rag_label()

    def _section(self, title):
        ctk.CTkLabel(self.frame, text=title, font=("Arial", 15, "bold")).pack(pady=(10, 4))

    # ---------- models ----------
    def refresh_models(self):
        models = self.app.ollama.get_available_models() or [NO_MODELS]
        self.model_menu.configure(values=models)
        self.model_menu.set(models[0])

    def get_current_model(self):
        m = self.model_menu.get()
        return None if m == NO_MODELS else m

    # ---------- system monitor ----------
    def update_system_stats(self, cpu, ram):
        self.cpu_label.configure(text=f"CPU: {cpu:.0f}%")
        self.ram_label.configure(text=f"RAM: {ram:.0f}%")

    # ---------- chats ----------
    def add_chat_button(self, chat_id, name):
        btn = ctk.CTkButton(
            self.chat_list_frame, text=name, command=lambda: self.app.on_chat_selected(chat_id)
        )
        btn.pack(fill="x", padx=5, pady=2)
        btn.bind("<Button-3>", lambda e: self._chat_menu(e, chat_id))
        self.chat_buttons[chat_id] = btn

    def _chat_menu(self, event, chat_id):
        menu = tk.Menu(self.frame, tearoff=0)
        menu.add_command(label="Rename", command=lambda: self._rename(chat_id))
        menu.add_command(label="Delete", command=lambda: self.app.on_delete_chat(chat_id))
        menu.tk_popup(event.x_root, event.y_root)

    def _rename(self, chat_id):
        name = ctk.CTkInputDialog(text="New name:", title="Rename chat").get_input()
        if self.app.chats.rename_chat(chat_id, name):
            self.chat_buttons[chat_id].configure(text=name.strip())

    def remove_chat_button(self, chat_id):
        btn = self.chat_buttons.pop(chat_id, None)
        if btn:
            btn.destroy()

    def _on_context_toggle(self):
        self.app.chats.toggle_context(self.context_switch.get())

    # ---------- RAG ----------
    def rag_enabled(self):
        return bool(self.rag_switch.get())

    def _add_files(self):
        paths = filedialog.askopenfilenames(
            title="Add files",
            filetypes=[("Documents", "*.txt *.md *.pdf *.py *.csv *.json"), ("All", "*.*")],
        )
        if paths:
            self.app.on_add_files(paths)

    def update_rag_label(self, text=None):
        if text is None:
            srcs = self.app.rag.sources()
            text = f"{len(srcs)} file(s) indexed" if srcs else "No files indexed"
        self.rag_label.configure(text=text)
