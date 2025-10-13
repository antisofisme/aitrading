#!/bin/bash
set -e

echo "🔧 Starting Cloudflare WARP setup..."

# Start WARP daemon
echo "📡 Starting WARP daemon..."
warp-svc &
WARP_PID=$!

# Wait for daemon to be ready
echo "⏳ Waiting for WARP daemon to start..."
for i in {1..30}; do
    if warp-cli --accept-tos status >/dev/null 2>&1; then
        echo "✅ WARP daemon ready"
        break
    fi
    echo "   Attempt $i/30..."
    sleep 2
done

# Check if daemon started
if ! warp-cli --accept-tos status >/dev/null 2>&1; then
    echo "❌ WARP daemon failed to start after 60 seconds"
    echo "📋 Continuing without WARP..."
    exec python3 /app/src/main.py
fi

# Register WARP with Teams license key
WARP_LICENSE_KEY="${WARP_LICENSE_KEY:-XrfV4782-W2X39u4G-h49e78ya}"
echo "🔑 Registering WARP with Teams license..."
warp-cli --accept-tos registration license "$WARP_LICENSE_KEY" || echo "⚠️ License registration failed (may already be registered)"

# Set mode to WARP (full tunnel)
echo "🔧 Setting WARP mode..."
warp-cli --accept-tos mode warp || echo "⚠️ Mode already set"

# Connect to WARP
echo "🚀 Connecting to WARP..."
warp-cli --accept-tos connect

# Wait for connection
echo "⏳ Waiting for WARP connection..."
sleep 15

# Check WARP status
echo "✅ WARP Status:"
warp-cli --accept-tos status || true

# Test connectivity to Dukascopy
echo "🧪 Testing Dukascopy connectivity..."
curl -I --connect-timeout 15 https://datafeed.dukascopy.com/ || echo "⚠️ Dukascopy test failed (will retry during download)"

echo "✅ WARP setup complete, starting application..."

# Start main application
exec python3 /app/src/main.py
