"""
Native MCP Server Mode for Big Homie
Connect Big Homie to Claude Desktop, Cursor, and VS Code as a callable service
"""

import asyncio
import json
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

from loguru import logger


class MCPMessageType(str, Enum):
    """MCP message types"""

    INITIALIZE = "initialize"
    INITIALIZED = "initialized"
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"
    COMPLETION_COMPLETE = "completion/complete"


@dataclass
class MCPMessage:
    """MCP protocol message"""

    jsonrpc: str = "2.0"
    id: Optional[int] = None
    method: Optional[str] = None
    params: Optional[dict] = None
    result: Optional[Any] = None
    error: Optional[dict] = None


class MCPServer:
    """
    Model Context Protocol server implementation

    Allows Big Homie to be used as an MCP server by:
    - Claude Desktop
    - Cursor IDE
    - VS Code with Claude extension
    - Any MCP-compatible client

    Features:
    - Standard MCP protocol support
    - Tool discovery and execution
    - Resource management
    - Prompt templates
    - Bidirectional streaming
    """

    def __init__(self):
        """Initialize the MCP server"""
        self.tools: dict[str, dict] = {}
        self.resources: dict[str, dict] = {}
        self.prompts: dict[str, dict] = {}
        self.handlers: dict[str, Callable] = {}
        self._register_handlers()
        self.server_info = {"name": "big-homie", "version": "1.0.0"}

    def _register_handlers(self):
        """Register MCP method handlers"""
        self.handlers = {
            MCPMessageType.INITIALIZE: self._handle_initialize,
            MCPMessageType.TOOLS_LIST: self._handle_tools_list,
            MCPMessageType.TOOLS_CALL: self._handle_tools_call,
            MCPMessageType.RESOURCES_LIST: self._handle_resources_list,
            MCPMessageType.RESOURCES_READ: self._handle_resources_read,
            MCPMessageType.PROMPTS_LIST: self._handle_prompts_list,
            MCPMessageType.PROMPTS_GET: self._handle_prompts_get,
        }

    async def start_stdio_server(self):
        """
        Start MCP server in stdio mode (for Claude Desktop/Cursor)

        Reads JSON-RPC messages from stdin and writes responses to stdout
        """
        logger.info("Starting MCP server in stdio mode")

        async def read_stdin():
            """Read messages from stdin"""
            loop = asyncio.get_event_loop()
            reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(reader)
            await loop.connect_read_pipe(lambda: protocol, sys.stdin.buffer)
            return reader

        async def write_stdout(message: dict):
            """Write message to stdout"""
            output = json.dumps(message) + "\n"
            sys.stdout.buffer.write(output.encode())
            sys.stdout.buffer.flush()

        reader = await read_stdin()

        while True:
            try:
                # Read JSON-RPC message
                line = await reader.readline()
                if not line:
                    break

                message_data = json.loads(line.decode())
                request = MCPMessage(**message_data)

                # Process message
                response = await self.handle_message(request)

                # Send response
                if response:
                    await write_stdout(response.__dict__)

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                await write_stdout(
                    {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}
                )
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await write_stdout(
                    {
                        "jsonrpc": "2.0",
                        "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                    }
                )

    async def handle_message(self, request: MCPMessage) -> Optional[MCPMessage]:
        """
        Handle an MCP message

        Args:
            request: Incoming MCP message

        Returns:
            Response message or None
        """
        method = request.method

        if not method:
            return MCPMessage(
                id=request.id, error={"code": -32600, "message": "Invalid request: missing method"}
            )

        handler = self.handlers.get(method)

        if not handler:
            return MCPMessage(
                id=request.id, error={"code": -32601, "message": f"Method not found: {method}"}
            )

        try:
            result = await handler(request.params or {})
            return MCPMessage(id=request.id, result=result)
        except Exception as e:
            logger.error(f"Handler error for {method}: {e}")
            return MCPMessage(id=request.id, error={"code": -32603, "message": str(e)})

    async def _handle_initialize(self, params: dict) -> dict:
        """Handle initialize request"""
        logger.info(f"MCP client initializing: {params.get('clientInfo', {})}")

        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": self.server_info,
            "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
        }

    async def _handle_tools_list(self, params: dict) -> dict:
        """List available tools"""
        from mcp_integration import mcp

        # Get all tools from MCP integration
        tools = []
        for tool_name, tool_def in mcp.tools.items():
            if not tool_def.enabled:
                continue

            # Convert to MCP tool format
            tools.append(
                {
                    "name": tool_name,
                    "description": tool_def.description,
                    "inputSchema": {
                        "type": "object",
                        "properties": tool_def.parameters,
                        "required": [
                            param_name
                            for param_name, param_def in tool_def.parameters.items()
                            if not param_def.get("optional", False)
                        ],
                    },
                }
            )

        return {"tools": tools}

    async def _handle_tools_call(self, params: dict) -> dict:
        """Execute a tool"""
        from mcp_integration import mcp

        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if not tool_name:
            raise ValueError("Missing tool name")

        # Execute tool via MCP integration.
        # MCP clients have already confirmed their intent by calling the tool;
        # pass confirmed=True so tools that require_confirmation can proceed.
        result = await mcp.execute_tool(tool_name, arguments, context={"confirmed": True})

        if not result.success:
            raise ValueError(result.error or "Tool execution failed")

        return {"content": [{"type": "text", "text": json.dumps(result.data, indent=2)}]}

    async def _handle_resources_list(self, params: dict) -> dict:
        """List available resources"""
        # Resources could include:
        # - Memory/knowledge base
        # - Agent profiles
        # - Configuration
        from agent_profiles import profile_manager

        resources = []

        # Add agent profiles as resources
        for profile in profile_manager.list_profiles():
            resources.append(
                {
                    "uri": f"profile://{profile.profile_id}",
                    "name": f"Agent Profile: {profile.name}",
                    "description": profile.role,
                    "mimeType": "application/json",
                }
            )

        return {"resources": resources}

    async def _handle_resources_read(self, params: dict) -> dict:
        """Read a resource"""
        uri = params.get("uri")

        if not uri:
            raise ValueError("Missing resource URI")

        # Handle profile:// URIs
        if uri.startswith("profile://"):
            from agent_profiles import profile_manager

            profile_id = uri.replace("profile://", "")
            profile = profile_manager.get_profile(profile_id)

            if not profile:
                raise ValueError(f"Profile not found: {profile_id}")

            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(profile.to_dict(), indent=2),
                    }
                ]
            }

        raise ValueError(f"Unknown resource URI: {uri}")

    async def _handle_prompts_list(self, params: dict) -> dict:
        """List available prompt templates"""
        prompts = [
            {
                "name": "analyze_code",
                "description": "Analyze code for issues and improvements",
                "arguments": [
                    {"name": "code", "description": "Code to analyze", "required": True},
                    {"name": "language", "description": "Programming language", "required": False},
                ],
            },
            {
                "name": "explain_concept",
                "description": "Explain a technical concept",
                "arguments": [
                    {"name": "concept", "description": "Concept to explain", "required": True}
                ],
            },
            {
                "name": "debug_error",
                "description": "Help debug an error message",
                "arguments": [
                    {"name": "error", "description": "Error message", "required": True},
                    {"name": "context", "description": "Additional context", "required": False},
                ],
            },
        ]

        return {"prompts": prompts}

    async def _handle_prompts_get(self, params: dict) -> dict:
        """Get a prompt template"""
        name = params.get("name")
        arguments = params.get("arguments", {})

        prompts = {
            "analyze_code": {
                "description": "Analyze code for issues and improvements",
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": f"Please analyze this {arguments.get('language', '')} code for potential issues, improvements, and best practices:\n\n```\n{arguments.get('code', '')}\n```",
                        },
                    }
                ],
            },
            "explain_concept": {
                "description": "Explain a technical concept",
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": f"Please explain the following technical concept in clear, accessible terms:\n\n{arguments.get('concept', '')}",
                        },
                    }
                ],
            },
            "debug_error": {
                "description": "Help debug an error",
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": (
                                f"I'm getting the following error:\n\n{arguments.get('error', '')}\n\n"
                                + (
                                    f"Context: {arguments.get('context', '')}\n\n"
                                    if arguments.get("context")
                                    else ""
                                )
                                + "Can you help me understand what's causing this and how to fix it?"
                            ),
                        },
                    }
                ],
            },
        }

        if name not in prompts:
            raise ValueError(f"Unknown prompt: {name}")

        return prompts[name]

    def generate_config_for_claude_desktop(self) -> dict:
        """
        Generate configuration for Claude Desktop

        Returns:
            Configuration dict to add to claude_desktop_config.json
        """
        return {
            "mcpServers": {
                "big-homie": {
                    "command": sys.executable,
                    "args": ["-m", "mcp_server_main"],
                    "env": {},
                }
            }
        }

    def generate_config_for_vscode(self) -> dict:
        """
        Generate configuration for VS Code

        Returns:
            Configuration dict to add to settings.json
        """
        return {
            "claude.mcpServers": {
                "big-homie": {"command": "python", "args": ["-m", "mcp_server_main"]}
            }
        }


# Global MCP server instance
mcp_server = MCPServer()

if __name__ == "__main__":
    import sys

    asyncio.run(mcp_server.start_stdio_server())
