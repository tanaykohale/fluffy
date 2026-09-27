"""Chat sessions: create / rename / delete, context window, and JSON persistence."""
import json
import os
import uuid
from datetime import datetime

from src.utils.helpers import LogManager, TokenManager

DEFAULT_STORE = os.path.expanduser("~/.fluffy/chats.json")


class ChatManager:
    def __init__(self, store_path=DEFAULT_STORE, log=True):
        self.store_path = store_path
        self.log = log
        self.chats = {}  # chat_id -> {"name", "messages", "created_at", "last_active"}
        self.current_chat = None
        self.context_enabled = True
        self.max_history_tokens = 1000
        self.load()

    # ---------- sessions ----------
    def create_new_chat(self, name=None):
        chat_id = str(uuid.uuid4())
        now = datetime.now().isoformat(timespec="seconds")
        self.chats[chat_id] = {
            "name": name or f"Chat {len(self.chats) + 1}",
            "messages": [],
            "created_at": now,
            "last_active": now,
        }
        self.current_chat = chat_id
        self.save()
        return chat_id

    def rename_chat(self, chat_id, new_name):
        new_name = (new_name or "").strip()
        if chat_id in self.chats and new_name:
            self.chats[chat_id]["name"] = new_name
            self.save()
            return True
        return False

    def delete_chat(self, chat_id):
        if self.chats.pop(chat_id, None) is None:
            return False
        if self.current_chat == chat_id:
            self.current_chat = next(iter(self.chats), None)
        self.save()
        return True

    def get_messages(self, chat_id=None):
        chat = self.chats.get(chat_id or self.current_chat)
        return chat["messages"] if chat else []

    def toggle_context(self, enabled):
        self.context_enabled = bool(enabled)

    # ---------- messages ----------
    def add_message(self, sender, message):
        """sender is "user" or "assistant". Returns the stored message dict."""
        if not self.current_chat:
            self.create_new_chat()
        if self.log:
            LogManager.log_message(self.current_chat, sender, message)
        entry = {
            "id": str(uuid.uuid4()),
            "sender": sender,
            "message": message,
            "timestamp": datetime.now().strftime("%H:%M"),
            "tokens": TokenManager.count_tokens(message),
        }
        chat = self.chats[self.current_chat]
        chat["messages"].append(entry)
        chat["last_active"] = datetime.now().isoformat(timespec="seconds")
        self.save()
        return entry

    def build_messages(self, user_message, system_prompt=None):
        """Messages list for Ollama /api/chat, honouring the context toggle and token budget.

        Call this *before* storing ``user_message`` with add_message.
        """
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        if self.context_enabled:
            history, budget = [], self.max_history_tokens
            for m in reversed(self.get_messages()):
                budget -= m["tokens"]
                if budget < 0:
                    break
                history.append({"role": m["sender"], "content": m["message"]})
            msgs.extend(reversed(history))
        msgs.append({"role": "user", "content": user_message})
        return msgs

    # ---------- persistence ----------
    def save(self):
        if not self.store_path:
            return
        os.makedirs(os.path.dirname(self.store_path) or ".", exist_ok=True)
        with open(self.store_path, "w", encoding="utf-8") as f:
            json.dump({"chats": self.chats, "current": self.current_chat}, f, indent=2)

    def load(self):
        if not self.store_path or not os.path.exists(self.store_path):
            return
        try:
            with open(self.store_path, encoding="utf-8") as f:
                data = json.load(f)
            self.chats = data.get("chats", {})
            self.current_chat = data.get("current") if data.get("current") in self.chats else None
        except (OSError, ValueError):
            self.chats, self.current_chat = {}, None

    def export_chat(self, chat_id, export_dir=os.path.expanduser("~/.fluffy/exports")):
        os.makedirs(export_dir, exist_ok=True)
        path = os.path.join(export_dir, f"{chat_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.chats[chat_id], f, indent=2)
        return path

    def import_chat(self, file_path):
        with open(file_path, encoding="utf-8") as f:
            chat = json.load(f)
        chat_id = str(uuid.uuid4())
        chat.setdefault("name", "Imported chat")
        chat.setdefault("messages", [])
        self.chats[chat_id] = chat
        self.current_chat = chat_id
        self.save()
        return chat_id
