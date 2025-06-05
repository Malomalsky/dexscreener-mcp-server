#!/usr/bin/env python3
"""
Debug script to test MCP server with Cursor-like input simulation.
"""

import asyncio
import json
import sys
from io import StringIO
from dexscreener_mcp.server import DexScreenerMCPServer

async def test_mcp_protocol():
    """Test MCP protocol communication like Cursor would do."""
    print("🔍 Testing MCP protocol communication...")
    
    # Create server
    server = DexScreenerMCPServer()
    print("✅ Server created")
    
    # Test 1: Check if tools are registered
    from mcp.types import ListToolsRequest
    handlers = server.server.request_handlers
    
    if ListToolsRequest in handlers:
        print("✅ ListToolsRequest handler found")
        
        # Simulate MCP client request
        request = ListToolsRequest(method="tools/list")
        result = await handlers[ListToolsRequest](request)
        
        if hasattr(result, 'root') and hasattr(result.root, 'tools'):
            tools = result.root.tools
            print(f"🛠️  Server reports {len(tools)} tools:")
            for i, tool in enumerate(tools, 1):
                print(f"   {i}. {tool.name}")
        else:
            print("❌ Unexpected result structure")
            print(f"Result: {result}")
            return False
    else:
        print("❌ ListToolsRequest handler not found")
        return False
    
    # Test 2: Check server capabilities
    from mcp.server import NotificationOptions
    try:
        capabilities = server.server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={}
        )
        print(f"🔧 Server capabilities: {capabilities}")
        
        if hasattr(capabilities, 'tools') and capabilities.tools:
            print("✅ Tools capability enabled")
        else:
            print("❌ Tools capability not found or disabled")
            return False
            
    except Exception as e:
        print(f"❌ Error getting capabilities: {e}")
        return False
    
    # Test 3: Simulate stdio communication
    print("\n🔌 Testing stdio communication simulation...")
    
    # Create fake stdin with MCP initialization
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
                "name": "cursor-test",
                "version": "1.0.0"
            }
        }
    }
    
    tools_request = {
        "jsonrpc": "2.0", 
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    # Simulate what Cursor would send
    fake_input = json.dumps(init_request) + "\n" + json.dumps(tools_request) + "\n"
    print(f"📤 Simulated Cursor input:\n{fake_input}")
    
    return True

async def test_direct_execution():
    """Test what happens when we run the server directly."""
    print("\n🎯 Testing direct server execution...")
    
    # This simulates what happens when Cursor starts the server
    import subprocess
    import os
    
    # Test command that Cursor would run
    cmd = [sys.executable, "-m", "dexscreener_mcp.server"]
    print(f"🔧 Command that Cursor executes: {' '.join(cmd)}")
    
    # Check if command exists and is executable
    try:
        result = subprocess.run([sys.executable, "-c", "import dexscreener_mcp; print('Import OK')"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ Package import works")
        else:
            print(f"❌ Package import failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False
    
    # Test module execution
    try:
        # Run for 2 seconds then kill (simulates Cursor starting server)
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE, text=True)
        print("🚀 Server process started...")
        
        # Give it a moment to initialize
        await asyncio.sleep(1)
        
        if process.poll() is None:
            print("✅ Server is running and waiting for input")
            process.terminate()
            await asyncio.sleep(0.5)
            if process.poll() is None:
                process.kill()
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Server exited early")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Server execution test failed: {e}")
        return False
    
    return True

def print_cursor_debug_info():
    """Print debugging information for Cursor configuration."""
    print("\n📋 Cursor Configuration Debug Info:")
    print("=" * 50)
    
    print("1. Verify Python path:")
    print(f"   Python executable: {sys.executable}")
    print(f"   Python version: {sys.version}")
    
    print("\n2. Verify package installation:")
    try:
        import dexscreener_mcp
        print(f"   ✅ Package location: {dexscreener_mcp.__file__}")
        print(f"   ✅ Package version: {getattr(dexscreener_mcp, '__version__', 'unknown')}")
    except ImportError as e:
        print(f"   ❌ Package not found: {e}")
    
    print("\n3. Recommended Cursor configuration:")
    config = {
        "mcpServers": {
            "dexscreener": {
                "command": sys.executable,
                "args": ["-m", "dexscreener_mcp.server"],
                "env": {}
            }
        }
    }
    print(f"   {json.dumps(config, indent=2)}")
    
    print("\n4. Alternative Cursor configuration (if above fails):")
    import os
    python_path = sys.executable.replace('\\', '\\\\')  # Escape backslashes for JSON
    alt_config = {
        "mcpServers": {
            "dexscreener": {
                "command": python_path,
                "args": ["-m", "dexscreener_mcp.server"],
                "env": {},
                "cwd": os.getcwd()
            }
        }
    }
    print(f"   {json.dumps(alt_config, indent=2)}")
    
    print("\n5. Configuration file location:")
    if sys.platform == "win32":
        config_path = os.path.expandvars("%APPDATA%\\Cursor\\User\\settings.json")
    elif sys.platform == "darwin":
        config_path = os.path.expanduser("~/Library/Application Support/Cursor/User/settings.json")
    else:
        config_path = os.path.expanduser("~/.config/Cursor/User/settings.json")
    
    print(f"   {config_path}")
    
    print("\n6. Testing steps:")
    print("   1. Add configuration to settings.json")
    print("   2. Restart Cursor completely") 
    print("   3. Open a file and check MCP panel/status")
    print("   4. Look for 'dexscreener' in MCP servers list")
    print("   5. Check Cursor output panel for error messages")

async def main():
    """Main debugging function."""
    print("🧪 DexScreener MCP Server - Cursor Debug Tool")
    print("=" * 60)
    
    # Test 1: Protocol communication
    success1 = await test_mcp_protocol()
    
    # Test 2: Direct execution  
    success2 = await test_direct_execution()
    
    # Print debug info
    print_cursor_debug_info()
    
    print("\n🎯 Summary:")
    print(f"   MCP Protocol Test: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"   Direct Execution Test: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print("\n✅ Server is working correctly!")
        print("   The issue is likely in Cursor configuration or MCP support.")
        print("   Try the configurations shown above.")
    else:
        print("\n❌ Server has issues that need to be fixed first.")

if __name__ == "__main__":
    asyncio.run(main())