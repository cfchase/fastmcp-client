# FastMCP Client

A Python client for interacting with MCP (Model Context Protocol) servers through Claude AI, built using the FastMCP library.

## Features

- Two client implementations:
  - **Single server client** (`client.py`): Connect to a single MCP server via stdio
  - **Multi-server client** (`multi_client.py`): Connect to multiple MCP servers simultaneously
- Interactive chat interface powered by Claude AI
- Automatic tool discovery and execution
- Native multi-server support with FastMCP

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

### Single Server Client

Connect to a single MCP server:

```bash
# Default: connects to kubernetes-mcp-server via npx
python client.py

# Connect with a custom command
python client.py --command "python -m my_server"

# With environment variables
python client.py --command "node server.js" --env PORT=8080 --env DEBUG=true

# With working directory
python client.py --command "./server" --cwd /path/to/server
```

### Multi-Server Client

Connect to multiple MCP servers simultaneously using a configuration file:

```bash
# Default: uses config.json
python multi_client.py

# Use a custom config file
python multi_client.py --config my-config.json
```

#### Configuration Format

Create a `config.json` file (see `config.example.json`):

```json
{
  "mcpServers": {
    "kubernetes": {
      "command": "npx",
      "args": ["kubernetes-mcp-server@latest"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem@latest", "/tmp"]
    },
    "remote_api": {
      "url": "http://remote-host:8123/mcp"
    },
    "python_server": {
      "command": "python",
      "args": ["-m", "./example_server.py"]
    }
  }
}
```

## How It Works

1. The client connects to MCP server(s) using FastMCP
2. It discovers available tools from all connected servers
3. User queries are sent to Claude AI along with the available tools
4. Claude determines if/when to use tools to answer queries
5. Tool calls are automatically routed to the appropriate server
6. Tool results are sent back to Claude for final response generation

## Multi-Server Features

When using `multi_client.py`:
- Tools from all servers are available in a single session
- FastMCP automatically prefixes tool names with server names
- Tool calls are routed to the appropriate server
- Both stdio (local) and HTTP (remote) servers are supported

## Development

This project uses FastMCP, which simplifies MCP client implementation by handling:
- Connection management
- Native multi-server support
- Session handling
- Protocol details
- Automatic tool prefixing and routing

The main components are:
- `MCPClient` class: Single server client
- `MCPMultiClient` class: Multi-server client with config file support
- FastMCP `Client`: Manages connections to MCP servers
- Anthropic SDK: Provides Claude AI integration