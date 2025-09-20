#!/bin/bash
echo "📦 Trading Engine: EMERGENCY PyPI FIX - Installing dependencies..."

# EMERGENCY FIX: Direct PyPI install to resolve missing dependencies
echo "🚀 Installing core dependencies first..."
pip install --break-system-packages --no-deps fastapi uvicorn pydantic requests python-dotenv

echo "📦 Installing remaining requirements..."
pip install -r requirements.txt --break-system-packages

echo "✅ Trading Engine: Dependencies installed successfully"
