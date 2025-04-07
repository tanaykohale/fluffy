import customtkinter as ctk
from src.ui.sidebar import Sidebar
from src.ui.chat_display import ChatDisplay

class FluffyMainWindow:
    def __init__(self, root, ollama_service, chat_manager):
        self.root = root
        self.ollama_service = ollama_service
        self.chat_manager = chat_manager

        # Main container
        self.main_frame = ctk.CTkFrame(root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create sidebar
        self.sidebar = Sidebar(
            self.main_frame, 
            self.ollama_service, 
            self.chat_manager, 
            self.on_new_chat,
            self.on_chat_selected
        )

        # Create chat display
        self.chat_display = ChatDisplay(
            self.main_frame, 
            self.chat_manager
        )

        # Layout
        self.sidebar.frame.pack(side="left", fill="y", padx=(0,10))
        self.chat_display.frame.pack(side="right", fill="both", expand=True)

    def on_new_chat(self):
        # Create a new chat and update UI
        new_chat_name = self.chat_manager.create_new_chat()
        self.sidebar.add_chat_button(new_chat_name)
        self.chat_display.load_chat(new_chat_name)

    def on_chat_selected(self, chat_name):
        # Load selected chat
        self.chat_manager.current_chat = chat_name
        self.chat_display.load_chat(chat_name)