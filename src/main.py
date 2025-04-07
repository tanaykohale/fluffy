import customtkinter as ctk
from src.ui.main_window import FluffyMainWindow
from src.services.ollama_service import OllamaService
from src.services.chat_manager import ChatManager
from src.services.system_monitor import SystemMonitor

class FluffyApp:
    def __init__(self):
        # Configure CustomTkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Create main application window
        self.root = ctk.CTk()
        self.root.title("Fluffy AI Chat")
        self.root.geometry("1000x700")

        # Initialize services
        self.ollama_service = OllamaService()
        self.chat_manager = ChatManager()
        
        # Create main window
        self.main_window = FluffyMainWindow(
            self.root, 
            self.ollama_service, 
            self.chat_manager
        )

    def run(self):
        self.root.mainloop()

def main():
    app = FluffyApp()
    app.run()

if __name__ == "__main__":
    main()