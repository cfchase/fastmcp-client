# FastMCP Client

A Python client for interacting with MCP (Model Context Protocol) servers through Claude AI, built using the FastMCP library.

## Features

- Two client implementations:
  - **Stdio client** (`client.py`): Connect to local MCP servers via stdio
  - **HTTP client** (`remote_client.py`): Connect to remote MCP servers via HTTP
- Interactive chat interface powered by Claude AI
- Automatic tool discovery and execution
- Simplified connection management with FastMCP

## Requirements

- Python >= 3.11
- An Anthropic API key

## Installation

```bash
# Install dependencies
uv pip install -e .
```

## Configuration

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=your-api-key-here
```

## Usage

### Stdio Client

Connect to MCP servers that run locally via stdio:

```bash
# Default: connects to kubernetes-mcp-server
python client.py

# Connect to a specific server
python client.py weather-mcp-server@latest
```

### HTTP Client

Connect to MCP servers running over HTTP:

```bash
# Default: connects to http://localhost:8123/mcp
python remote_client.py

# Connect to a specific URL
python remote_client.py --url https://your-mcp-server.com/mcp
```

## How It Works

1. The client connects to an MCP server using FastMCP
2. It discovers available tools from the server
3. User queries are sent to Claude AI along with the available tools
4. Claude determines if/when to use tools to answer queries
5. Tool results are sent back to Claude for final response generation

## Development

This project uses FastMCP, which simplifies MCP client implementation by handling:
- Connection management
- Session handling
- Protocol details
- Error handling

The main components are:
- `MCPClient` class: Handles the interaction between Claude AI and MCP servers
- FastMCP `Client`: Manages the connection to MCP servers
- Anthropic SDK: Provides Claude AI integration