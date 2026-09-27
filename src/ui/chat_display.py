import customtkinter as ctk

LABELS = {"user": "You", "assistant": "Fluffy"}


class ChatDisplay:
    def __init__(self, parent, on_send):
        self.frame = ctk.CTkFrame(parent)

        self.title = ctk.CTkLabel(self.frame, text="New chat", font=("Arial", 16, "bold"))
        self.title.pack(pady=10)

        self.text = ctk.CTkTextbox(self.frame, wrap="word", state="disabled")
        self.text.pack(fill="both", expand=True, padx=10, pady=10)
        self.text.tag_config("user", foreground="#7cc4ff")
        self.text.tag_config("assistant", foreground="#e6e6e6")
        self.text.tag_config("meta", foreground="#8a8a8a")

        self.progress = ctk.CTkProgressBar(self.frame, mode="indeterminate")
        self.progress.pack(fill="x", padx=10)
        self.progress.set(0)

        row = ctk.CTkFrame(self.frame)
        row.pack(fill="x", padx=10, pady=10)
        self.entry = ctk.CTkEntry(row, placeholder_text="Type a message...")
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.send_btn = ctk.CTkButton(row, text="Send", command=lambda: on_send(self.take_input()))
        self.send_btn.pack(side="right")
        self.entry.bind("<Return>", lambda e: on_send(self.take_input()))

    def take_input(self):
        msg = self.entry.get().strip()
        self.entry.delete(0, "end")
        return msg

    def set_busy(self, busy):
        self.send_btn.configure(state="disabled" if busy else "normal")
        if busy:
            self.progress.start()
        else:
            self.progress.stop()
            self.progress.set(0)

    def show_chat(self, name, messages):
        self.title.configure(text=name)
        self._edit(lambda: self.text.delete("1.0", "end"))
        for m in messages:
            self.append_message(m["sender"], m["message"], m.get("timestamp", ""))

    def append_message(self, sender, message, timestamp=""):
        def do():
            self.text.insert("end", f"{LABELS.get(sender, sender)}  {timestamp}\n", "meta")
            self.text.insert("end", message + "\n\n", sender)
        self._edit(do)

    # streaming: header once, then chunks
    def start_stream(self):
        self._edit(lambda: self.text.insert("end", "Fluffy\n", "meta"))

    def stream_chunk(self, chunk):
        self._edit(lambda: self.text.insert("end", chunk, "assistant"))

    def end_stream(self):
        self._edit(lambda: self.text.insert("end", "\n\n"))

    def _edit(self, fn):
        self.text.configure(state="normal")
        fn()
        self.text.configure(state="disabled")
        self.text.see("end")
