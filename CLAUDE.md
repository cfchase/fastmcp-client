# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python FastMCP client project that enables interaction with MCP servers through Claude AI. The codebase provides two client implementations:
- **client.py**: Stdio-based FastMCP client for local server connections
- **remote_client.py**: HTTP-based FastMCP client for remote server connections

## Architecture

### Core Components

1. **MCPClient Class Structure**:
   - Uses FastMCP's Client class for simplified connection management
   - Anthropic integration for Claude AI interactions
   - Tool execution pipeline between Claude and MCP servers
   - Interactive REPL-like chat interface

2. **Connection Flow**:
   - Load environment variables (ANTHROPIC_API_KEY from .env)
   - Initialize Anthropic client
   - Connect to MCP server using FastMCP Client (stdio or HTTP)
   - List available tools from server
   - Process queries through Claude with tool access
   - Execute tool calls and return results

3. **Key Dependencies**:
   - `fastmcp>=2.9.2`: FastMCP library for MCP client/server interactions
   - `anthropic>=0.55.0`: Claude AI Python SDK
   - `python-dotenv>=1.1.1`: Environment variable management

## Common Development Commands

### Running the Clients

```bash
# Run stdio client (connects to npx-based MCP servers)
python client.py [server-name]
# Default: kubernetes-mcp-server@latest

# Run HTTP client
python remote_client.py --url http://localhost:8123/mcp
# Additional headers: --header "Key:Value"
```

### Package Management

This project uses `uv` as the package manager:

```bash
# Install dependencies
uv pip install -e .

# Update dependencies
uv pip compile pyproject.toml -o requirements.txt
uv pip sync requirements.txt
```

## Project Structure

- **Python 3.13** required (specified in .python-version)
- **Environment variables**: Store ANTHROPIC_API_KEY in .env file
- **Simplified architecture**: FastMCP handles connection management, session handling, and protocol details
- **No test infrastructure**: Tests need to be implemented
- **Minimal error handling**: Basic try-catch in chat loops only

## Key Changes from MCP to FastMCP

- **Simplified Client**: FastMCP's Client class handles all connection complexity
- **Async Context Manager**: Uses `async with Client(...)` pattern for automatic cleanup
- **Unified Interface**: Same client API works for stdio, HTTP, and SSE connections
- **Direct Tool Access**: `client.list_tools()` and `client.call_tool()` methods
- **No Manual Session Management**: FastMCP handles ClientSession internally
- **Transport Classes**: Use `NpxStdioTransport` for NPX-based servers (stdio client)
- **Tool Types**: Tools are returned as `mcp.types.Tool` objects with attributes (not dictionaries)

## Important Notes

- The project is in early development (v0.1.0) with minimal documentation
- Both clients share similar architecture but use different transport mechanisms
- Tool schemas are automatically extracted from MCP servers and passed to Claude
- The chat loop runs continuously until user types 'quit'

## Git Commit Guidelines

When creating commits in this repository:
- **DO NOT** include Claude-specific references in commit messages
- **DO NOT** mention "Generated with Claude Code" or similar attributions
- **DO NOT** add Co-Authored-By references to Claude
- Focus commit messages on the technical changes made
- Use conventional commit format when appropriate (feat:, fix:, docs:, etc.)