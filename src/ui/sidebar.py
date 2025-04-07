import customtkinter as ctk
import tkinter as tk

class Sidebar:
    def __init__(self, parent, ollama_service, chat_manager, new_chat_callback, chat_select_callback):
        self.parent = parent
        self.ollama_service = ollama_service
        self.chat_manager = chat_manager
        self.new_chat_callback = new_chat_callback
        self.chat_select_callback = chat_select_callback

        # Main sidebar frame
        self.frame = ctk.CTkFrame(parent, width=250)

        # Model Selection
        self.create_model_section()

        # System Monitor
        self.create_system_monitor()

        # Chat Management
        self.create_chat_management()

        # Context Awareness
        self.create_context_switch()

    def create_model_section(self):
        # Model Selection Label
        model_label = ctk.CTkLabel(self.frame, text="Model Selection", font=("Arial", 16, "bold"))
        model_label.pack(pady=(10,5))

        # Model Dropdown
        available_models = self.ollama_service.get_available_models()
        self.model_menu = ctk.CTkOptionMenu(
            self.frame, 
            values=available_models,
            command=self.on_model_change
        )
        self.model_menu.pack(padx=10, pady=5)

    def create_system_monitor(self):
        # System Monitor Label
        system_label = ctk.CTkLabel(self.frame, text="System Monitor", font=("Arial", 16, "bold"))
        system_label.pack(pady=(10,5))

        # CPU Usage
        self.cpu_label = ctk.CTkLabel(self.frame, text="CPU: 0%")
        self.cpu_label.pack(pady=2)

        # RAM Usage
        self.ram_label = ctk.CTkLabel(self.frame, text="RAM: 0%")
        self.ram_label.pack(pady=2)

    def create_chat_management(self):
        # Chat Management Label
        chat_label = ctk.CTkLabel(self.frame, text="Chats", font=("Arial", 16, "bold"))
        chat_label.pack(pady=(10,5))

        # New Chat Button
        new_chat_button = ctk.CTkButton(
            self.frame, 
            text="New Chat", 
            command=self.new_chat_callback
        )
        new_chat_button.pack(padx=10, pady=5)

        # Chat List Frame
        self.chat_list_frame = ctk.CTkScrollableFrame(self.frame)
        self.chat_list_frame.pack(fill="both", expand=True, padx=10, pady=5)

    def create_context_switch(self):
        # Context Awareness Label
        context_label = ctk.CTkLabel(self.frame, text="Context Awareness", font=("Arial", 16, "bold"))
        context_label.pack(pady=(10,5))

        # Context Switch
        self.context_switch = ctk.CTkSwitch(
            self.frame, 
            text="Keep Context", 
            command=self.on_context_toggle
        )
        self.context_switch.pack(pady=5)

    def add_chat_button(self, chat_name):
        # Create a button for each chat
        chat_button = ctk.CTkButton(
            self.chat_list_frame, 
            text=chat_name,
            command=lambda name=chat_name: self.chat_select_callback(name)
        )
        chat_button.pack(fill="x", padx=5, pady=2)

        # Right-click menu
        chat_button.bind("<Button-3>", lambda e, name=chat_name: self.show_chat_menu(e, name, chat_button))

    def show_chat_menu(self, event, chat_name, button):
        # Context menu for chat buttons
        menu = tk.Menu(self.frame, tearoff=0)
        menu.add_command(label="Rename", command=lambda: self.rename_chat(chat_name, button))
        menu.add_command(label="Delete", command=lambda: self.delete_chat(chat_name, button))
        menu.tk_popup(event.x_root, event.y_root)

    def rename_chat(self, chat_name, button):
        # Rename chat dialog
        dialog = ctk.CTkInputDialog(text="Enter new name:", title="Rename Chat")
        new_name = dialog.get_input()
        
        if new_name and new_name.strip():
            # Update button text
            button.configure(text=new_name)

    def delete_chat(self, chat_name, button):
        # Remove chat from manager and UI
        if chat_name in self.chat_manager.chats:
            del self.chat_manager.chats[chat_name]
        button.destroy()

    def on_model_change(self, model_name):
        # Handle model selection
        print(f"Selected model: {model_name}")

    def on_context_toggle(self):
        # Toggle context awareness
        enabled = self.context_switch.get()
        self.chat_manager.toggle_context(enabled)

    def update_system_stats(self, cpu_usage, ram_usage):
        # Update system monitor labels
        self.cpu_label.configure(text=f"CPU: {cpu_usage}%")
        self.ram_label.configure(text=f"RAM: {ram_usage}%")