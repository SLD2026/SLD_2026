#!/usr/bin/env bash
set -euo pipefail
cd /home/noc/river_monitoring_system
export PATH="/home/noc/.local/bin:$PATH"
export PYTHONPATH="/home/noc/.local/lib/python3.14/site-packages"
lsof -ti:8000 2>/dev/null | xargs -r kill -9 || true
pkill -f "main.py" || true
pkill -f "uvicorn" || true
sleep 1
python3 main.py