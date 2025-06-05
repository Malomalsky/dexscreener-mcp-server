#!/usr/bin/env python3
"""
Simple MCP client to test our DexScreener server.
"""

import asyncio
import json
import subprocess
import sys
from typing import Any, Dict

class SimpleMCPClient:
    """A simple MCP client for testing."""
    
    def __init__(self, server_command: list):
        self.server_command = server_command
        self.process = None
        self.request_id = 0
    
    async def start_server(self):
        """Start the MCP server process."""
        print(f"🚀 Starting server: {' '.join(self.server_command)}")
        self.process = await asyncio.create_subprocess_exec(
            *self.server_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        print("✅ Server process started")
    
    async def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a JSON-RPC request to the server."""
        if not self.process:
            raise RuntimeError("Server not started")
        
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        request_line = json.dumps(request) + "\n"
        print(f"📤 Sending: {request}")
        
        self.process.stdin.write(request_line.encode())
        await self.process.stdin.drain()
        
        # Read response
        response_line = await self.process.stdout.readline()
        if not response_line:
            raise RuntimeError("No response from server")
        
        response = json.loads(response_line.decode().strip())
        print(f"📥 Received: {response}")
        
        return response
    
    async def stop_server(self):
        """Stop the server process."""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            print("🛑 Server stopped")

async def test_dexscreener_mcp():
    """Test the DexScreener MCP server."""
    print("🧪 Testing DexScreener MCP Server")
    print("=" * 50)
    
    # Create client
    client = SimpleMCPClient([sys.executable, "-m", "dexscreener_mcp.server"])
    
    try:
        # Start server
        await client.start_server()
        
        # Wait a bit for server to initialize
        await asyncio.sleep(1)
        
        # Step 1: Initialize
        print("\n📋 Step 1: Initialize connection")
        init_response = await client.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        })
        
        if "result" in init_response:
            print("✅ Initialization successful")
            capabilities = init_response["result"]["capabilities"]
            print(f"🔧 Server capabilities: {capabilities}")
        else:
            print(f"❌ Initialization failed: {init_response}")
            return False
        
        # Step 2: List tools
        print("\n🛠️  Step 2: List available tools")
        tools_response = await client.send_request("tools/list")
        
        if "result" in tools_response:
            tools = tools_response["result"]["tools"]
            print(f"✅ Found {len(tools)} tools:")
            for i, tool in enumerate(tools, 1):
                print(f"   {i}. {tool['name']}: {tool['description']}")
            
            if len(tools) == 7:
                print("🎯 All 7 expected tools found!")
                return True
            else:
                print(f"⚠️  Expected 7 tools, got {len(tools)}")
                return False
        else:
            print(f"❌ Failed to list tools: {tools_response}")
            return False
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    finally:
        await client.stop_server()

async def test_tool_call():
    """Test calling a specific tool."""
    print("\n🔧 Testing tool call...")
    
    client = SimpleMCPClient([sys.executable, "-m", "dexscreener_mcp.server"])
    
    try:
        await client.start_server()
        await asyncio.sleep(1)
        
        # Initialize
        await client.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        })
        
        # Call get_supported_chains (simple tool)
        print("🌐 Calling get_supported_chains...")
        call_response = await client.send_request("tools/call", {
            "name": "get_supported_chains",
            "arguments": {}
        })
        
        if "result" in call_response:
            result = call_response["result"]
            print("✅ Tool call successful!")
            print(f"📊 Result: {json.dumps(result, indent=2)[:200]}...")
            return True
        else:
            print(f"❌ Tool call failed: {call_response}")
            return False
    
    except Exception as e:
        print(f"❌ Tool call test failed: {e}")
        return False
    
    finally:
        await client.stop_server()

async def main():
    """Run all tests."""
    print("🎯 DexScreener MCP Server Test Suite")
    print("=" * 60)
    
    # Test 1: Basic MCP protocol
    success1 = await test_dexscreener_mcp()
    
    # Test 2: Tool calling
    success2 = await test_tool_call()
    
    print("\n🎯 Test Results:")
    print(f"   MCP Protocol: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"   Tool Calling: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print("\n🎉 All tests passed! The MCP server is working perfectly.")
        print("   The issue with Cursor is definitely in the configuration.")
    else:
        print("\n❌ Some tests failed. There may be issues with the server.")

if __name__ == "__main__":
    asyncio.run(main())