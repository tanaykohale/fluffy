import asyncio
import customtkinter as ctk

class ChatDisplay:
    def __init__(self, parent, chat_manager):
        self.parent = parent
        self.chat_manager = chat_manager
        self.ollama_service = ollama_service
        
        # Main chat display frame
        self.frame = ctk.CTkFrame(parent)

        # Chat title
        self.chat_title = ctk.CTkLabel(
            self.frame, 
            text="Select a chat", 
            font=("Arial", 16, "bold")
        )
        self.chat_title.pack(pady=10)

        # Chat text display
        self.chat_text = ctk.CTkTextbox(
            self.frame, 
            wrap="word", 
            state="disabled"
        )
        self.chat_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Message input area
        self.input_frame = ctk.CTkFrame(self.frame)
        self.input_frame.pack(fill="x", padx=10, pady=10)

        self.message_entry = ctk.CTkEntry(
            self.input_frame, 
            placeholder_text="Type a message...",
            width=500
        )
        self.message_entry.pack(side="left", expand=True, padx=(0,10))

        self.send_button = ctk.CTkButton(
            self.input_frame, 
            text="Send", 
            command=self.send_message
        )
        self.send_button.pack(side="right")

        # Bind enter key to send message
        self.message_entry.bind("<Return>", lambda event: self.send_message())

        # Add a progress bar for AI response
        self.progress_bar = ctk.CTkProgressBar(self.frame)
        self.progress_bar.pack(fill="x", padx=10, pady=(0,5))
        self.progress_bar.set(0)
        self.progress_bar.configure(mode="indeterminate")



    def load_chat(self, chat_name):
        # Update chat title
        self.chat_title.configure(text=f"Chat: {chat_name}")

        # Clear existing text
        self.chat_text.configure(state="normal")
        self.chat_text.delete("1.0", "end")

        # Load chat messages
        if chat_name in self.chat_manager.chats:
            for msg in self.chat_manager.chats[chat_name]:
                self.display_message(msg)

        self.chat_text.configure(state="disabled")
        self.scroll_to_bottom()

    async def generate_ai_response(self, message):
        """
        Async method to generate AI response
        """
        try:
            # Show progress bar
            self.progress_bar.start()
            
            # Generate response
            model = self.parent.sidebar.get_current_model()
            context = self.chat_manager.get_conversation_context()
            full_prompt = f"{context}\nUser: {message}\nAssistant:"
            
            response = await self.ollama_service.generate_response_async(
                model, 
                full_prompt, 
                stream=True
            )
            
            # Collect full response
            ai_response = ""
            for token in response:
                ai_response += token
                # Optionally update UI with streaming tokens
                self.update_ai_response_preview(ai_response)
            
            # Add AI response to chat
            self.chat_manager.add_message("Assistant", ai_response)
            self.display_message(
                self.chat_manager.chats[self.chat_manager.current_chat]['messages'][-1]
            )
        except Exception as e:
            print(f"Error generating AI response: {e}")
        finally:
            # Stop progress bar
            self.progress_bar.stop()
            self.progress_bar.set(0)

    def send_message(self):
        message = self.message_entry.get().strip()
        if not message:
            return

        # Add user message
        self.chat_manager.add_message("You", message)
        self.display_message(
            self.chat_manager.chats[self.chat_manager.current_chat]['messages'][-1]
        )

        # Clear input
        self.message_entry.delete(0, "end")

        # Generate AI response in a separate thread
        asyncio.run(self.generate_ai_response(message))

    def update_ai_response_preview(self, partial_response):
        """
        Update UI with partial AI response (optional)
        """
        # Implement a method to show real-time AI response if desired
        pass

    def display_message(self, message):
        self.chat_text.configure(state="normal")
        
        # Format message display
        formatted_msg = (
            f"[{message['timestamp']}] "
            f"{message['sender']}: {message['message']}\n"
        )
        
        self.chat_text.insert("end", formatted_msg)
        self.chat_text.configure(state="disabled")
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        self.chat_text.see("end")


