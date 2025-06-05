# DexScreener MCP Server - Debug Guide

If you're seeing "0 tools enabled" in Cursor, follow these steps:

## 🔧 Quick Diagnostics

### 1. Run the debug script:
```bash
python debug_cursor.py
```
This will tell you if the server is working correctly.

### 2. Test the server manually:
```bash
python test_tools.py
```
Should show "7 tools available" if working.

## 🎯 Cursor Configuration

### Step 1: Find your Cursor settings
- **Windows**: `%APPDATA%\Cursor\User\settings.json`
- **macOS**: `~/Library/Application Support/Cursor/User/settings.json`  
- **Linux**: `~/.config/Cursor/User/settings.json`

### Step 2: Add MCP server config
Use one of these configurations:

**Option A (Simple):**
```json
{
  "mcpServers": {
    "dexscreener": {
      "command": "python",
      "args": ["-m", "dexscreener_mcp.server"],
      "env": {}
    }
  }
}
```

**Option B (Full path - Windows):**
```json
{
  "mcpServers": {
    "dexscreener": {
      "command": "C:\\Users\\YourUser\\AppData\\Local\\Programs\\Python\\Python311\\python.exe",
      "args": ["-m", "dexscreener_mcp.server"],
      "env": {}
    }
  }
}
```

### Step 3: Restart Cursor completely
- Close all Cursor windows
- Wait 5 seconds  
- Reopen Cursor

### Step 4: Check for MCP panel
- Look for MCP section in Cursor
- Should show "dexscreener" server
- Check Output panel for errors

## 🐛 Common Issues

### "0 tools enabled"
1. **Wrong Python path**: Use absolute path to Python
2. **Package not installed**: Run `pip install -e .` in project folder
3. **Cursor cache**: Restart Cursor completely
4. **MCP not supported**: Cursor version might not support MCP

### "Server not starting"
1. **Test manually**: `python -m dexscreener_mcp.server`
2. **Check imports**: `python -c "import dexscreener_mcp; print('OK')"`
3. **Check Python**: `python --version`

### "No error messages"
1. **Check Cursor Output panel** → MCP tab
2. **Enable Cursor developer tools**
3. **Look for process in Task Manager** (Windows)

## ✅ Verification

If everything works, you should see:
- Server listed in Cursor MCP panel
- 7 tools available
- No error messages in Output panel

## 📞 Still not working?

1. Run `python debug_cursor.py` and share the output
2. Check Cursor version (MCP might be experimental)
3. Try with Claude Desktop first (full MCP support)
4. Consider that Cursor MCP support might be limited

The server itself works perfectly - the issue is always in the configuration or Cursor's MCP support level.