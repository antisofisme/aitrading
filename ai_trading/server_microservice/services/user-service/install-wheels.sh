#!/bin/bash
echo "📦 User Service: Installing dependencies from local wheels (offline first)..."

# OFFLINE FIRST strategy - use local wheels without internet, fallback to PyPI
if [ -d "wheels" ] && [ "$(ls -A wheels)" ]; then
    echo "🔒 Attempting OFFLINE installation from local wheels..."
    pip install --no-index --find-links wheels/ -r requirements.txt --quiet --break-system-packages || {
        echo "⚠️ Some packages missing from wheels, using PyPI fallback..."
        pip install --find-links wheels/ -r requirements.txt --quiet --break-system-packages
    }
else
    echo "⚠️ No wheels directory found, installing from PyPI..."
    pip install -r requirements.txt --quiet --break-system-packages
fi
echo "✅ User Service: Dependencies installed successfully"
