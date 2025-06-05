#!/usr/bin/env python3
"""
Test script that simulates exactly what Cursor does when connecting to MCP server.
Run this and check the output to see what Cursor should see.
"""

import asyncio
import json
import sys
import subprocess
from pathlib import Path

def create_cursor_config():
    """Create a sample Cursor configuration."""
    config = {
        "mcpServers": {
            "dexscreener": {
                "command": sys.executable,
                "args": ["-m", "dexscreener_mcp.server"],
                "env": {}
            }
        }
    }
    
    # Write to a test file
    config_file = Path("cursor_config_test.json")
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"📁 Created test config: {config_file.absolute()}")
    print(f"📋 Config content:\n{json.dumps(config, indent=2)}")
    return config

async def test_mcp_handshake():
    """Test the full MCP handshake that Cursor would perform."""
    print("\n🤝 Testing MCP handshake (what Cursor does)...")
    
    # Start the server process
    cmd = [sys.executable, "-m", "dexscreener_mcp.server"]
    print(f"🚀 Starting: {' '.join(cmd)}")
    
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0  # Unbuffered
    )
    
    try:
        # Step 1: Initialize
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
                    "name": "cursor",
                    "version": "0.42.0"
                }
            }
        }
        
        print("📤 Sending initialize request...")
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Wait for response
        await asyncio.sleep(1)
        
        # Step 2: List tools
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2, 
            "method": "tools/list",
            "params": {}
        }
        
        print("📤 Sending tools/list request...")
        process.stdin.write(json.dumps(tools_request) + "\n")
        process.stdin.flush()
        
        # Wait for response
        await asyncio.sleep(1)
        
        # Step 3: Check what we got back
        print("📥 Reading responses...")
        
        # Read whatever is available
        process.stdin.close()
        stdout, stderr = process.communicate(timeout=5)
        
        print(f"📄 STDOUT:\n{stdout}")
        if stderr:
            print(f"⚠️  STDERR:\n{stderr}")
            
        # Parse responses
        if stdout.strip():
            for line in stdout.strip().split('\n'):
                if line.strip():
                    try:
                        response = json.loads(line)
                        print(f"✅ Parsed response: {json.dumps(response, indent=2)}")
                        
                        # Check if this is tools list response
                        if response.get('id') == 2 and 'result' in response:
                            tools = response['result'].get('tools', [])
                            print(f"🛠️  Found {len(tools)} tools in response!")
                            for tool in tools:
                                print(f"   - {tool.get('name', 'unnamed')}")
                                
                    except json.JSONDecodeError as e:
                        print(f"❌ Failed to parse line: {line}")
                        print(f"   Error: {e}")
        else:
            print("❌ No stdout received")
            
    except subprocess.TimeoutExpired:
        print("⏰ Process timed out")
        process.kill()
    except Exception as e:
        print(f"❌ Error during handshake: {e}")
        process.kill()
    
    return process.returncode == 0

def check_cursor_installation():
    """Check if Cursor is installed and where."""
    print("\n🔍 Checking Cursor installation...")
    
    possible_paths = [
        "cursor",
        "/Applications/Cursor.app/Contents/MacOS/Cursor",
        r"C:\Users\{}\AppData\Local\Programs\cursor\Cursor.exe".format(Path.home().name),
        "/usr/bin/cursor"
    ]
    
    cursor_found = False
    for path in possible_paths:
        try:
            result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ Found Cursor at: {path}")
                print(f"   Version: {result.stdout.strip()}")
                cursor_found = True
                break
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            continue
    
    if not cursor_found:
        print("❌ Cursor not found in common locations")
    
    return cursor_found

def check_mcp_support():
    """Check if MCP support is available."""
    print("\n🔌 Checking MCP support...")
    
    try:
        import mcp
        print(f"✅ MCP library version: {getattr(mcp, '__version__', 'unknown')}")
        
        # Check if we have all needed components
        from mcp.server import Server, NotificationOptions
        from mcp.server.stdio import stdio_server
        from mcp.types import Tool, CallToolRequest, ListToolsRequest
        print("✅ All MCP components available")
        
        return True
    except ImportError as e:
        print(f"❌ MCP import error: {e}")
        return False

async def main():
    """Main test function."""
    print("🧪 Cursor MCP Integration Test")
    print("=" * 50)
    
    # Test 1: Create config
    config = create_cursor_config()
    
    # Test 2: Check installations
    cursor_found = check_cursor_installation()
    mcp_ok = check_mcp_support()
    
    # Test 3: Test handshake
    handshake_ok = await test_mcp_handshake()
    
    print("\n🎯 Test Results:")
    print(f"   Cursor found: {'✅' if cursor_found else '❌'}")
    print(f"   MCP support: {'✅' if mcp_ok else '❌'}")
    print(f"   MCP handshake: {'✅' if handshake_ok else '❌'}")
    
    print("\n💡 Recommendations:")
    if not cursor_found:
        print("   - Install Cursor from https://cursor.sh")
    
    if not mcp_ok:
        print("   - Reinstall MCP: pip install mcp")
    
    if not handshake_ok:
        print("   - Check server logs above for errors")
        print("   - Verify Python path in Cursor config")
    
    if cursor_found and mcp_ok and handshake_ok:
        print("   ✅ Everything looks good!")
        print("   - Use the config from cursor_config_test.json")
        print("   - Make sure to restart Cursor after config changes")
        print("   - Check Cursor's output panel for MCP logs")

if __name__ == "__main__":
    asyncio.run(main())