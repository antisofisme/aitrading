#!/bin/bash
echo "📦 AI Provider: Installing dependencies (DIRECT PyPI - emergency fix)..."

# EMERGENCY FIX: Direct PyPI install to resolve missing dependencies
echo "🚀 Installing core dependencies first..."
pip install --break-system-packages --no-deps fastapi uvicorn pydantic requests python-dotenv

echo "📦 Installing remaining requirements..."
pip install -r requirements.txt --break-system-packages

echo "✅ AI Provider: Dependencies installed successfully"
