#!/bin/bash

# Start Neliti WebSocket MCP Server
cd /mnt/f/WINDSURF/neliti_code/server_side
export PYTHONPATH=/mnt/f/WINDSURF/neliti_code/server_side

echo "🚀 Starting Neliti WebSocket MCP Server..."
python3 websocket-mcp-server.py