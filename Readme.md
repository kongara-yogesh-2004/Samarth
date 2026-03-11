# Samarth – AI Powered Browser Testing Assistant

Samarth is an AI-powered browser testing assistant that enables users to interact with websites using natural language. It combines **Large Language Models (Google Gemini)** with **Model Context Protocol (MCP)** and **Playwright** to perform automated browser actions and frontend testing through a conversational interface.

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
→ FastAPI Backend  
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
- FontAwesome  

### Backend
- Python  
- FastAPI  
- MCP (Model Context Protocol)  
- Playwright MCP Tools  
- Google Gemini API  
- Uvicorn  

---

## Project Structure

```
samarth-ai-tester/
│
├── index.html        # Chat-based frontend UI
├── server.py         # FastAPI backend server
└── README.md         # Project documentation
```

---

## Installation

Clone the repository and install the required dependencies.

```bash
git clone https://github.com/yourusername/samarth-ai-tester.git
cd samarth-ai-tester
```

Install Python dependencies:

```bash
pip install fastapi uvicorn google-genai mcp
```

Install Playwright MCP tools:

```bash
npm install -g @playwright/mcp
```

Set your Gemini API key:

```bash
export GEMINI_API_KEY="your_api_key"
```

---

## Running the Project

Start the FastAPI backend server:

```bash
python server.py
```

The backend server will start at:

```
http://localhost:8000
```

Open the frontend by launching:

```
index.html
```

in your browser.

---

## Example Queries

Users can interact with the assistant using natural language commands such as:

- Open google.com  
- Navigate to amazon.com  
- Search for laptops  
- Click the login button  
- Extract the page title  
- Test if the navigation bar exists  

---

## Use Cases

- Automated frontend testing  
- QA automation assistance  
- AI-driven browser interaction  
- UI validation and exploratory testing  
- AI agent-based testing workflows  

---

## Future Improvements

- Multi-session test management  
- Screenshot-based visual validation  
- Automatic test case generation  
- Integration with CI/CD pipelines  
- Support for multiple browser engines  

---

## Author

**Yogesh Kongara**

Computer Science Student | Full Stack Developer | AI Enthusiast  

GitHub:  
https://github.com/kongara-yogesh-2004  

LinkedIn:  
https://linkedin.com/in/yogesh-kongara
