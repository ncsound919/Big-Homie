# MCP Server Mode - Setup Guide

Big Homie can run as a native MCP (Model Context Protocol) server, allowing it to be used directly in:
- **Claude Desktop**
- **Cursor IDE**
- **VS Code** (with Claude extension)

## What is MCP Server Mode?

MCP Server Mode turns Big Homie into a service that other AI applications can call to access its tools and capabilities. This means you can use Big Homie's advanced features (web search, persistent shells, agent profiles, media generation, etc.) directly from your IDE or Claude Desktop.

## Quick Start

### 1. For Claude Desktop

Add this to your `claude_desktop_config.json`:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "big-homie": {
      "command": "python",
      "args": ["-m", "mcp_server_main"],
      "cwd": "/path/to/Big-Homie"
    }
  }
}
```

### 2. For Cursor IDE

Add this to your Cursor settings (Cursor Settings → Features → MCP):

```json
{
  "mcpServers": {
    "big-homie": {
      "command": "python",
      "args": ["-m", "mcp_server_main"],
      "cwd": "/path/to/Big-Homie"
    }
  }
}
```

### 3. For VS Code (with Claude Extension)

Add this to your VS Code `settings.json`:

```json
{
  "claude.mcpServers": {
    "big-homie": {
      "command": "python",
      "args": ["-m", "mcp_server_main"],
      "cwd": "/path/to/Big-Homie"
    }
  }
}
```

## Available Tools via MCP

When connected as an MCP server, Big Homie exposes these tools:

### Web & Research
- `web_search` - Search the web for current information
- `github_search_repos` - Search GitHub repositories
- `browser_navigate` - Navigate to URLs and extract content
- `browser_screenshot` - Capture webpage screenshots

### Development
- `shell_session_create` - Create persistent shell sessions
- `shell_session_execute` - Run commands in persistent shells
- `file_read` / `file_write` - File operations
- `vision_analyze_image` - Analyze images with AI

### Media Generation
- `image_generate` - Generate images with ComfyUI
- `video_generate` - Generate videos with MiniMax/ComfyUI
- `music_generate` - Generate music with Google Lyria/MiniMax

### Agent Management
- `profile_create` - Create custom agent profiles
- `profile_switch` - Switch between agent profiles
- `profile_list` - List all available profiles
- `profile_create_from_template` - Use templates (coder, researcher, writer, analyst)

## Available Resources

Big Homie exposes these resources via MCP:

- `profile://<profile_id>` - Access agent profile configurations
- Memory and knowledge base (if configured)

## Available Prompts

Pre-configured prompt templates:

- `analyze_code` - Code analysis and review
- `explain_concept` - Technical concept explanations
- `debug_error` - Error debugging assistance

## Testing the Connection

### From Claude Desktop
1. Restart Claude Desktop after updating the config
2. Start a conversation
3. Try: "Use the web_search tool to find the latest news about AI"
4. Claude should now have access to Big Homie's web search

### From Cursor
1. Restart Cursor after updating settings
2. Open the command palette (Cmd/Ctrl+Shift+P)
3. Try asking Cursor to use Big Homie's tools
4. Example: "Create a persistent shell session and run npm install"

## Troubleshooting

### Server Not Connecting

1. **Check Python path**: Make sure `python` points to your Python 3.8+ installation
   ```bash
   python --version
   ```

2. **Check working directory**: The `cwd` should point to the Big-Homie directory
   ```bash
   ls /path/to/Big-Homie/mcp_server_main.py
   ```

3. **Check dependencies**: Ensure all requirements are installed
   ```bash
   cd /path/to/Big-Homie
   pip install -r requirements.txt
   ```

4. **Check logs**: Look for errors in the MCP server output
   - Claude Desktop: Check `~/Library/Logs/Claude/`
   - Cursor: Check Output panel → MCP Server

### Tools Not Appearing

1. **Restart the client**: Fully quit and restart Claude Desktop/Cursor
2. **Verify config syntax**: Ensure JSON is valid (no trailing commas, quotes matched)
3. **Check API keys**: Some tools require API keys in `.env`
   ```bash
   # In Big-Homie directory
   cp .env.example .env
   # Edit .env with your API keys
   ```

### Permission Errors

Some tools require confirmation by default. The confirmation system works differently in MCP mode:

- Tools marked `requires_confirmation: false` work immediately
- Tools marked `requires_confirmation: true` may need user approval in the client

## Environment Variables

Set these in your `.env` file to enable full functionality:

```bash
# LLM Providers
ANTHROPIC_API_KEY=your-key
OPENAI_API_KEY=your-key
HUGGINGFACE_API_KEY=your-key

# Web Search
SERP_API_KEY=your-key

# Media Generation
GOOGLE_LYRIA_API_KEY=your-key
MINIMAX_API_KEY=your-key
COMFYUI_ENABLED=true

# GitHub
GITHUB_TOKEN=your-token
```

## Advanced Configuration

### Custom Python Environment

If using a virtual environment:

```json
{
  "mcpServers": {
    "big-homie": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "mcp_server_main"],
      "cwd": "/path/to/Big-Homie"
    }
  }
}
```

### Environment Variables in Config

Pass environment variables to the MCP server:

```json
{
  "mcpServers": {
    "big-homie": {
      "command": "python",
      "args": ["-m", "mcp_server_main"],
      "cwd": "/path/to/Big-Homie",
      "env": {
        "SERP_API_KEY": "your-key",
        "DEBUG": "true"
      }
    }
  }
}
```

## Security Notes

- MCP servers run locally on your machine
- Big Homie only executes tools you explicitly request
- Sensitive operations require confirmation
- Shell commands are restricted by default
- All data stays on your machine unless you use external APIs

## Support

For issues or questions:
- GitHub Issues: https://github.com/tap919/Big-Homie/issues
- Check logs in `~/.big_homie/logs/`
- Enable debug mode: Set `DEBUG=true` in `.env`
