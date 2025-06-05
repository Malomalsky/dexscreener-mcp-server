#!/usr/bin/env python3
"""
Simple test script to verify MCP server tools registration.
"""

import asyncio
from dexscreener_mcp.server import DexScreenerMCPServer

async def test_tools():
    """Test that tools are properly registered."""
    print("🧪 Testing DexScreener MCP Server tools...")
    
    # Create server instance
    server = DexScreenerMCPServer()
    print("✅ Server created successfully")
    
    # Check request handlers
    if hasattr(server.server, 'request_handlers'):
        handlers = server.server.request_handlers
        print(f"📋 Found {len(handlers)} request handlers")
        print(f"Handler keys: {list(handlers.keys())}")
        
        # Look for ListToolsRequest handler
        from mcp.types import ListToolsRequest
        if ListToolsRequest in handlers:
            list_tools_handler = handlers[ListToolsRequest]
            print("✅ ListToolsRequest handler found")
            
            # Create a mock request to test
            request = ListToolsRequest(method="tools/list")
            
            try:
                # Call the handler
                result = await list_tools_handler(request)
                if hasattr(result, 'root') and hasattr(result.root, 'tools'):
                    tools = result.root.tools
                    print(f"🛠️  Found {len(tools)} tools:")
                    
                    for i, tool in enumerate(tools, 1):
                        print(f"   {i}. {tool.name}: {tool.description}")
                    
                    return len(tools)
                else:
                    print(f"❌ Unexpected result type: {type(result)}")
                    print(f"Result: {result}")
            except Exception as e:
                print(f"❌ Error calling handler: {e}")
        else:
            print("❌ ListToolsRequest handler not found")
            print(f"Available handlers: {list(handlers.keys())}")
    else:
        print("❌ No request_handlers found on server")
    
    return 0

if __name__ == "__main__":
    count = asyncio.run(test_tools())
    print(f"\n🎯 Result: {count} tools available")
    if count > 0:
        print("✅ Server should work correctly with MCP clients")
    else:
        print("❌ Problem with tools registration")