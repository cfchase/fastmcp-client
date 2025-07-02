"""FastMCP Multi-Server Client"""

import asyncio
import argparse
import json

from fastmcp import Client
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


class MCPMultiClient:
    """FastMCP Client for interacting with multiple MCP servers"""

    def __init__(self):
        # Initialize Anthropic client for Claude AI
        self.anthropic = Anthropic()
        self.client = None
        self.tools = []

    async def initialize(self, config_path: str):
        """Load configuration and initialize multi-server client"""
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print(f"Loaded configuration for {len(config.get('mcpServers', {}))} servers")
        
        self.client = Client(config)
        async with self.client:
            self.tools = await self.client.list_tools()
            
            # Convert tools to Anthropic format
            self.available_tools = [{ 
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.inputSchema
            } for tool in self.tools]
            
            print(f"Connected to servers with {len(self.tools)} total tools")

    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""
        # Use FastMCP client to connect and interact with the servers
        async with self.client:
            messages = [
                {
                    "role": "user",
                    "content": query
                }
            ]

            # Initial Claude API call
            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=messages,
                tools=self.available_tools
            )

            # Process response and handle tool calls
            final_text = []

            for content in response.content:
                if content.type == 'text':
                    final_text.append(content.text)
                elif content.type == 'tool_use':
                    tool_name = content.name
                    tool_args = content.input
                    
                    # Execute tool call using FastMCP client
                    result = await self.client.call_tool(tool_name, tool_args)
                    final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                    # Continue conversation with tool results
                    if hasattr(content, 'text') and content.text:
                        messages.append({
                          "role": "assistant",
                          "content": content.text
                        })
                    messages.append({
                        "role": "user", 
                        "content": str(result)
                    })

                    # Get next response from Claude
                    response = self.anthropic.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=1000,
                        messages=messages,
                    )

                    final_text.append(response.content[0].text)

            return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nFastMCP Multi-Server Client Started!")
        print("Type your queries or 'quit' to exit.")
        print("Type 'list' to see all available tools.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() == 'quit':
                    break
                
                if query.lower() == 'list':
                    print("\nAvailable tools:")
                    for tool in self.tools:
                        print(f"  - {tool.name}: {tool.description}")
                    continue
                    
                response = await self.process_query(query)
                print("\n" + response)
                    
            except Exception as e:
                print(f"\nError: {str(e)}")


async def main():
    """Main function to run the FastMCP multi-server client"""
    parser = argparse.ArgumentParser(description="Run FastMCP Multi-Server Client")
    parser.add_argument(
        "--config", type=str, default="config.json", 
        help="Path to configuration file (default: config.json)"
    )
    args = parser.parse_args()

    client = MCPMultiClient()
    await client.initialize(args.config)
    await client.chat_loop()


if __name__ == "__main__":
    asyncio.run(main())