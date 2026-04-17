"""
MCP (Model Context Protocol) Integration Layer
Enables Big Homie to connect to external tools and APIs
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

import httpx
from loguru import logger


class ToolType(str, Enum):
    """Types of tools available via MCP"""

    API = "api"  # External API calls
    BROWSER = "browser"  # Browser automation
    FILE = "file"  # File operations
    SHELL = "shell"  # Shell commands
    DATABASE = "database"  # Database queries
    CUSTOM = "custom"  # Custom integrations
    CLOUD = "cloud"  # Cloud infrastructure
    BLOCKCHAIN = "blockchain"  # Blockchain operations
    DATA = "data"  # Data retrieval


@dataclass
class ToolDefinition:
    """Definition of a tool available to the agent"""

    name: str
    type: ToolType
    description: str
    parameters: dict[str, Any]
    handler: Optional[Callable] = None
    enabled: bool = True
    requires_confirmation: bool = False


@dataclass
class ToolCall:
    """A tool invocation request"""

    tool_name: str
    arguments: dict[str, Any]
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult:
    """Result of a tool execution"""

    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class MCPIntegration:
    """
    Model Context Protocol integration layer

    Provides tools for agents to interact with external systems:
    - GitHub API (repos, issues, PRs)
    - Stripe API (payments, subscriptions)
    - Browser automation (Playwright)
    - File system operations
    - Shell commands
    - Database queries
    """

    def __init__(self):
        self.tools: dict[str, ToolDefinition] = {}
        self.tool_usage_log: list[dict] = []
        self._register_default_tools()

    def _register_default_tools(self):
        """Register built-in tools"""

        # GitHub API Tools
        self.register_tool(
            ToolDefinition(
                name="github_create_issue",
                type=ToolType.API,
                description="Create a GitHub issue in a repository",
                parameters={
                    "repo": {"type": "string", "description": "Repository in format owner/name"},
                    "title": {"type": "string", "description": "Issue title"},
                    "body": {"type": "string", "description": "Issue description"},
                    "labels": {"type": "array", "description": "Optional labels", "optional": True},
                },
                handler=self._github_create_issue,
                requires_confirmation=True,
            )
        )

        self.register_tool(
            ToolDefinition(
                name="github_search_repos",
                type=ToolType.API,
                description="Search GitHub repositories",
                parameters={
                    "query": {"type": "string", "description": "Search query"},
                    "language": {
                        "type": "string",
                        "description": "Filter by language",
                        "optional": True,
                    },
                    "limit": {"type": "integer", "description": "Max results", "default": 10},
                },
                handler=self._github_search_repos,
            )
        )

        # Browser Tools
        self.register_tool(
            ToolDefinition(
                name="browser_navigate",
                type=ToolType.BROWSER,
                description="Navigate to a URL and get page content",
                parameters={
                    "url": {"type": "string", "description": "URL to visit"},
                    "wait_for": {
                        "type": "string",
                        "description": "CSS selector to wait for",
                        "optional": True,
                    },
                },
                handler=self._browser_navigate,
            )
        )

        self.register_tool(
            ToolDefinition(
                name="browser_screenshot",
                type=ToolType.BROWSER,
                description="Take a screenshot of a webpage",
                parameters={
                    "url": {"type": "string", "description": "URL to screenshot"},
                    "full_page": {
                        "type": "boolean",
                        "description": "Capture full page",
                        "default": True,
                    },
                },
                handler=self._browser_screenshot,
            )
        )

        # File Tools
        self.register_tool(
            ToolDefinition(
                name="file_read",
                type=ToolType.FILE,
                description="Read contents of a file",
                parameters={"path": {"type": "string", "description": "File path"}},
                handler=self._file_read,
            )
        )

        self.register_tool(
            ToolDefinition(
                name="file_write",
                type=ToolType.FILE,
                description="Write content to a file",
                parameters={
                    "path": {"type": "string", "description": "File path"},
                    "content": {"type": "string", "description": "Content to write"},
                },
                handler=self._file_write,
                requires_confirmation=True,
            )
        )

        # Shell Tools
        self.register_tool(
            ToolDefinition(
                name="shell_execute",
                type=ToolType.SHELL,
                description="Execute a shell command (disabled by default; enable explicitly)",
                parameters={
                    "command": {"type": "string", "description": "Command to execute"},
                    "cwd": {"type": "string", "description": "Working directory", "optional": True},
                },
                handler=self._shell_execute,
                requires_confirmation=True,
                enabled=False,  # Disabled by default to prevent arbitrary command execution
            )
        )

        # Persistent Shell Tools
        self.register_tool(
            ToolDefinition(
                name="shell_session_create",
                type=ToolType.SHELL,
                description="Create a persistent shell session that maintains state across commands",
                parameters={
                    "cwd": {"type": "string", "description": "Working directory", "optional": True}
                },
                handler=self._shell_session_create,
                requires_confirmation=False,
            )
        )

        self.register_tool(
            ToolDefinition(
                name="shell_session_execute",
                type=ToolType.SHELL,
                description="Execute a command in a persistent shell session",
                parameters={
                    "session_id": {
                        "type": "string",
                        "description": "Session ID from shell_session_create",
                    },
                    "command": {"type": "string", "description": "Command to execute"},
                    "timeout": {
                        "type": "number",
                        "description": "Command timeout in seconds",
                        "optional": True,
                        "default": 30,
                    },
                },
                handler=self._shell_session_execute,
                requires_confirmation=True,
            )
        )

        self.register_tool(
            ToolDefinition(
                name="shell_session_list",
                type=ToolType.SHELL,
                description="List all active persistent shell sessions",
                parameters={},
                handler=self._shell_session_list,
                requires_confirmation=False,
            )
        )

        self.register_tool(
            ToolDefinition(
                name="shell_session_terminate",
                type=ToolType.SHELL,
                description="Terminate a persistent shell session",
                parameters={
                    "session_id": {"type": "string", "description": "Session ID to terminate"}
                },
                handler=self._shell_session_terminate,
                requires_confirmation=False,
            )
        )

        # Vision Tools
        self.register_tool(
            ToolDefinition(
                name="vision_analyze_image",
                type=ToolType.CUSTOM,
                description="Analyze an image using vision AI (image must be in the screenshots directory)",
                parameters={
                    "image_path": {
                        "type": "string",
                        "description": "Path to image file (must be within the screenshots data directory)",
                    },
                    "prompt": {"type": "string", "description": "Analysis question or prompt"},
                    "quality": {
                        "type": "string",
                        "description": "Quality level: fast, good, high, excellent",
                        "default": "fast",
                    },
                },
                handler=self._vision_analyze,
                requires_confirmation=True,
            )
        )

        self.register_tool(
            ToolDefinition(
                name="vision_extract_text",
                type=ToolType.CUSTOM,
                description="Extract text from an image using OCR (image must be in the screenshots directory)",
                parameters={
                    "image_path": {
                        "type": "string",
                        "description": "Path to image file (must be within the screenshots data directory)",
                    }
                },
                handler=self._vision_extract_text,
                requires_confirmation=True,
            )
        )

        self.register_tool(
            ToolDefinition(
                name="vision_audit_ui",
                type=ToolType.CUSTOM,
                description="Perform UI/UX audit on a design or screenshot (image must be in the screenshots directory)",
                parameters={
                    "image_path": {
                        "type": "string",
                        "description": "Path to UI screenshot or mockup (must be within the screenshots data directory)",
                    },
                    "focus_areas": {
                        "type": "array",
                        "description": "Areas to focus on (optional)",
                        "optional": True,
                    },
                },
                handler=self._vision_audit_ui,
                requires_confirmation=True,
            )
        )

        # Media Generation Tools
        self.register_tool(
            ToolDefinition(
                name="image_generate",
                type=ToolType.CUSTOM,
                description="Generate an image using AI (ComfyUI workflows)",
                parameters={
                    "prompt": {
                        "type": "string",
                        "description": "Text description of the image to generate",
                    },
                    "workflow": {
                        "type": "string",
                        "description": "ComfyUI workflow name",
                        "optional": True,
                        "default": "default",
                    },
                    "reference_image": {
                        "type": "string",
                        "description": "Path to reference image (optional)",
                        "optional": True,
                    },
                    "width": {
                        "type": "integer",
                        "description": "Image width",
                        "optional": True,
                        "default": 512,
                    },
                    "height": {
                        "type": "integer",
                        "description": "Image height",
                        "optional": True,
                        "default": 512,
                    },
                },
                handler=self._image_generate,
                requires_confirmation=True,
            )
        )

        self.register_tool(
            ToolDefinition(
                name="video_generate",
                type=ToolType.CUSTOM,
                description="Generate a video using AI (MiniMax or ComfyUI)",
                parameters={
                    "prompt": {
                        "type": "string",
                        "description": "Text description of the video to generate",
                    },
                    "provider": {
                        "type": "string",
                        "description": "Provider: minimax or comfyui",
                        "optional": True,
                    },
                    "duration": {
                        "type": "number",
                        "description": "Video duration in seconds (if supported)",
                        "optional": True,
                    },
                    "width": {"type": "integer", "description": "Video width", "optional": True},
                    "height": {"type": "integer", "description": "Video height", "optional": True},
                    "fps": {
                        "type": "integer",
                        "description": "Frames per second",
                        "optional": True,
                    },
                },
                handler=self._video_generate,
                requires_confirmation=True,
            )
        )

        self.register_tool(
            ToolDefinition(
                name="music_generate",
                type=ToolType.CUSTOM,
                description="Generate music or audio using AI (Google Lyria, MiniMax, or ComfyUI)",
                parameters={
                    "prompt": {
                        "type": "string",
                        "description": "Text description of the music to generate",
                    },
                    "provider": {
                        "type": "string",
                        "description": "Provider: google_lyria, minimax, or comfyui",
                        "optional": True,
                    },
                    "durationSeconds": {
                        "type": "number",
                        "description": "Desired duration in seconds (may be ignored by some providers)",
                        "optional": True,
                    },
                    "genre": {
                        "type": "string",
                        "description": "Music genre (optional)",
                        "optional": True,
                    },
                    "mood": {
                        "type": "string",
                        "description": "Music mood (optional)",
                        "optional": True,
                    },
                    "tempo": {
                        "type": "string",
                        "description": "Tempo: slow, medium, fast (optional)",
                        "optional": True,
                    },
                },
                handler=self._music_generate,
                requires_confirmation=True,
            )
        )

        # Web Search Tool
        self.register_tool(
            ToolDefinition(
                name="web_search",
                type=ToolType.API,
                description="Search the web using natural language queries to find current information, news, articles, and websites",
                parameters={
                    "query": {"type": "string", "description": "Natural language search query"},
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "optional": True,
                        "default": 5,
                    },
                    "search_type": {
                        "type": "string",
                        "description": "Type of search: web, news, images (default: web)",
                        "optional": True,
                        "default": "web",
                    },
                },
                handler=self._web_search,
                requires_confirmation=False,
            )
        )

        # Agent Profile Management Tools
        self.register_tool(
            ToolDefinition(
                name="profile_create",
                type=ToolType.CUSTOM,
                description="Create a new agent profile with custom configuration",
                parameters={
                    "name": {"type": "string", "description": "Profile name"},
                    "role": {"type": "string", "description": "Agent role description"},
                    "system_prompt": {"type": "string", "description": "Custom system prompt"},
                    "model": {"type": "string", "description": "Model to use", "optional": True},
                    "temperature": {
                        "type": "number",
                        "description": "Temperature (0-1)",
                        "optional": True,
                    },
                    "tools_enabled": {
                        "type": "array",
                        "description": "List of enabled tools",
                        "optional": True,
                    },
                    "memory_isolated": {
                        "type": "boolean",
                        "description": "Use isolated memory",
                        "optional": True,
                        "default": True,
                    },
                },
                handler=self._profile_create,
                requires_confirmation=False,
            )
        )

        self.register_tool(
            ToolDefinition(
                name="profile_list",
                type=ToolType.CUSTOM,
                description="List all agent profiles",
                parameters={},
                handler=self._profile_list,
                requires_confirmation=False,
            )
        )

        self.register_tool(
            ToolDefinition(
                name="profile_switch",
                type=ToolType.CUSTOM,
                description="Switch to a different agent profile",
                parameters={
                    "profile_id": {"type": "string", "description": "Profile ID to switch to"}
                },
                handler=self._profile_switch,
                requires_confirmation=False,
            )
        )

        self.register_tool(
            ToolDefinition(
                name="profile_get_active",
                type=ToolType.CUSTOM,
                description="Get the currently active agent profile",
                parameters={},
                handler=self._profile_get_active,
                requires_confirmation=False,
            )
        )

        self.register_tool(
            ToolDefinition(
                name="profile_delete",
                type=ToolType.CUSTOM,
                description="Delete an agent profile",
                parameters={
                    "profile_id": {"type": "string", "description": "Profile ID to delete"}
                },
                handler=self._profile_delete,
                requires_confirmation=True,
            )
        )

        self.register_tool(
            ToolDefinition(
                name="profile_create_from_template",
                type=ToolType.CUSTOM,
                description="Create a profile from a template (coder, researcher, writer, analyst)",
                parameters={
                    "template_name": {
                        "type": "string",
                        "description": "Template name: coder, researcher, writer, or analyst",
                    },
                    "custom_name": {
                        "type": "string",
                        "description": "Custom profile name",
                        "optional": True,
                    },
                },
                handler=self._profile_create_from_template,
                requires_confirmation=False,
            )
        )

        # Cloudflare Tools
        self.register_tool(
            ToolDefinition(
                name="cloudflare_deploy_worker",
                type=ToolType.API,
                description="Deploy a Cloudflare Worker script",
                parameters={
                    "script_name": {"type": "string", "description": "Name of the Worker script"},
                    "script_content": {
                        "type": "string",
                        "description": "JavaScript/TypeScript code for the Worker",
                    },
                    "bindings": {
                        "type": "array",
                        "description": "KV/R2 bindings",
                        "optional": True,
                    },
                },
                handler=self._cloudflare_deploy_worker,
                requires_confirmation=True,
            )
        )

        self.register_tool(
            ToolDefinition(
                name="cloudflare_kv_write",
                type=ToolType.API,
                description="Write a key-value pair to Cloudflare KV storage",
                parameters={
                    "namespace_id": {"type": "string", "description": "KV namespace ID"},
                    "key": {"type": "string", "description": "Key name"},
                    "value": {"type": "string", "description": "Value to store"},
                },
                handler=self._cloudflare_kv_write,
                requires_confirmation=True,
            )
        )

        self.register_tool(
            ToolDefinition(
                name="cloudflare_kv_read",
                type=ToolType.API,
                description="Read a value from Cloudflare KV storage",
                parameters={
                    "namespace_id": {"type": "string", "description": "KV namespace ID"},
                    "key": {"type": "string", "description": "Key name"},
                },
                handler=self._cloudflare_kv_read,
                requires_confirmation=False,
            )
        )

        # Vercel Tools
        self.register_tool(
            ToolDefinition(
                name="vercel_deploy",
                type=ToolType.API,
                description="Deploy a project to Vercel",
                parameters={
                    "project_name": {"type": "string", "description": "Project name"},
                    "files": {
                        "type": "object",
                        "description": "Files to deploy (path: content mapping)",
                    },
                    "env_vars": {
                        "type": "object",
                        "description": "Environment variables",
                        "optional": True,
                    },
                },
                handler=self._vercel_deploy,
                requires_confirmation=True,
            )
        )

        self.register_tool(
            ToolDefinition(
                name="vercel_list_deployments",
                type=ToolType.API,
                description="List recent Vercel deployments",
                parameters={
                    "project_id": {"type": "string", "description": "Project ID", "optional": True},
                    "limit": {"type": "integer", "description": "Max results", "default": 20},
                },
                handler=self._vercel_list_deployments,
                requires_confirmation=False,
            )
        )

        # Stripe Tools
        self.register_tool(
            ToolDefinition(
                name="stripe_create_customer",
                type=ToolType.API,
                description="Create a Stripe customer",
                parameters={
                    "email": {"type": "string", "description": "Customer email"},
                    "name": {"type": "string", "description": "Customer name", "optional": True},
                },
                handler=self._stripe_create_customer,
                requires_confirmation=True,
            )
        )

        self.register_tool(
            ToolDefinition(
                name="stripe_create_payment_intent",
                type=ToolType.API,
                description="Create a Stripe payment intent (REQUIRES CONFIRMATION)",
                parameters={
                    "amount": {"type": "integer", "description": "Amount in cents"},
                    "currency": {
                        "type": "string",
                        "description": "Currency code",
                        "default": "usd",
                    },
                    "customer_id": {
                        "type": "string",
                        "description": "Customer ID",
                        "optional": True,
                    },
                },
                handler=self._stripe_create_payment_intent,
                requires_confirmation=True,
            )
        )

        # Perplexity Tools
        self.register_tool(
            ToolDefinition(
                name="perplexity_search",
                type=ToolType.API,
                description="Search using Perplexity AI with citations",
                parameters={
                    "query": {"type": "string", "description": "Search query"},
                    "max_tokens": {
                        "type": "integer",
                        "description": "Max response tokens",
                        "default": 4096,
                    },
                },
                handler=self._perplexity_search,
                requires_confirmation=False,
            )
        )

        # Coinbase Commerce Tools
        self.register_tool(
            ToolDefinition(
                name="coinbase_create_charge",
                type=ToolType.API,
                description="Create a cryptocurrency charge (REQUIRES CONFIRMATION)",
                parameters={
                    "name": {"type": "string", "description": "Charge name"},
                    "description": {"type": "string", "description": "Charge description"},
                    "amount": {"type": "string", "description": "Amount in local currency"},
                    "currency": {
                        "type": "string",
                        "description": "Currency code",
                        "default": "USD",
                    },
                },
                handler=self._coinbase_create_charge,
                requires_confirmation=True,
            )
        )

        # Base L2 Tools
        self.register_tool(
            ToolDefinition(
                name="base_get_balance",
                type=ToolType.BLOCKCHAIN,
                description="Get ETH balance on Base L2",
                parameters={
                    "address": {"type": "string", "description": "Wallet address", "optional": True}
                },
                handler=self._base_get_balance,
                requires_confirmation=False,
            )
        )

        self.register_tool(
            ToolDefinition(
                name="base_send_transaction",
                type=ToolType.BLOCKCHAIN,
                description="Send ETH on Base L2 (REQUIRES CONFIRMATION)",
                parameters={
                    "to_address": {"type": "string", "description": "Recipient address"},
                    "amount_eth": {"type": "number", "description": "Amount in ETH"},
                },
                handler=self._base_send_transaction,
                requires_confirmation=True,
            )
        )

        # DraftKings Tools
        self.register_tool(
            ToolDefinition(
                name="draftkings_get_odds",
                type=ToolType.DATA,
                description="Get sports odds from DraftKings (read-only)",
                parameters={
                    "sport": {
                        "type": "string",
                        "description": "Sport type",
                        "default": "BASKETBALL",
                    },
                    "league": {"type": "string", "description": "League name", "default": "NBA"},
                },
                handler=self._draftkings_get_odds,
                requires_confirmation=False,
            )
        )

        # PrizePicks Tools
        self.register_tool(
            ToolDefinition(
                name="prizepicks_get_projections",
                type=ToolType.DATA,
                description="Get player projections from PrizePicks (read-only)",
                parameters={
                    "league": {"type": "string", "description": "League filter", "optional": True},
                    "per_page": {
                        "type": "integer",
                        "description": "Results per page",
                        "default": 100,
                    },
                },
                handler=self._prizepicks_get_projections,
                requires_confirmation=False,
            )
        )

        # Google Cloud Tools
        self.register_tool(
            ToolDefinition(
                name="gcs_upload_file",
                type=ToolType.CLOUD,
                description="Upload a file to Google Cloud Storage",
                parameters={
                    "bucket_name": {"type": "string", "description": "GCS bucket name"},
                    "source_file_path": {"type": "string", "description": "Local file path"},
                    "destination_blob_name": {
                        "type": "string",
                        "description": "Destination path in bucket",
                    },
                },
                handler=self._gcs_upload_file,
                requires_confirmation=True,
            )
        )

        self.register_tool(
            ToolDefinition(
                name="bigquery_query",
                type=ToolType.DATABASE,
                description="Execute a BigQuery SQL query",
                parameters={"query": {"type": "string", "description": "SQL query to execute"}},
                handler=self._bigquery_query,
                requires_confirmation=True,
            )
        )

    def register_tool(self, tool: ToolDefinition):
        """Register a new tool"""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name} ({tool.type.value})")

    async def execute_tool(
        self, tool_name: str, arguments: dict[str, Any], context: Optional[dict] = None
    ) -> ToolResult:
        """Execute a tool by name"""

        if tool_name not in self.tools:
            return ToolResult(success=False, error=f"Tool '{tool_name}' not found")

        tool = self.tools[tool_name]

        if not tool.enabled:
            return ToolResult(success=False, error=f"Tool '{tool_name}' is disabled")

        # Validate parameters
        validation_error = self._validate_parameters(tool, arguments)
        if validation_error:
            return ToolResult(success=False, error=validation_error)

        # Gate high-risk operations behind explicit confirmation in context
        if tool.requires_confirmation:
            confirmed = (context or {}).get("confirmed", False)
            if not confirmed:
                return ToolResult(
                    success=False,
                    error=(
                        f"Tool '{tool_name}' requires explicit confirmation. "
                        "Re-invoke with context={'confirmed': True} to proceed."
                    ),
                )

        # Log tool usage
        self.tool_usage_log.append(
            {
                "tool": tool_name,
                "arguments": arguments,
                "timestamp": asyncio.get_event_loop().time(),
            }
        )

        try:
            # Execute tool handler
            if tool.handler:
                result_data = await tool.handler(arguments, context or {})
                return ToolResult(
                    success=True, data=result_data, metadata={"tool_type": tool.type.value}
                )
            else:
                return ToolResult(success=False, error="Tool has no handler implementation")

        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name} - {e}")
            return ToolResult(success=False, error=str(e))

    def _validate_parameters(self, tool: ToolDefinition, arguments: dict) -> Optional[str]:
        """Validate tool parameters"""
        for param_name, param_def in tool.parameters.items():
            if param_def.get("optional", False):
                continue

            if param_name not in arguments:
                return f"Missing required parameter: {param_name}"

        return None

    # Tool Handlers

    async def _github_create_issue(self, args: dict, context: dict) -> dict:
        """Create a GitHub issue"""
        from config import settings

        if not settings.github_token:
            raise ValueError("GITHUB_TOKEN not configured")

        repo = args["repo"]
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.github.com/repos/{repo}/issues",
                headers={
                    "Authorization": f"Bearer {settings.github_token}",
                    "Accept": "application/vnd.github+json",
                },
                json={
                    "title": args["title"],
                    "body": args["body"],
                    "labels": args.get("labels", []),
                },
            )
            response.raise_for_status()
            return response.json()

    async def _github_search_repos(self, args: dict, context: dict) -> dict:
        """Search GitHub repositories"""
        query = args["query"]
        if args.get("language"):
            query += f" language:{args['language']}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/search/repositories",
                params={"q": query, "per_page": args.get("limit", 10)},
                headers={"Accept": "application/vnd.github+json"},
            )
            response.raise_for_status()
            data = response.json()
            return {
                "total_count": data["total_count"],
                "repositories": [
                    {
                        "name": repo["full_name"],
                        "description": repo["description"],
                        "stars": repo["stargazers_count"],
                        "url": repo["html_url"],
                    }
                    for repo in data["items"]
                ],
            }

    async def _browser_navigate(self, args: dict, context: dict) -> dict:
        """Navigate to URL using Playwright"""
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                await page.goto(args["url"])

                if args.get("wait_for"):
                    await page.wait_for_selector(args["wait_for"], timeout=5000)

                content = await page.content()
                title = await page.title()

                return {
                    "url": page.url,
                    "title": title,
                    "content": content[:5000],  # First 5KB
                }
            finally:
                await browser.close()

    async def _browser_screenshot(self, args: dict, context: dict) -> dict:
        """Take screenshot of URL"""
        import base64

        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                await page.goto(args["url"])
                screenshot = await page.screenshot(full_page=args.get("full_page", True))

                # Return base64 encoded
                return {"url": page.url, "screenshot": base64.b64encode(screenshot).decode()}
            finally:
                await browser.close()

    async def _file_read(self, args: dict, context: dict) -> str:
        """Read file contents"""
        from pathlib import Path

        path = Path(args["path"])
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        return path.read_text()

    async def _file_write(self, args: dict, context: dict) -> dict:
        """Write file contents"""
        from pathlib import Path

        path = Path(args["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(args["content"])

        return {"path": str(path), "bytes_written": len(args["content"])}

    async def _shell_execute(self, args: dict, context: dict) -> dict:
        """Execute shell command (disabled by default; use argv list to prevent injection)"""
        import shlex
        import subprocess

        raw_command = args["command"]
        # Use shlex.split to avoid shell=True and prevent command injection
        try:
            argv = shlex.split(raw_command)
        except ValueError as exc:
            logger.warning(f"shell_execute: failed to parse command: {exc}")
            return {
                "stdout": "",
                "stderr": f"Invalid command: {exc}",
                "returncode": 1,
                "success": False,
            }

        result = subprocess.run(
            argv, shell=False, cwd=args.get("cwd"), capture_output=True, text=True, timeout=30
        )

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0,
        }

    def get_tools_for_llm(self) -> list[dict]:
        """
        Get tool definitions in format suitable for LLM function calling

        Returns list compatible with OpenAI/Anthropic function calling APIs
        """
        tools = []

        for tool in self.tools.values():
            if not tool.enabled:
                continue

            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": {
                            "type": "object",
                            "properties": tool.parameters,
                            "required": [
                                k
                                for k, v in tool.parameters.items()
                                if not v.get("optional", False)
                            ],
                        },
                    },
                }
            )

        return tools

    def get_tool_usage_stats(self) -> dict:
        """Get statistics on tool usage"""
        from collections import Counter

        tool_counts = Counter(entry["tool"] for entry in self.tool_usage_log)

        return {
            "total_calls": len(self.tool_usage_log),
            "unique_tools": len(tool_counts),
            "most_used": tool_counts.most_common(5),
        }

    # Vision tool handlers
    def _validate_image_path(self, image_path: str) -> str:
        """
        Validate that image_path is within the safe screenshots directory.

        Raises ValueError for any path that resolves outside the allowed directory
        to prevent model-driven arbitrary file reads.
        """
        from pathlib import Path

        from config import settings

        allowed_dir = (settings.data_dir / "screenshots").resolve()
        resolved = Path(image_path).resolve()

        if not resolved.is_relative_to(allowed_dir):
            raise ValueError(
                f"Image path '{image_path}' is outside the allowed screenshots directory. "
                f"Images must be stored in: {allowed_dir}"
            )

        return str(resolved)

    async def _vision_analyze(self, args: dict, context: dict) -> dict:
        """Analyze image with vision AI"""
        from config import settings
        from vision_analysis import vision_analyzer

        if not settings.enable_vision:
            raise ValueError("Vision capabilities are disabled in settings")

        image_path = self._validate_image_path(args["image_path"])

        result = await vision_analyzer.analyze_image(
            image_path=image_path, prompt=args["prompt"], quality=args.get("quality", "fast")
        )

        if not result.success:
            raise ValueError(f"Vision analysis failed: {result.error}")

        return {"analysis": result.analysis, "model_used": result.model_used, "cost": result.cost}

    async def _vision_extract_text(self, args: dict, context: dict) -> dict:
        """Extract text from image using OCR"""
        from config import settings
        from vision_analysis import vision_analyzer

        if not settings.enable_vision:
            raise ValueError("Vision capabilities are disabled in settings")

        image_path = self._validate_image_path(args["image_path"])

        result = await vision_analyzer.extract_text_from_image(
            image_path=image_path, use_local_ocr=settings.use_local_ocr
        )

        if not result.success:
            raise ValueError(f"Text extraction failed: {result.error}")

        return {
            "text": result.extracted_text,
            "method": "local_ocr" if result.cost == 0.0 else "vision_api",
            "cost": result.cost,
        }

    async def _vision_audit_ui(self, args: dict, context: dict) -> dict:
        """Perform UI/UX audit"""
        from config import settings
        from vision_analysis import vision_analyzer

        if not settings.enable_vision:
            raise ValueError("Vision capabilities are disabled in settings")

        image_path = self._validate_image_path(args["image_path"])

        result = await vision_analyzer.audit_ui_design(
            image_path=image_path, focus_areas=args.get("focus_areas")
        )

        if not result.success:
            raise ValueError(f"UI audit failed: {result.error}")

        return {"audit": result.analysis, "model_used": result.model_used, "cost": result.cost}

    # Media Generation Tool Handlers

    async def _image_generate(self, args: dict, context: dict) -> dict:
        """Generate an image using ComfyUI"""
        from config import settings
        from media_generation import MediaType, media_manager

        if not settings.enable_media_generation:
            raise ValueError("Media generation is disabled in settings")

        result = await media_manager.generate_media(
            media_type=MediaType.IMAGE,
            prompt=args["prompt"],
            provider="comfyui",
            workflow=args.get("workflow"),
            reference_image=args.get("reference_image"),
            width=args.get("width", 512),
            height=args.get("height", 512),
        )

        if not result.success:
            raise ValueError(f"Image generation failed: {result.error}")

        return {
            "success": True,
            "file_path": result.file_path,
            "url": result.url,
            "metadata": result.metadata,
        }

    async def _video_generate(self, args: dict, context: dict) -> dict:
        """Generate a video using MiniMax or ComfyUI"""
        from config import settings
        from media_generation import MediaType, media_manager

        if not settings.enable_media_generation:
            raise ValueError("Media generation is disabled in settings")

        result = await media_manager.generate_media(
            media_type=MediaType.VIDEO,
            prompt=args["prompt"],
            provider=args.get("provider"),
            duration=args.get("duration"),
            width=args.get("width"),
            height=args.get("height"),
            fps=args.get("fps"),
        )

        if not result.success:
            raise ValueError(f"Video generation failed: {result.error}")

        return {
            "success": True,
            "file_path": result.file_path,
            "url": result.url,
            "task_id": result.task_id,
            "status": result.status.value,
            "metadata": result.metadata,
        }

    async def _music_generate(self, args: dict, context: dict) -> dict:
        """Generate music using Google Lyria, MiniMax, or ComfyUI"""
        from config import settings
        from media_generation import MediaType, media_manager

        if not settings.enable_media_generation:
            raise ValueError("Media generation is disabled in settings")

        # Build parameters dict, including optional ones
        params = {}
        if "durationSeconds" in args:
            params["durationSeconds"] = args["durationSeconds"]
        if "genre" in args:
            params["genre"] = args["genre"]
        if "mood" in args:
            params["mood"] = args["mood"]
        if "tempo" in args:
            params["tempo"] = args["tempo"]

        result = await media_manager.generate_media(
            media_type=MediaType.MUSIC,
            prompt=args["prompt"],
            provider=args.get("provider"),
            **params,
        )

        if not result.success:
            raise ValueError(f"Music generation failed: {result.error}")

        return {
            "success": True,
            "file_path": result.file_path,
            "url": result.url,
            "task_id": result.task_id,
            "status": result.status.value,
            "metadata": result.metadata,
        }

    async def _web_search(self, args: dict, context: dict) -> dict:
        """Search the web using SERP API"""
        from config import settings

        if not settings.serp_api_key:
            raise ValueError("SERP API key not configured (set SERP_API_KEY in .env)")

        query = args["query"]
        num_results = args.get("num_results", 5)
        search_type = args.get("search_type", "web")

        # Build SERP API request
        params = {"q": query, "num": num_results, "api_key": settings.serp_api_key}

        # Select endpoint based on search type
        if search_type == "news":
            params["tbm"] = "nws"
        elif search_type == "images":
            params["tbm"] = "isch"

        async with httpx.AsyncClient() as client:
            response = await client.get("https://serpapi.com/search", params=params, timeout=30.0)

            if response.status_code != 200:
                raise ValueError(
                    f"SERP API request failed ({response.status_code}): {response.text}"
                )

            data = response.json()

            # Parse results based on search type
            if search_type == "images":
                results = [
                    {
                        "title": img.get("title", ""),
                        "url": img.get("original", ""),
                        "thumbnail": img.get("thumbnail", ""),
                        "source": img.get("source", ""),
                    }
                    for img in data.get("images_results", [])[:num_results]
                ]
            elif search_type == "news":
                results = [
                    {
                        "title": article.get("title", ""),
                        "url": article.get("link", ""),
                        "snippet": article.get("snippet", ""),
                        "source": article.get("source", ""),
                        "date": article.get("date", ""),
                    }
                    for article in data.get("news_results", [])[:num_results]
                ]
            else:  # web search
                results = [
                    {
                        "title": result.get("title", ""),
                        "url": result.get("link", ""),
                        "snippet": result.get("snippet", ""),
                        "position": result.get("position", 0),
                    }
                    for result in data.get("organic_results", [])[:num_results]
                ]

            # Include answer box if available (for quick facts)
            answer_box = data.get("answer_box")
            knowledge_graph = data.get("knowledge_graph")

            return {
                "success": True,
                "query": query,
                "search_type": search_type,
                "results": results,
                "answer_box": answer_box,
                "knowledge_graph": knowledge_graph,
                "total_results": len(results),
            }

    async def _shell_session_create(self, args: dict, context: dict) -> dict:
        """Create a persistent shell session"""
        from persistent_shell import shell_manager

        cwd = args.get("cwd")
        session_id = await shell_manager.create_session(cwd=cwd)

        return {
            "success": True,
            "session_id": session_id,
            "message": "Persistent shell session created. Use this session_id for subsequent commands.",
        }

    async def _shell_session_execute(self, args: dict, context: dict) -> dict:
        """Execute a command in a persistent shell session"""
        from persistent_shell import shell_manager

        session_id = args["session_id"]
        command = args["command"]
        timeout = args.get("timeout", 30.0)

        result = await shell_manager.execute_command(session_id, command, timeout)

        return {
            "success": True,
            "session_id": session_id,
            "command": command,
            "output": result["stdout"],
            "exit_code": result["exit_code"],
        }

    async def _shell_session_list(self, args: dict, context: dict) -> dict:
        """List all active persistent shell sessions"""
        from persistent_shell import shell_manager

        sessions = await shell_manager.list_sessions()

        return {"success": True, "sessions": sessions, "count": len(sessions)}

    async def _shell_session_terminate(self, args: dict, context: dict) -> dict:
        """Terminate a persistent shell session"""
        from persistent_shell import shell_manager

        session_id = args["session_id"]
        await shell_manager.terminate_session(session_id)

        return {"success": True, "session_id": session_id, "message": "Shell session terminated"}

    async def _profile_create(self, args: dict, context: dict) -> dict:
        """Create a new agent profile"""
        from agent_profiles import profile_manager

        profile = profile_manager.create_profile(
            name=args["name"],
            role=args["role"],
            system_prompt=args["system_prompt"],
            model=args.get("model"),
            temperature=args.get("temperature"),
            tools_enabled=args.get("tools_enabled"),
            memory_isolated=args.get("memory_isolated", True),
        )

        return {
            "success": True,
            "profile_id": profile.profile_id,
            "name": profile.name,
            "message": f"Profile '{profile.name}' created successfully",
        }

    async def _profile_list(self, args: dict, context: dict) -> dict:
        """List all agent profiles"""
        from agent_profiles import profile_manager

        profiles = profile_manager.list_profiles()
        active = profile_manager.get_active_profile()

        return {
            "success": True,
            "profiles": [
                {
                    "profile_id": p.profile_id,
                    "name": p.name,
                    "role": p.role,
                    "model": p.model,
                    "is_active": p.profile_id == (active.profile_id if active else None),
                }
                for p in profiles
            ],
            "count": len(profiles),
            "active_profile_id": active.profile_id if active else None,
        }

    async def _profile_switch(self, args: dict, context: dict) -> dict:
        """Switch to a different agent profile"""
        from agent_profiles import profile_manager

        profile = profile_manager.switch_profile(args["profile_id"])

        return {
            "success": True,
            "profile_id": profile.profile_id,
            "name": profile.name,
            "role": profile.role,
            "system_prompt": profile.system_prompt,
            "message": f"Switched to profile: {profile.name}",
        }

    async def _profile_get_active(self, args: dict, context: dict) -> dict:
        """Get the currently active agent profile"""
        from agent_profiles import profile_manager

        profile = profile_manager.get_active_profile()

        if not profile:
            return {"success": False, "error": "No active profile"}

        return {
            "success": True,
            "profile": {
                "profile_id": profile.profile_id,
                "name": profile.name,
                "role": profile.role,
                "system_prompt": profile.system_prompt,
                "model": profile.model,
                "temperature": profile.temperature,
                "max_tokens": profile.max_tokens,
                "tools_enabled": profile.tools_enabled,
                "memory_isolated": profile.memory_isolated,
            },
        }

    async def _profile_delete(self, args: dict, context: dict) -> dict:
        """Delete an agent profile"""
        from agent_profiles import profile_manager

        profile_manager.delete_profile(args["profile_id"])

        return {
            "success": True,
            "profile_id": args["profile_id"],
            "message": f"Profile '{args['profile_id']}' deleted",
        }

    async def _profile_create_from_template(self, args: dict, context: dict) -> dict:
        """Create a profile from a template"""
        from agent_profiles import profile_manager

        kwargs = {}
        if args.get("custom_name"):
            kwargs["name"] = args["custom_name"]

        profile = profile_manager.create_from_template(args["template_name"], **kwargs)

        return {
            "success": True,
            "profile_id": profile.profile_id,
            "name": profile.name,
            "role": profile.role,
            "message": f"Profile created from template: {args['template_name']}",
        }

    # Cloudflare Tool Handlers
    async def _cloudflare_deploy_worker(self, args: dict, context: dict) -> dict:
        """Deploy a Cloudflare Worker"""
        from integrations.cloudflare_integration import cloudflare

        result = await cloudflare.deploy_worker(
            script_name=args["script_name"],
            script_content=args["script_content"],
            bindings=args.get("bindings"),
        )
        if not result.success:
            raise ValueError(result.error)
        return result.data

    async def _cloudflare_kv_write(self, args: dict, context: dict) -> dict:
        """Write to Cloudflare KV"""
        from integrations.cloudflare_integration import cloudflare

        result = await cloudflare.kv_write(
            namespace_id=args["namespace_id"], key=args["key"], value=args["value"]
        )
        if not result.success:
            raise ValueError(result.error)
        return result.data

    async def _cloudflare_kv_read(self, args: dict, context: dict) -> dict:
        """Read from Cloudflare KV"""
        from integrations.cloudflare_integration import cloudflare

        result = await cloudflare.kv_read(namespace_id=args["namespace_id"], key=args["key"])
        if not result.success:
            raise ValueError(result.error)
        return {"key": args["key"], "value": result.data}

    # Vercel Tool Handlers
    async def _vercel_deploy(self, args: dict, context: dict) -> dict:
        """Deploy to Vercel"""
        from integrations.vercel_integration import vercel

        result = await vercel.create_deployment(
            project_name=args["project_name"], files=args["files"], env_vars=args.get("env_vars")
        )
        if not result.success:
            raise ValueError(result.error)
        return result.data

    async def _vercel_list_deployments(self, args: dict, context: dict) -> dict:
        """List Vercel deployments"""
        from integrations.vercel_integration import vercel

        result = await vercel.list_deployments(
            project_id=args.get("project_id"), limit=args.get("limit", 20)
        )
        if not result.success:
            raise ValueError(result.error)
        return {"deployments": result.data}

    # Stripe Tool Handlers
    async def _stripe_create_customer(self, args: dict, context: dict) -> dict:
        """Create Stripe customer"""
        from integrations.stripe_integration import stripe

        result = await stripe.create_customer(email=args["email"], name=args.get("name"))
        if not result.success:
            raise ValueError(result.error)
        return result.data

    async def _stripe_create_payment_intent(self, args: dict, context: dict) -> dict:
        """Create Stripe payment intent"""
        from integrations.stripe_integration import stripe

        result = await stripe.create_payment_intent(
            amount=args["amount"],
            currency=args.get("currency", "usd"),
            customer_id=args.get("customer_id"),
        )
        if not result.success:
            raise ValueError(result.error)
        return result.data

    # Perplexity Tool Handlers
    async def _perplexity_search(self, args: dict, context: dict) -> dict:
        """Search with Perplexity AI"""
        from integrations.perplexity_integration import perplexity

        result = await perplexity.search(
            query=args["query"], max_tokens=args.get("max_tokens", 4096)
        )
        if not result.success:
            raise ValueError(result.error)
        return result.data

    # Coinbase Commerce Tool Handlers
    async def _coinbase_create_charge(self, args: dict, context: dict) -> dict:
        """Create Coinbase Commerce charge"""
        from integrations.coinbase_commerce_integration import coinbase_commerce

        result = await coinbase_commerce.create_charge(
            name=args["name"],
            description=args["description"],
            amount=args["amount"],
            currency=args.get("currency", "USD"),
        )
        if not result.success:
            raise ValueError(result.error)
        return result.data

    # Base L2 Tool Handlers
    async def _base_get_balance(self, args: dict, context: dict) -> dict:
        """Get Base L2 balance"""
        from integrations.base_l2_integration import base_l2

        result = await base_l2.get_balance(address=args.get("address"))
        if not result.success:
            raise ValueError(result.error)
        return result.data

    async def _base_send_transaction(self, args: dict, context: dict) -> dict:
        """Send Base L2 transaction"""
        from integrations.base_l2_integration import base_l2

        result = await base_l2.send_transaction(
            to_address=args["to_address"], amount_eth=args["amount_eth"]
        )
        if not result.success:
            raise ValueError(result.error)
        return result.data

    # DraftKings Tool Handlers
    async def _draftkings_get_odds(self, args: dict, context: dict) -> dict:
        """Get DraftKings odds"""
        from integrations.draftkings_integration import draftkings

        result = await draftkings.get_odds(
            sport=args.get("sport", "BASKETBALL"), league=args.get("league", "NBA")
        )
        if not result.success:
            raise ValueError(result.error)
        return result.data

    # PrizePicks Tool Handlers
    async def _prizepicks_get_projections(self, args: dict, context: dict) -> dict:
        """Get PrizePicks projections"""
        from integrations.prizepicks_integration import prizepicks

        result = await prizepicks.get_projections(
            league=args.get("league"), per_page=args.get("per_page", 100)
        )
        if not result.success:
            raise ValueError(result.error)
        return result.data

    # Google Cloud Tool Handlers
    async def _gcs_upload_file(self, args: dict, context: dict) -> dict:
        """Upload file to Google Cloud Storage"""
        from integrations.google_cloud_integration import google_cloud

        result = await google_cloud.storage_upload_file(
            bucket_name=args["bucket_name"],
            source_file_path=args["source_file_path"],
            destination_blob_name=args["destination_blob_name"],
        )
        if not result.success:
            raise ValueError(result.error)
        return result.data

    async def _bigquery_query(self, args: dict, context: dict) -> dict:
        """Execute BigQuery query"""
        from integrations.google_cloud_integration import google_cloud

        result = await google_cloud.bigquery_query(query=args["query"])
        if not result.success:
            raise ValueError(result.error)
        return result.data


# Global MCP instance
mcp = MCPIntegration()
