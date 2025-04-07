# 📱 Fluffy - Local AI Chat Interface

A sleek, WhatsApp-style desktop application for interacting with local AI models through Ollama. Built with Python and CustomTkinter.


  <tr>
    <td><img src="screenshots/main.png" alt="Fluffy main blank"></td>
    <td><img src="screenshots/main1.png" alt="Fluffy main"></td>
  </tr>



## ✨ Features

- 🤖 **Local Hosted LLM Integration**
  - Seamless connection with Ollama API
  - Auto-detection of available models
  - Real-time response streaming
  - Context-aware conversations (toggleable)
<table>
  <tr>
    <td><img src="screenshots/Detect Available Models.png" alt="Model error" height="200" width="355"></td>
    <td><img src="screenshots/Select model.png" alt="Choose model" height="200" width="355"></td>
  </tr>
</table>
  

- 💬 **Chat Management**
  - Multiple chat sessions
  - Rename and delete chats
  - Persistent chat history
  - Right-click context menu

- 📊 **System Monitoring**
  - Real-time CPU usage
  - RAM usage tracking
  - Non-blocking performance

- 🎨 **Modern UI**
  - WhatsApp-inspired interface
  - Message bubbles
  - Smooth scrolling
  - Dark mode support

## 🚀 Getting Started

### Prerequisites

```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Install required Python packages
pip install -r requirements.txt
