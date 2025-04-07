from datetime import datetime

import os
import json
from src.utils.helpers import LogManager, TokenManager
import uuid

class ChatManager:
    def __init__(self):
        self.chats = {}
        self.current_chat = None
        self.conversation_history = []
        self.context_enabled = False
        self.max_history_tokens = 1000

    def create_new_chat(self):
        # Generate unique chat ID
        chat_id = str(uuid.uuid4())
        chat_name = f"Chat {len(self.chats) + 1}"
        
        self.chats[chat_id] = {
            'name': chat_name,
            'messages': [],
            'created_at': datetime.now(),
            'last_active': datetime.now()
        }
        self.current_chat = chat_id
        return chat_id

    def add_message(self, sender, message):
        if not self.current_chat:
            self.create_new_chat()

        # Log message
        LogManager.log_message(self.current_chat, sender, message)

        # Create message entry
        message_entry = {
            'id': str(uuid.uuid4()),
            'sender': sender,
            'message': message,
            'timestamp': datetime.now(),
            'tokens': TokenManager.count_tokens(message)
        }
        
        # Add to chat messages
        self.chats[self.current_chat]['messages'].append(message_entry)
        self.chats[self.current_chat]['last_active'] = datetime.now()

        # Update conversation history if context is enabled
        if self.context_enabled:
            self.update_conversation_history(sender, message)

    def get_conversation_context(self):
        if not self.context_enabled:
            return ""
        
        # Collect recent messages
        context_messages = self.chats[self.current_chat]['messages'][-10:]
        
        # Build context string
        context = ""
        for msg in context_messages:
            context += f"{msg['sender']}: {msg['message']}\n"
        
        # Truncate to max tokens
        return TokenManager.truncate_context(context, self.max_history_tokens)

    def export_chat(self, chat_id):
        """
        Export chat to a JSON file
        """
        try:
            export_path = os.path.expanduser(f"~/.fluffy/exports/{chat_id}.json")
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            
            with open(export_path, 'w') as f:
                json.dump(self.chats[chat_id], f, indent=4, default=str)
            
            return export_path
        except Exception as e:
            print(f"Error exporting chat: {e}")
            return None

    def import_chat(self, file_path):
        """
        Import chat from a JSON file
        """
        try:
            with open(file_path, 'r') as f:
                imported_chat = json.load(f)
            
            # Generate new unique ID
            new_chat_id = str(uuid.uuid4())
            self.chats[new_chat_id] = imported_chat
            self.current_chat = new_chat_id
            
            return new_chat_id
        except Exception as e:
            print(f"Error importing chat: {e}")
            return None