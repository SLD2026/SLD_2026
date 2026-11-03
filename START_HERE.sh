#!/usr/bin/env bash
# ============================================
# River Monitoring System - Main Startup Script
# ============================================
set -euo pipefail

echo "=================================================="
echo "🚀 RIVER MONITORING SYSTEM - STARTING..."
echo "=================================================="

cd /home/noc/river_monitoring_system

# Set environment
export PATH="/home/noc/.local/bin:$PATH"
export PYTHONPATH="/home/noc/.local/lib/python3.14/site-packages"

# Cleanup existing processes
echo "🧹 Cleaning up existing processes..."
lsof -ti:8000 2>/dev/null | xargs -r kill -9 || true
pkill -f "main.py" || true
pkill -f "uvicorn" || true
sleep 2

echo "✓ Cleanup done"
echo ""
echo "=================================================="
echo "🌊 Launching Server..."
echo "=================================================="
echo ""
echo "📱 Access dashboard at: http://localhost:8000"
echo "⚠️  Press Ctrl+C to stop"
echo ""
echo "--------------------------------------------------"
echo ""

# Start server
python3 main.py