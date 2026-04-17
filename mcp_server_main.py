"""
MCP Server Entry Point
Run this module to start Big Homie as an MCP server
"""

import asyncio
import sys

from loguru import logger

from mcp_server import mcp_server


def main():
    """Main entry point for MCP server mode"""
    logger.info("Starting Big Homie MCP Server")
    logger.info("Use this with Claude Desktop, Cursor, or VS Code")

    try:
        asyncio.run(mcp_server.start_stdio_server())
    except KeyboardInterrupt:
        logger.info("MCP server stopped by user")
    except Exception as e:
        logger.error(f"MCP server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
