import asyncio
import argparse
from typing import Dict, Any, Optional

from fastmcp import Client
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self):
        # Initialize Anthropic client for Claude AI
        self.anthropic = Anthropic()
        self.client = None
        self.tools = []
        self.messages = []  # Store conversation history
        
    async def initialize(self, command: str):
        self.client = Client(command)
        async with self.client:
            self.tools = await self.client.list_tools()
            
                        # Convert tools to Anthropic format
            self.available_tools = [{ 
                    "name": tool.name,
                    "description": tool.description or "",
                    "input_schema": tool.inputSchema
                } for tool in self.tools]

    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""
        # Use FastMCP client to connect and interact with the server
        async with self.client :
            # Add user query to conversation history
            self.messages.append({
                "role": "user",
                "content": query
            })

            # Initial Claude API call with full conversation history
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=self.messages,
                tools=self.available_tools
            )

            # Process response and handle tool calls
            final_text = []
            assistant_content = []

            for content in response.content:
                if content.type == 'text':
                    final_text.append(content.text)
                    assistant_content.append({"type": "text", "text": content.text})
                elif content.type == 'tool_use':
                    tool_name = content.name
                    tool_args = content.input
                    
                    # Execute tool call using FastMCP client
                    result = await self.client.call_tool(tool_name, tool_args)
                    final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")
                    
                    # Add tool use to assistant content
                    assistant_content.append({
                        "type": "tool_use",
                        "id": content.id,
                        "name": tool_name,
                        "input": tool_args
                    })

                    # Add assistant message with tool use
                    self.messages.append({
                        "role": "assistant",
                        "content": assistant_content
                    })
                    
                    # Add tool result
                    self.messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": str(result)
                        }]
                    })

                    # Get next response from Claude with updated history
                    response = self.anthropic.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1000,
                        messages=self.messages,
                    )

                    # Reset assistant content for new response
                    assistant_content = []
                    for new_content in response.content:
                        if new_content.type == 'text':
                            final_text.append(new_content.text)
                            assistant_content.append({"type": "text", "text": new_content.text})

            # Add final assistant response to history
            if assistant_content:
                self.messages.append({
                    "role": "assistant",
                    "content": assistant_content
                })

            return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nFastMCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        print("Type 'clear' to clear conversation history.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() == 'quit':
                    break
                
                if query.lower() == 'clear':
                    self.messages = []
                    print("Conversation history cleared.")
                    continue
                    
                response = await self.process_query(query)
                print("\n" + response)
                    
            except Exception as e:
                print(f"\nError: {str(e)}")

async def main():
    parser = argparse.ArgumentParser(description="Run FastMCP Stdio Client")
    parser.add_argument(
        "--command", type=str, default="npx kubernetes-mcp-server@latest",
        help="Full command to run the server (default: 'npx kubernetes-mcp-server@latest')"
    )

    args = parser.parse_args()

    client = MCPClient()
    await client.initialize(args.command)
    await client.chat_loop()

if __name__ == "__main__":
    asyncio.run(main())