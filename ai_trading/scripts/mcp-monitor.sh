#!/bin/bash

# MCP Server Auto-Restart Monitor
# Monitors and restarts the 3 main MCP servers if they stop running

LOG_FILE="/tmp/mcp-monitor.log"
RESTART_DELAY=5

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check if a process is running
is_process_running() {
    local process_name="$1"
    pgrep -f "$process_name" > /dev/null 2>&1
}

# Function to restart MCP server if not running
restart_mcp_server() {
    local server_name="$1"
    local start_command="$2"
    
    if ! is_process_running "$server_name"; then
        log_message "⚠️  $server_name not running, attempting restart..."
        
        # Kill any zombie processes
        pkill -f "$server_name" 2>/dev/null || true
        sleep 2
        
        # Start the server
        eval "$start_command" &
        sleep $RESTART_DELAY
        
        if is_process_running "$server_name"; then
            log_message "✅ $server_name restarted successfully"
        else
            log_message "❌ Failed to restart $server_name"
        fi
    else
        log_message "✅ $server_name is running"
    fi
}

# Main monitoring function
monitor_mcp_servers() {
    log_message "🔍 Starting MCP server monitoring..."
    
    # Monitor mcp-server-docker
    restart_mcp_server "mcp-server-docker" "uv tool uvx mcp-server-docker"
    
    # Monitor mcp-server-github  
    restart_mcp_server "mcp-server-github" "npx mcp-server-github"
    
    # Monitor mcp-server-filesystem
    restart_mcp_server "mcp-server-filesystem" "npx mcp-server-filesystem /mnt/f/WINDSURF/neliti_code"
    
    log_message "🔍 MCP monitoring cycle completed"
}

# Function to show current status
show_status() {
    echo "=== MCP Servers Status ==="
    echo "Docker MCP:     $(is_process_running 'mcp-server-docker' && echo '✅ Running' || echo '❌ Stopped')"
    echo "GitHub MCP:     $(is_process_running 'mcp-server-github' && echo '✅ Running' || echo '❌ Stopped')"
    echo "Filesystem MCP: $(is_process_running 'mcp-server-filesystem' && echo '✅ Running' || echo '❌ Stopped')"
    echo "===================="
}

# Function to install as systemd service
install_service() {
    cat > /tmp/mcp-monitor.service << EOF
[Unit]
Description=MCP Server Auto-Restart Monitor
After=network.target

[Service]
Type=simple
User=$(whoami)
ExecStart=/bin/bash /mnt/f/WINDSURF/neliti_code/scripts/mcp-monitor.sh daemon
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

    sudo mv /tmp/mcp-monitor.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable mcp-monitor.service
    echo "✅ MCP Monitor service installed and enabled"
}

# Parse command line arguments
case "${1:-status}" in
    "monitor")
        monitor_mcp_servers
        ;;
    "daemon")
        log_message "🚀 MCP Monitor daemon started"
        while true; do
            monitor_mcp_servers
            sleep 60  # Check every minute
        done
        ;;
    "status")
        show_status
        ;;
    "install")
        install_service
        ;;
    "start")
        log_message "🚀 Starting all MCP servers..."
        restart_mcp_server "mcp-server-docker" "uv tool uvx mcp-server-docker"
        restart_mcp_server "mcp-server-github" "npx mcp-server-github"  
        restart_mcp_server "mcp-server-filesystem" "npx mcp-server-filesystem /mnt/f/WINDSURF/neliti_code"
        show_status
        ;;
    "stop")
        log_message "🛑 Stopping all MCP servers..."
        pkill -f "mcp-server-docker" || true
        pkill -f "mcp-server-github" || true
        pkill -f "mcp-server-filesystem" || true
        show_status
        ;;
    "restart")
        log_message "🔄 Restarting all MCP servers..."
        $0 stop
        sleep 3
        $0 start
        ;;
    *)
        echo "Usage: $0 {status|monitor|daemon|start|stop|restart|install}"
        echo ""
        echo "Commands:"
        echo "  status   - Show current MCP server status"
        echo "  monitor  - Run one monitoring cycle"
        echo "  daemon   - Run continuous monitoring"
        echo "  start    - Start all MCP servers"
        echo "  stop     - Stop all MCP servers"
        echo "  restart  - Restart all MCP servers"
        echo "  install  - Install as systemd service"
        ;;
esac