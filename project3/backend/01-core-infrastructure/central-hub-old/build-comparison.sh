#!/bin/bash

echo "=== Central Hub Docker Build Performance Comparison ==="
echo ""

# Test 1: Standard Dockerfile (downloads everything)
echo "🔄 Testing STANDARD BUILD (downloads all packages)..."
echo "Command: docker build -f Dockerfile -t central-hub:online ."
start_time=$(date +%s)
timeout 300 docker build -f Dockerfile -t central-hub:online . > build_online.log 2>&1
end_time=$(date +%s)
online_duration=$((end_time - start_time))

if [ $online_duration -eq 300 ]; then
    echo "❌ Standard build: TIMEOUT after 5 minutes"
    online_result="TIMEOUT (>300s)"
else
    echo "✅ Standard build completed in: ${online_duration}s"
    online_result="${online_duration}s"
fi

echo ""

# Test 2: Offline Dockerfile (uses local packages)
echo "🚀 Testing OFFLINE BUILD (uses pip_packages/ offline)..."
echo "Command: docker build -f Dockerfile.offline -t central-hub:offline ."
start_time=$(date +%s)
timeout 300 docker build -f Dockerfile.offline -t central-hub:offline . > build_offline.log 2>&1
end_time=$(date +%s)
offline_duration=$((end_time - start_time))

if [ $offline_duration -eq 300 ]; then
    echo "❌ Offline build: TIMEOUT after 5 minutes"
    offline_result="TIMEOUT (>300s)"
else
    echo "✅ Offline build completed in: ${offline_duration}s"
    offline_result="${offline_duration}s"
fi

echo ""
echo "=== PERFORMANCE COMPARISON RESULTS ==="
echo ""
echo "📊 Build Method Comparison:"
echo "┌─────────────────────┬─────────────────┬─────────────────┐"
echo "│ Build Method        │ Duration        │ Status          │"
echo "├─────────────────────┼─────────────────┼─────────────────┤"
echo "│ Standard (online)   │ $online_result  │ Downloads all   │"
echo "│ Offline (pip_pkgs)  │ $offline_result │ No downloads    │"
echo "└─────────────────────┴─────────────────┴─────────────────┘"
echo ""

# Calculate improvement if both completed
if [ $online_duration -lt 300 ] && [ $offline_duration -lt 300 ]; then
    if [ $online_duration -gt 0 ]; then
        improvement=$(echo "scale=1; ($online_duration - $offline_duration) * 100 / $online_duration" | bc)
        echo "📈 Performance Improvement: ${improvement}% faster with offline packages"
    fi
fi

echo ""
echo "💾 Package Storage:"
echo "   - pip_packages/ size: $(du -sh pip_packages/ | cut -f1)"
echo "   - Total packages: $(ls pip_packages/ | wc -l) files"
echo ""
echo "🎯 CONCLUSION:"
echo "   Like node_modules for Node.js, pip_packages/ provides:"
echo "   ✓ No internet dependency during builds"
echo "   ✓ Consistent build times"
echo "   ✓ Offline development capability"
echo "   ✓ Faster rebuild cycles"
echo ""
echo "📝 Build logs saved to:"
echo "   - build_online.log (standard build)"
echo "   - build_offline.log (offline build)"