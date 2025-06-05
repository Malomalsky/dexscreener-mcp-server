#!/usr/bin/env python3
"""
Simple test that demonstrates MCP stdio protocol working correctly.
This shows what should happen when Cursor connects.
"""

import json
import sys

def simulate_mcp_client():
    """Simulate what an MCP client like Cursor sends."""
    
    # Initialize request
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    # Tools list request
    tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    print("📤 MCP Client would send:")
    print(json.dumps(init_request))
    print(json.dumps(tools_request))
    
    return [init_request, tools_request]

def main():
    """Main function."""
    print("🧪 MCP STDIO Protocol Test")
    print("=" * 40)
    
    print("\n1. What MCP client (Cursor) sends:")
    requests = simulate_mcp_client()
    
    print("\n2. Test server manually:")
    print("   Run this command:")
    print(f"   {sys.executable} -m dexscreener_mcp.server")
    print("\n   Then paste these lines one by one:")
    for req in requests:
        print(f"   {json.dumps(req)}")
    
    print("\n3. Expected server response:")
    print("   Should see JSON responses with:")
    print("   - Initialize response with server capabilities")
    print("   - Tools list with 7 tools")
    
    print("\n4. If this works, the issue is in Cursor configuration")
    print("   If this doesn't work, there's a server problem")
    
    print("\n💡 Generated Cursor config file:")
    
    # For Windows (where you're running)
    if sys.platform == "win32":
        python_path = sys.executable.replace("\\", "/")  # Use forward slashes
    else:
        python_path = sys.executable
    
    cursor_config = {
        "mcpServers": {
            "dexscreener": {
                "command": python_path,
                "args": ["-m", "dexscreener_mcp.server"],
                "env": {}
            }
        }
    }
    
    with open("cursor_settings.json", "w") as f:
        json.dump(cursor_config, f, indent=2)
    
    print(f"   Saved to: cursor_settings.json")
    print(f"   Content: {json.dumps(cursor_config, indent=2)}")
    
    print(f"\n📁 Copy this to your Cursor settings:")
    if sys.platform == "win32":
        settings_path = "%APPDATA%\\Cursor\\User\\settings.json"
    elif sys.platform == "darwin": 
        settings_path = "~/Library/Application Support/Cursor/User/settings.json"
    else:
        settings_path = "~/.config/Cursor/User/settings.json"
    
    print(f"   {settings_path}")

if __name__ == "__main__":
    main()