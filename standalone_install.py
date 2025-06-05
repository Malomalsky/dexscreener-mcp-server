#!/usr/bin/env python3
"""
Standalone installation script for DexScreener MCP Server.
This script installs the server with minimal dependencies to avoid conflicts.
"""

import subprocess
import sys
from pathlib import Path

def install_minimal():
    """Install with minimal dependencies to avoid conflicts."""
    
    # Minimal dependencies that shouldn't conflict
    minimal_deps = [
        "httpx>=0.25.0",
        "pydantic>=2.0.0,<3.0.0", 
        "asyncio-throttle>=1.0.0",
        "structlog>=23.0.0",
        "tenacity>=8.0.0",
        "python-dotenv>=1.0.0",
    ]
    
    print("🚀 Installing DexScreener MCP Server with minimal dependencies...")
    print("This avoids conflicts with FastAPI and other packages.")
    
    try:
        # Install minimal dependencies first
        for dep in minimal_deps:
            print(f"📦 Installing {dep}...")
            subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
        
        # Install the package in development mode
        print("📦 Installing dexscreener-mcp-server...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)
        
        print("✅ Installation completed successfully!")
        print("\n🎯 You can now use:")
        print("   python -m dexscreener_mcp.server")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    if not install_minimal():
        sys.exit(1)