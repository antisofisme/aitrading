#!/bin/bash

# Install MCP Auto-Restart as Systemd Service
# This creates a system service that automatically monitors and restarts MCP servers

SERVICE_NAME="mcp-monitor"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
SCRIPT_PATH="/mnt/f/WINDSURF/neliti_code/scripts/mcp-control.py"
USER=$(whoami)

echo "🚀 Installing MCP Auto-Restart Service..."

# Create systemd service file
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=MCP Server Auto-Restart Monitor
Documentation=https://github.com/neliti-ai/mcp-monitor
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=/mnt/f/WINDSURF/neliti_code
ExecStart=/usr/bin/python3 $SCRIPT_PATH daemon
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StartLimitBurst=5
StartLimitInterval=60

# Resource limits
MemoryMax=256M
CPUQuota=10%

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=false
ReadWritePaths=/mnt/f/WINDSURF/neliti_code
ReadWritePaths=/tmp

# Environment
Environment=PYTHONPATH=/mnt/f/WINDSURF/neliti_code
Environment=HOME=/home/$USER

[Install]
WantedBy=multi-user.target
EOF

# Set proper permissions
sudo chmod 644 "$SERVICE_FILE"

# Reload systemd and enable service
echo "📋 Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "✅ Enabling MCP monitor service..."
sudo systemctl enable "$SERVICE_NAME"

echo "🚀 Starting MCP monitor service..."
sudo systemctl start "$SERVICE_NAME"

# Check service status
echo ""
echo "=== Service Status ==="
sudo systemctl status "$SERVICE_NAME" --no-pager -l

echo ""
echo "=== Service Commands ==="
echo "• Check status:  sudo systemctl status $SERVICE_NAME"
echo "• Start:         sudo systemctl start $SERVICE_NAME"
echo "• Stop:          sudo systemctl stop $SERVICE_NAME"
echo "• Restart:       sudo systemctl restart $SERVICE_NAME"
echo "• View logs:     sudo journalctl -u $SERVICE_NAME -f"
echo "• Disable:       sudo systemctl disable $SERVICE_NAME"

echo ""
echo "✅ MCP Auto-Restart Service installed successfully!"
echo "📊 The service will now automatically monitor and restart your MCP servers."