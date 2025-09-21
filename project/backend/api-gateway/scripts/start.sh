#!/bin/bash

# API Gateway Startup Script
# Ensures the service starts with proper environment and error handling

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting AI Trading Platform API Gateway...${NC}"

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed or not in PATH${NC}"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node --version)
echo -e "${GREEN}📦 Node.js version: ${NODE_VERSION}${NC}"

# Change to API Gateway directory
cd "$(dirname "$0")/.."

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ package.json not found in current directory${NC}"
    exit 1
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"
    npm install --force
fi

# Check if .env file exists, create from example if not
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}📋 Creating .env from .env.example${NC}"
        cp .env.example .env
    else
        echo -e "${YELLOW}⚠️  No .env file found, using defaults${NC}"
    fi
fi

# Health check function
health_check() {
    local max_attempts=30
    local attempt=1

    echo -e "${YELLOW}🏥 Performing health check...${NC}"

    while [ $attempt -le $max_attempts ]; do
        if curl -s -f http://localhost:3001/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ API Gateway is healthy!${NC}"
            return 0
        fi

        echo "Attempt $attempt/$max_attempts - waiting for server..."
        sleep 2
        attempt=$((attempt + 1))
    done

    echo -e "${RED}❌ Health check failed after $max_attempts attempts${NC}"
    return 1
}

# Function to start the server
start_server() {
    echo -e "${GREEN}🚀 Starting API Gateway server...${NC}"

    # Start server in background
    npm start &
    SERVER_PID=$!

    # Wait a moment for server to start
    sleep 3

    # Check if process is still running
    if ! kill -0 $SERVER_PID 2>/dev/null; then
        echo -e "${RED}❌ Server failed to start${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ Server started with PID: $SERVER_PID${NC}"

    # Perform health check
    if health_check; then
        echo -e "${GREEN}🎉 API Gateway is running successfully!${NC}"
        echo -e "${GREEN}📋 Environment: $(node -e \"console.log(process.env.NODE_ENV || 'development')\")${NC}"
        echo -e "${GREEN}🏥 Health Check: http://localhost:3001/health${NC}"
        echo -e "${GREEN}📖 API Docs: http://localhost:3001/api${NC}"
        echo -e "${GREEN}🔑 Default Admin: admin@aitrading.com / Admin123!${NC}"
        echo -e "${GREEN}👤 Default User: user@aitrading.com / User123!${NC}"

        # Keep script running and handle signals
        trap "echo -e '\n${YELLOW}🛑 Stopping API Gateway...${NC}'; kill $SERVER_PID; exit 0" SIGINT SIGTERM

        # Wait for server process
        wait $SERVER_PID
    else
        echo -e "${RED}❌ Server health check failed${NC}"
        kill $SERVER_PID 2>/dev/null || true
        exit 1
    fi
}

# Function to stop existing server
stop_existing() {
    echo -e "${YELLOW}🔍 Checking for existing API Gateway processes...${NC}"

    # Find processes using port 3001
    local pids=$(lsof -ti:3001 2>/dev/null || true)

    if [ -n "$pids" ]; then
        echo -e "${YELLOW}🛑 Stopping existing processes on port 3001...${NC}"
        echo "$pids" | xargs kill -TERM 2>/dev/null || true
        sleep 2

        # Force kill if still running
        local remaining=$(lsof -ti:3001 2>/dev/null || true)
        if [ -n "$remaining" ]; then
            echo -e "${YELLOW}🔥 Force killing remaining processes...${NC}"
            echo "$remaining" | xargs kill -9 2>/dev/null || true
        fi
    fi
}

# Main execution
case "${1:-start}" in
    "start")
        stop_existing
        start_server
        ;;
    "stop")
        stop_existing
        echo -e "${GREEN}✅ API Gateway stopped${NC}"
        ;;
    "restart")
        stop_existing
        sleep 2
        start_server
        ;;
    "health")
        if health_check; then
            echo -e "${GREEN}✅ API Gateway is healthy${NC}"
            exit 0
        else
            echo -e "${RED}❌ API Gateway is not responding${NC}"
            exit 1
        fi
        ;;
    "status")
        if curl -s -f http://localhost:3001/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ API Gateway is running${NC}"
            curl -s http://localhost:3001/health
        else
            echo -e "${RED}❌ API Gateway is not running${NC}"
            exit 1
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|health|status}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the API Gateway server"
        echo "  stop    - Stop the API Gateway server"
        echo "  restart - Restart the API Gateway server"
        echo "  health  - Check if the API Gateway is healthy"
        echo "  status  - Show current status and health"
        exit 1
        ;;
esac