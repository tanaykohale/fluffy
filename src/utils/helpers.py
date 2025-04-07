import os
import json
from datetime import datetime

class ConfigManager:
    CONFIG_PATH = os.path.expanduser("~/.fluffy/config.json")

    @classmethod
    def load_config(cls):
        try:
            if os.path.exists(cls.CONFIG_PATH):
                with open(cls.CONFIG_PATH, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
        return {}

    @classmethod
    def save_config(cls, config):
        try:
            os.makedirs(os.path.dirname(cls.CONFIG_PATH), exist_ok=True)
            with open(cls.CONFIG_PATH, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

class LogManager:
    LOG_DIR = os.path.expanduser("~/.fluffy/logs")

    @classmethod
    def log_message(cls, chat_id, sender, message):
        try:
            os.makedirs(cls.LOG_DIR, exist_ok=True)
            log_file = os.path.join(cls.LOG_DIR, f"{chat_id}.log")
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"{timestamp} | {sender}: {message}\n"
            
            with open(log_file, 'a') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Error logging message: {e}")

class TokenManager:
    @staticmethod
    def count_tokens(text):
        """
        Simple token counting method
        In a real-world scenario, you'd use a more sophisticated tokenization method
        """
        return len(text.split())

    @staticmethod
    def truncate_context(context, max_tokens=1000):
        """
        Truncate context to stay within token limit
        """
        tokens = context.split()
        if len(tokens) > max_tokens:
            return ' '.join(tokens[-max_tokens:])
        return context