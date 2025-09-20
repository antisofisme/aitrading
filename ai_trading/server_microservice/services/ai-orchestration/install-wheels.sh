#!/bin/bash
echo "📦 AI Orchestration: EMERGENCY PyPI FIX - Installing dependencies..."

# EMERGENCY FIX: Direct PyPI install to resolve missing dependencies
echo "🚀 Installing core dependencies first..."
pip install --break-system-packages --no-deps fastapi uvicorn pydantic requests python-dotenv

echo "📦 Installing remaining requirements..."
pip install -r requirements.txt --break-system-packages

echo "✅ AI Orchestration: Dependencies installed successfully"
