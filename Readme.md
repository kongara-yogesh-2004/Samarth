# Samarth – AI Powered Browser Testing Assistant

Samarth is an AI-powered browser testing assistant that enables users to interact with websites using natural language.  
It combines **Large Language Models (Google Gemini)** with **Model Context Protocol (MCP)** and **Playwright** to perform automated browser actions and frontend testing through a conversational interface.

The system allows testers and developers to instruct the AI to browse websites, perform UI interactions, and analyze results without writing manual automation scripts.

---

## Features

- Natural language driven browser automation  
- AI-powered frontend testing assistant  
- Chat-based testing interface  
- Automated webpage navigation  
- MCP tool calling for browser actions  
- Real-time tool execution and response interpretation  
- FastAPI backend for scalable request handling  
- Interactive conversation history support  

---

## Architecture

The system consists of two main components.

### Frontend
A chat interface where users can interact with the AI assistant.

Responsibilities:
- Accept user commands
- Display assistant responses
- Show tool execution results
- Maintain conversation context

### Backend
A FastAPI server that connects the LLM with browser automation tools.

Responsibilities:
- Process user queries
- Send prompts to Gemini LLM
- Select and execute MCP tools
- Run Playwright automation
- Return interpreted results

### Workflow

User Query  
→ FastAPI Server  
→ Gemini LLM  
→ Tool Selection (MCP)  
→ Playwright Browser Automation  
→ Result Interpretation  
→ Response Returned to User

---

## Tech Stack

### Frontend
- HTML  
- CSS  
- JavaScript  
- FontAwesome Icons  

### Backend
- Python  
- FastAPI  
- MCP (Model Context Protocol)  
- Playwright MCP Tools  
- Google Gemini API  
- Uvicorn  

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/samarth-ai-tester.git
cd samarth-ai-tester

**### 2.Install Python Dependencies**
'''bash
pip install fastapi uvicorn google-genai mcp

**### 3. Install Playwright MCP**

npm install -g @playwright/mcp

**### 4. Set Gemini API Key**

Linux / Mac:

export GEMINI_API_KEY="your_api_key"

Windows:

set GEMINI_API_KEY=your_api_key


**### 5.Running the Project
**
Start the backend server:
'''bash
python server.py

**The server will start at:**

http://localhost:8000

Open the frontend by launching the HTML file in your browser.
