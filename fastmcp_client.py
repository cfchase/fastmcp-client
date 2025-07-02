"""FastMCP Multi-Server Client"""

import asyncio
import json
import argparse
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastmcp import Client
from fastmcp.client import NpxStdioTransport
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


class MultiServerMCPClient:
    """FastMCP Client for interacting with multiple MCP servers"""

    def __init__(self, config_path: str = "config.json"):
        # Initialize Anthropic client for Claude AI
        self.anthropic = Anthropic()
        self.config_path = config_path
        self.servers_config = []
        self.connected_servers = []

    def load_config(self):
        """Load server configurations from JSON file"""
        try:
            if not Path(self.config_path).exists():
                # Create a default config if it doesn't exist
                self._create_default_config()
            
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self.servers_config = config.get('servers', [])
                print(f"Loaded {len(self.servers_config)} server configurations")
        except Exception as e:
            print(f"Error loading config: {e}")
            self.servers_config = []

    def _create_default_config(self):
        """Create a default configuration file"""
        default_config = {
            "servers": [
                {
                    "name": "kubernetes-server",
                    "type": "npx",
                    "package": "kubernetes-mcp-server@latest",
                    "description": "Kubernetes management server"
                },
                {
                    "name": "http-server",
                    "type": "http",
                    "url": "http://localhost:8123/mcp",
                    "description": "HTTP MCP server"
                }
            ]
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        print(f"Created default config file: {self.config_path}")

    def _create_transport(self, server_config: Dict[str, Any]):
        """Create appropriate transport based on server configuration"""
        server_type = server_config.get('type', '').lower()
        
        if server_type == 'npx':
            package = server_config.get('package')
            if not package:
                raise ValueError(f"NPX server {server_config.get('name')} missing 'package' field")
            return NpxStdioTransport(package=package)
        
        elif server_type == 'http':
            url = server_config.get('url')
            if not url:
                raise ValueError(f"HTTP server {server_config.get('name')} missing 'url' field")
            return url  # For HTTP, we pass the URL directly to Client
        
        else:
            raise ValueError(f"Unsupported server type: {server_type}")

    async def connect_to_servers(self):
        """Connect to all configured servers and collect their tools"""
        self.connected_servers = []
        all_tools = []
        
        for server_config in self.servers_config:
            try:
                server_name = server_config.get('name', 'unnamed')
                print(f"\nConnecting to server: {server_name}")
                
                transport = self._create_transport(server_config)
                
                # Test connection and get tools
                async with Client(transport) as client:
                    tools = await client.list_tools()
                    server_tools = []
                    
                    for tool in tools:
                        # Prefix tool names with server name to avoid conflicts
                        prefixed_tool = {
                            "name": f"{server_name}_{tool.name}",
                            "original_name": tool.name,
                            "description": f"[{server_name}] {tool.description or ''}",
                            "input_schema": tool.inputSchema,
                            "server_name": server_name,
                            "transport": transport
                        }
                        server_tools.append(prefixed_tool)
                        all_tools.append(prefixed_tool)
                    
                    self.connected_servers.append({
                        'name': server_name,
                        'config': server_config,
                        'transport': transport,
                        'tools': server_tools
                    })
                    
                    print(f"  ✓ Connected with {len(server_tools)} tools: {[t['original_name'] for t in server_tools]}")
                    
            except Exception as e:
                print(f"  ✗ Failed to connect to {server_config.get('name', 'unnamed')}: {e}")
        
        print(f"\nSuccessfully connected to {len(self.connected_servers)} servers")
        print(f"Total available tools: {len(all_tools)}")
        return all_tools

    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools from all servers"""
        # Connect to servers and get all available tools
        all_tools = await self.connect_to_servers()
        
        if not all_tools:
            return "No tools available. Please check your server configurations."
        
        # Convert tools to Anthropic format
        available_tools = [
            {
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["input_schema"],
            }
            for tool in all_tools
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

                # Find the tool and its server
                tool_info = next((t for t in all_tools if t["name"] == tool_name), None)
                if not tool_info:
                    final_text.append(f"[Error: Tool {tool_name} not found]")
                    continue

                server_name = tool_info["server_name"]
                original_tool_name = tool_info["original_name"]
                transport = tool_info["transport"]

                try:
                    # Execute tool call using the appropriate server
                    async with Client(transport) as client:
                        result = await client.call_tool(original_tool_name, tool_args)
                        final_text.append(f"[Calling {server_name}:{original_tool_name} with args {tool_args}]")

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
                        
                except Exception as e:
                    final_text.append(f"[Error executing {server_name}:{original_tool_name}: {e}]")

        return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nFastMCP Multi-Server Client Started!")
        print("Type your queries or 'quit' to exit.")
        print("Available commands:")
        print("  'list' - Show all available tools")
        print("  'servers' - Show connected servers")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == "quit":
                    break
                elif query.lower() == "list":
                    await self._list_tools()
                    continue
                elif query.lower() == "servers":
                    await self._list_servers()
                    continue

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def _list_tools(self):
        """List all available tools from all servers"""
        all_tools = await self.connect_to_servers()
        if not all_tools:
            print("No tools available")
            return
            
        print("\nAvailable tools:")
        current_server = None
        for tool in all_tools:
            if tool["server_name"] != current_server:
                current_server = tool["server_name"]
                print(f"\n  {current_server}:")
            print(f"    • {tool['original_name']}: {tool['description'].replace(f'[{current_server}] ', '')}")

    async def _list_servers(self):
        """List all configured servers"""
        print(f"\nConfigured servers ({len(self.servers_config)}):")
        for server in self.servers_config:
            print(f"  • {server.get('name', 'unnamed')} ({server.get('type', 'unknown')})")
            if server.get('description'):
                print(f"    {server['description']}")


async def main():
    """Main function to run the FastMCP multi-server client"""
    parser = argparse.ArgumentParser(description="Run FastMCP Multi-Server Client")
    parser.add_argument(
        "--config", type=str, default="config.json",
        help="Path to configuration file (default: config.json)"
    )
    args = parser.parse_args()

    client = MultiServerMCPClient(config_path=args.config)
    client.load_config()
    await client.chat_loop()


if __name__ == "__main__":
    asyncio.run(main())