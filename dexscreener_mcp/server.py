"""
DexScreener MCP Server implementation with comprehensive tools and error handling.
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional, Sequence

import structlog
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    TextContent,
    Tool,
)
from pydantic import ValidationError

from .client import DexScreenerAPIError, DexScreenerClient
from .types import ChainId

logger = structlog.get_logger(__name__)


class DexScreenerMCPServer:
    """
    Beautiful MCP server for DexScreener API with comprehensive tools,
    error handling, and best practices implementation.
    """
    
    def __init__(self):
        self.client: Optional[DexScreenerClient] = None
        self.server = Server("dexscreener-mcp-server")
        self._setup_handlers()
        
        logger.info("DexScreener MCP Server initialized")
    
    def _setup_handlers(self):
        """Set up MCP server handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available DexScreener tools."""
            return [
                Tool(
                    name="get_token_info",
                    description="Get comprehensive token information and trading pairs",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "token_address": {
                                "type": "string",
                                "description": "Token contract address (e.g., 0x...)",
                            }
                        },
                        "required": ["token_address"],
                    },
                ),
                Tool(
                    name="get_pair_info",
                    description="Get detailed trading pair information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "chain_id": {
                                "type": "string",
                                "description": "Blockchain identifier (e.g., ethereum, bsc, polygon)",
                            },
                            "pair_address": {
                                "type": "string",
                                "description": "Trading pair contract address",
                            },
                        },
                        "required": ["chain_id", "pair_address"],
                    },
                ),
                Tool(
                    name="search_tokens",
                    description="Search for tokens and trading pairs by name, symbol, or address",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query (token name, symbol, or address)",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results (optional, default: 20)",
                                "minimum": 1,
                                "maximum": 100,
                            },
                        },
                        "required": ["query"],
                    },
                ),
                Tool(
                    name="get_trending_pairs",
                    description="Get trending/popular trading pairs, optionally filtered by blockchain",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "chain_id": {
                                "type": "string",
                                "description": "Optional blockchain identifier to filter by",
                            }
                        },
                        "required": [],
                    },
                ),
                Tool(
                    name="get_multiple_pairs",
                    description="Get information for multiple trading pairs in a batch request",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pair_addresses": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of pair addresses in format 'chain:address'",
                                "minItems": 1,
                                "maxItems": 30,
                            }
                        },
                        "required": ["pair_addresses"],
                    },
                ),
                Tool(
                    name="get_supported_chains",
                    description="Get list of supported blockchain networks",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                ),
                Tool(
                    name="get_rate_limit_info",
                    description="Get current API rate limit status and information",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                ),
            ]
        
        @self.server.call_tool()
        async def call_tool(request: CallToolRequest) -> CallToolResult:
            """Handle tool calls with comprehensive error handling."""
            
            if not self.client:
                self.client = DexScreenerClient()
            
            try:
                tool_name = request.params.name
                arguments = request.params.arguments or {}
                
                logger.info("Tool called", tool=tool_name, args=arguments)
                
                # Route to appropriate tool handler
                if tool_name == "get_token_info":
                    result = await self._get_token_info(arguments)
                elif tool_name == "get_pair_info":
                    result = await self._get_pair_info(arguments)
                elif tool_name == "search_tokens":
                    result = await self._search_tokens(arguments)
                elif tool_name == "get_trending_pairs":
                    result = await self._get_trending_pairs(arguments)
                elif tool_name == "get_multiple_pairs":
                    result = await self._get_multiple_pairs(arguments)
                elif tool_name == "get_supported_chains":
                    result = await self._get_supported_chains(arguments)
                elif tool_name == "get_rate_limit_info":
                    result = await self._get_rate_limit_info(arguments)
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")
                
                logger.info("Tool completed successfully", tool=tool_name)
                
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=json.dumps(result, indent=2, default=str),
                        )
                    ]
                )
                
            except DexScreenerAPIError as e:
                error_msg = f"DexScreener API Error: {e.message}"
                if e.status_code:
                    error_msg += f" (Status: {e.status_code})"
                
                logger.error("API error", tool=tool_name, error=error_msg)
                
                return CallToolResult(
                    content=[TextContent(type="text", text=error_msg)],
                    isError=True,
                )
                
            except ValidationError as e:
                error_msg = f"Validation Error: {str(e)}"
                logger.error("Validation error", tool=tool_name, error=error_msg)
                
                return CallToolResult(
                    content=[TextContent(type="text", text=error_msg)],
                    isError=True,
                )
                
            except Exception as e:
                error_msg = f"Unexpected Error: {str(e)}"
                logger.error("Unexpected error", tool=tool_name, error=error_msg, exc_info=True)
                
                return CallToolResult(
                    content=[TextContent(type="text", text=error_msg)],
                    isError=True,
                )
    
    async def _get_token_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get token information."""
        token_address = args["token_address"]
        
        if not token_address:
            raise ValueError("token_address is required")
        
        response = await self.client.get_token_info(token_address)
        return response.dict()
    
    async def _get_pair_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get pair information."""
        chain_id = args["chain_id"]
        pair_address = args["pair_address"]
        
        if not chain_id or not pair_address:
            raise ValueError("chain_id and pair_address are required")
        
        response = await self.client.get_pair_info(chain_id, pair_address)
        return response.dict()
    
    async def _search_tokens(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search for tokens."""
        query = args["query"]
        limit = args.get("limit")
        
        if not query:
            raise ValueError("query is required")
        
        response = await self.client.search(query, limit)
        return response.dict()
    
    async def _get_trending_pairs(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get trending pairs."""
        chain_id = args.get("chain_id")
        
        response = await self.client.get_trending_pairs(chain_id)
        return response.dict()
    
    async def _get_multiple_pairs(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get multiple pairs information."""
        pair_addresses = args["pair_addresses"]
        
        if not pair_addresses:
            raise ValueError("pair_addresses is required")
        
        pairs = await self.client.get_multiple_pairs(pair_addresses)
        return {"pairs": [pair.dict() for pair in pairs]}
    
    async def _get_supported_chains(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get supported blockchain networks."""
        chains = [
            {
                "id": "ethereum",
                "name": "Ethereum",
                "native_currency": "ETH",
                "explorer": "https://etherscan.io",
            },
            {
                "id": "bsc",
                "name": "BNB Smart Chain",
                "native_currency": "BNB",
                "explorer": "https://bscscan.com",
            },
            {
                "id": "polygon",
                "name": "Polygon",
                "native_currency": "MATIC",
                "explorer": "https://polygonscan.com",
            },
            {
                "id": "avalanche",
                "name": "Avalanche",
                "native_currency": "AVAX",
                "explorer": "https://snowtrace.io",
            },
            {
                "id": "arbitrum",
                "name": "Arbitrum One",
                "native_currency": "ETH",
                "explorer": "https://arbiscan.io",
            },
            {
                "id": "optimism",
                "name": "Optimism",
                "native_currency": "ETH",
                "explorer": "https://optimistic.etherscan.io",
            },
            {
                "id": "base",
                "name": "Base",
                "native_currency": "ETH",
                "explorer": "https://basescan.org",
            },
            {
                "id": "fantom",
                "name": "Fantom",
                "native_currency": "FTM",
                "explorer": "https://ftmscan.com",
            },
        ]
        
        return {"supported_chains": chains}
    
    async def _get_rate_limit_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get rate limit information."""
        rate_limit = self.client.get_rate_limit_info()
        return rate_limit.dict()
    
    async def run(self):
        """Run the MCP server."""
        try:
            # Configure structured logging
            structlog.configure(
                processors=[
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.processors.add_log_level,
                    structlog.processors.JSONRenderer(),
                ],
                logger_factory=structlog.WriteLoggerFactory(),
                wrapper_class=structlog.BoundLogger,
                cache_logger_on_first_use=True,
            )
            
            logger.info("Starting DexScreener MCP Server")
            
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="dexscreener-mcp-server",
                        server_version="1.0.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={},
                        ),
                    ),
                )
        except Exception as e:
            logger.error("Server error", error=str(e), exc_info=True)
            raise
        finally:
            if self.client:
                await self.client.close()
            logger.info("DexScreener MCP Server stopped")


async def async_main():
    """Async main entry point for the MCP server."""
    server = DexScreenerMCPServer()
    await server.run()


def main():
    """Synchronous entry point for the MCP server (used by CLI)."""
    try:
        print("🚀 Starting DexScreener MCP Server...")
        print("💡 This server is designed to run within MCP-enabled applications")
        print("   like Claude Desktop, Cursor, Zed, etc.")
        print("   It will wait for MCP protocol messages on stdio.")
        print()
        print("⏳ Waiting for MCP client connection...")
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\n👋 Server interrupted by user")
        logger.info("Server interrupted by user")
    except EOFError:
        print("\n💡 No MCP client connected - this is normal when running standalone")
        print("   Use this server through Claude Desktop, Cursor, or other MCP clients")
    except Exception as e:
        error_msg = str(e)
        if "stdin" in error_msg.lower() or "stdio" in error_msg.lower():
            print(f"\n💡 Server stopped (MCP client disconnected)")
            print("   This is normal - the server runs when MCP clients connect")
        else:
            print(f"❌ Server failed to start: {e}")
            logger.error("Server failed to start", error=str(e))
            raise


if __name__ == "__main__":
    main()