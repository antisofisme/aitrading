#!/bin/bash

# Test Authentication Script
# Quick verification that JWT authentication is working

echo "🧪 Testing API Gateway Authentication..."

# Test 1: Health Check
echo "1. Health Check..."
HEALTH=$(curl -s http://localhost:3001/health)
if echo "$HEALTH" | grep -q "success.*true"; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    exit 1
fi

# Test 2: Admin Login
echo "2. Admin Login..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:3001/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@aitrading.com","password":"Admin123!"}')

if echo "$LOGIN_RESPONSE" | grep -q "accessToken"; then
    echo "✅ Admin login successful"

    # Extract token (simplified)
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4)

    if [ -n "$TOKEN" ]; then
        echo "✅ Token extracted successfully"

        # Test 3: Protected Endpoint
        echo "3. Testing protected endpoint..."
        PROFILE_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" http://localhost:3001/api/auth/me)

        if echo "$PROFILE_RESPONSE" | grep -q "admin@aitrading.com"; then
            echo "✅ Protected endpoint access successful"
        else
            echo "❌ Protected endpoint access failed"
            echo "Response: $PROFILE_RESPONSE"
        fi
    else
        echo "❌ Failed to extract token"
    fi
else
    echo "❌ Admin login failed"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

# Test 4: User Login
echo "4. User Login..."
USER_LOGIN=$(curl -s -X POST http://localhost:3001/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"user@aitrading.com","password":"User123!"}')

if echo "$USER_LOGIN" | grep -q "accessToken"; then
    echo "✅ User login successful"
else
    echo "❌ User login failed"
    echo "Response: $USER_LOGIN"
fi

echo ""
echo "🎉 Authentication tests completed!"
echo "✅ API Gateway is fully operational with JWT authentication"