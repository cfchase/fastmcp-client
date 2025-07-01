"""FastMCP HTTP Client"""

import argparse
import asyncio
from typing import Dict, Any

from fastmcp import Client
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


class MCPClient:
    """FastMCP Client for interacting with an MCP HTTP server"""

    def __init__(self):
        # Initialize Anthropic client for Claude AI
        self.anthropic = Anthropic()
        self.server_url = None

    async def connect_to_http_server(self, server_url: str):
        """Set up connection parameters for HTTP server"""
        self.server_url = server_url
        print(f"Configured to connect to: {server_url}")

    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""
        # Use FastMCP client to connect and interact with the server
        async with Client(self.server_url) as client:
            # List available tools
            tools = await client.list_tools()
            print("\nConnected to server with tools:", [tool.name for tool in tools])
            
            # Convert tools to Anthropic format
            available_tools = [
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "input_schema": tool.inputSchema,
                }
                for tool in tools
            ]

            messages = [{"role": "user", "content": query}]

            # Initial Claude API call
            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=messages,
                tools=available_tools,
            )

            # Process response and handle tool calls
            final_text = []

            for content in response.content:
                if content.type == "text":
                    final_text.append(content.text)
                elif content.type == "tool_use":
                    tool_name = content.name
                    tool_args = content.input

                    # Execute tool call using FastMCP client
                    result = await client.call_tool(tool_name, tool_args)
                    final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                    # Continue conversation with tool results
                    if hasattr(content, "text") and content.text:
                        messages.append({"role": "assistant", "content": content.text})
                    messages.append({"role": "user", "content": str(result)})

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
        print("\nFastMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == "quit":
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")


async def main():
    """Main function to run the FastMCP client"""
    parser = argparse.ArgumentParser(description="Run FastMCP HTTP Client")
    parser.add_argument(
        "--url", type=str, default="http://localhost:8123/mcp", 
        help="Full URL of the MCP server (default: http://localhost:8123/mcp)"
    )
    args = parser.parse_args()

    client = MCPClient()
    await client.connect_to_http_server(args.url)
    await client.chat_loop()


if __name__ == "__main__":
    asyncio.run(main())