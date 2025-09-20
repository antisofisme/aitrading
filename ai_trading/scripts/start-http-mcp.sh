#!/bin/bash

# Start Neliti HTTP REST API MCP Server
cd /mnt/f/WINDSURF/neliti_code/server_side

export REST_BASE_URL=http://localhost:8000
export REST_TIMEOUT=30000
export REST_VERIFY_SSL=false

echo "🚀 Starting Neliti HTTP MCP Server..."
dkmaker-mcp-rest-api