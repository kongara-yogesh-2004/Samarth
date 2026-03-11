from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
import uvicorn
import logging
from typing import Optional, Dict, Any, List
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from google import genai
from google.genai import types
from contextlib import AsyncExitStack

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MCPServer")

app = FastAPI(title="MCP FastAPI Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    interactive: bool = False
    conversation_history: Optional[List[Dict[str, str]]] = None

class QueryResponse(BaseModel):
    response: str
    conversation_history: Optional[List[Dict[str, str]]] = None

mcp_clients = {}

class MCPClient:
    def __init__(self, client_id, api_key=None):
        self.client_id = client_id
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        
        # Use provided API key or check environment variable
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or " "
        self.gemini_client = genai.Client(api_key=self.api_key)
        self.model = "gemini-2.0-flash"
        self.tools = []
        self.initialized = False

    async def connect_to_playwright_mcp(self, headless=False) -> List:
        """Connect to an MCP server and return available tools"""
        
        command = "npx"
        args = ["@playwright/mcp@latest"]

        # if headless:
        #     args.append("--headless")
            
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=os.environ.copy()
        )
        
        try:
            logger.info(f"Connecting to Playwright MCP server for client {self.client_id}: {command} {' '.join(args)}")
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            self.stdio, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
            
            await self.session.initialize()
            
            # lists available tools from our MCP server
            response = await self.session.list_tools()
            self.tools = response.tools
            logger.info(f"Connected to server with {len(self.tools)} tools for client {self.client_id}")
            self.initialized = True
            return self.tools
            
        except Exception as e:
            logger.error(f"Error connecting to Playwright MCP: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to connect to Playwright MCP: {str(e)}")

    def validate_schema(self, schema: Dict) -> Dict:
        """Clean and validate JSON schema for Gemini compatibility"""
        if not isinstance(schema, dict):
            return {"type": "string"}
        cleaned = {}

        for key, value in schema.items():
            if key in ['$schema', 'additionalProperties']:
                continue
                
            # here we are recursively cleaning nested dictionaries
            if isinstance(value, dict):
                cleaned[key] = self.validate_schema(value)
            elif isinstance(value, list):
                cleaned[key] = [
                    self.validate_schema(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                cleaned[key] = value
        
        # For OBJECT type schemas, ensure properties exists and is not empty
        if schema.get('type') == 'object':
            if 'properties' not in cleaned or not cleaned['properties']:
                cleaned['properties'] = {
                    "placeholder": {
                        "type": "string",
                        "description": "Placeholder parameter"
                    }
                }
                
        return cleaned

    async def prepare_tools_for_gemini(self) -> List[Dict]:
        """Prepare tools for Gemini API format"""
        if not self.tools:
            response_tools = await self.session.list_tools()
            self.tools = response_tools.tools
            
        available_tools = []
        for tool in self.tools:
            # here we are cleaning and validating the schema
            cleaned_schema = self.validate_schema(tool.inputSchema)
            
            available_tools.append({
                "name": tool.name,
                "description": tool.description or f"Use the {tool.name} browser tool",
                "parameters": cleaned_schema
            })
            
        logger.info(f"Prepared {len(available_tools)} tools for Gemini for client {self.client_id}")
        return available_tools

    async def process_query(self, query: str, conversation_history=None) -> Dict:
        """Process a query using Gemini and available tools"""
        if not conversation_history:
            conversation_history = [{"role": "user", "content": query+"if the user gives an domain name for example: google.com, append https:// to the domain name and call the corresponding function"}]
        elif conversation_history[-1]["role"] != "user" or conversation_history[-1]["content"] != query:
            conversation_history.append({"role": "user", "content": query})

        available_tools = await self.prepare_tools_for_gemini()

        tools_obj = types.Tool(function_declarations=available_tools)
        config = types.GenerateContentConfig(tools=[tools_obj])

        # Convert the conversation history to a single prompt
        conversation_prompt = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in conversation_history]
        )

        logger.info(f"Sending request to Gemini for client {self.client_id}")
        try:
            # Call Gemini's generate_content
            gemini_response = await asyncio.to_thread(
                self.gemini_client.models.generate_content,
                model=self.model,
                contents=conversation_prompt,
                config=config
            )
            
            response_text, updated_history = await self._process_gemini_response(gemini_response, conversation_history.copy())
            return {
                "response": response_text,
                "conversation_history": updated_history
            }
            
        except Exception as e:
            logger.error(f"Gemini API error for client {self.client_id}: {str(e)}", exc_info=True)
            error_message = f"Error processing with Gemini: {str(e)}"
            conversation_history.append({"role": "assistant", "content": error_message})
            return {
                "response": error_message,
                "conversation_history": conversation_history
            }

    async def _process_gemini_response(self, gemini_response, messages):
        """Process response from Gemini, handling function calls if present"""
        final_text = []
        candidate = gemini_response.candidates[0]
        part = candidate.content.parts[0]

        # here we are obtaining the assistant's initial text
        assistant_text = part.text if hasattr(part, 'text') and part.text else ""
        
        # Here we are adding the initial assistant response to conversation history if there's text
        if assistant_text:
            messages.append({"role": "assistant", "content": assistant_text})
            final_text.append(assistant_text)

        if hasattr(part, 'function_call') and part.function_call:
            function_call = part.function_call
            tool_name = function_call.name
            tool_args = function_call.args
            
            logger.info(f"Function call detected for client {self.client_id}: {tool_name}")
            tool_call_message = f"Calling tool {tool_name}"
            final_text.append(tool_call_message)

            try:
                tool_result = await self.session.call_tool(tool_name, tool_args)

                messages.append({
                    "role": "function",
                    "name": tool_name, 
                    "content": tool_result.content if isinstance(tool_result.content, str) else str(tool_result.content)
                })

                result_text = f"Tool {tool_name} executed successfully"
                final_text.append(result_text)
                
                interpretation = await self._get_result_interpretation(messages)
                if interpretation:
                    final_text.append(interpretation)
                    messages.append({"role": "assistant", "content": interpretation})
                
            except Exception as e:
                logger.error(f"Error calling tool {tool_name} for client {self.client_id}: {str(e)}")
                error_text = f"Error executing tool {tool_name}: {str(e)}"
                final_text.append(error_text)
                messages.append({"role": "assistant", "content": error_text})
        
        return "\n".join(final_text), messages

    async def _get_result_interpretation(self, messages):
        """Get interpretation of tool results from Gemini"""
        interpretation_messages = messages.copy()
        interpretation_messages.append({
            "role": "user",
            "content": "Please interpret these results and continue."
        })
        
        try:
            conversation_prompt = "\n".join(
                [f"{msg['role']}: {msg['content']}" for msg in interpretation_messages]
            )
            
            logger.info(f"Getting interpretation from Gemini for client {self.client_id}")
            gemini_response = await asyncio.to_thread(
                self.gemini_client.models.generate_content,
                model=self.model,
                contents=conversation_prompt
            )
            
            if gemini_response.candidates and gemini_response.candidates[0].content.parts:
                return gemini_response.candidates[0].content.parts[0].text
            return "No interpretation available."
        
        except Exception as e:
            logger.error(f"Error getting interpretation for client {self.client_id}: {str(e)}")
            return f"Could not get interpretation: {str(e)}"

    async def cleanup(self):
        """Clean up resources"""
        try:
            await self.exit_stack.aclose()
            logger.info(f"Cleaned up resources for client {self.client_id}")
        except Exception as e:
            logger.error(f"Error cleaning up resources for client {self.client_id}: {str(e)}")

async def get_or_create_client(client_id: str):
    """Get existing client or create a new one"""
    if client_id not in mcp_clients or not mcp_clients[client_id].initialized:
        logger.info(f"Creating new MCP client with ID: {client_id}")
        client = MCPClient(client_id=client_id)
        await client.connect_to_playwright_mcp(headless=True)
        mcp_clients[client_id] = client
    return mcp_clients[client_id]


async def cleanup_client(client_id: str):
    """Clean up a client after use"""
    if client_id in mcp_clients:
        await mcp_clients[client_id].cleanup()
        del mcp_clients[client_id]
        logger.info(f"Cleaned up client {client_id}")


@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, background_tasks: BackgroundTasks, req: Request):
    """Process a query with the MCP client"""
    client_id = req.client.host
    
    try:
        client = await get_or_create_client(client_id)
        result = await client.process_query(
            request.query, 
            conversation_history=request.conversation_history
        )
        
        if not request.interactive:
            background_tasks.add_task(cleanup_client, client_id)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"Error processing query for client {client_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cleanup")
async def manual_cleanup(req: Request):
    """Manually cleanup a client"""
    client_id = req.client.host
    
    if client_id in mcp_clients:
        await cleanup_client(client_id)
        return {"status": "success", "message": f"Client {client_id} cleaned up"}
    
    return {"status": "success", "message": "No client to clean up"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup all clients on shutdown"""
    for client_id in list(mcp_clients.keys()):
        await cleanup_client(client_id)

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000)
