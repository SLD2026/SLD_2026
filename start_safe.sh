#!/usr/bin/env bash
# ============================================
# SAFE MODE STARTUP SCRIPT
# Fix untuk Segmentation Fault Issue
# ============================================

set -euo pipefail

echo "=================================================="
echo "🔧 STARTING RIVER MONITORING SYSTEM (SAFE MODE)"
echo "=================================================="

# 1. Set working directory
cd /home/noc/river_monitoring_system

# 2. Set Python path
export PATH="/home/noc/.local/bin:$PATH"
export PYTHONPATH="/home/noc/.local/lib/python3.14/site-packages"

# 3. Set environment variables untuk fix segfault
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export OPENCV_OPENCL_RUNTIME=''
export OPENCV_OPENCL_DEVICE='disabled'

# Disable Intel MKL yang sering cause segfault
export MKL_SERVICE_FORCE_INTEL=0

# Set CUDA visible devices (optional - uncomment jika masih crash)
# export CUDA_VISIBLE_DEVICES=0

echo ""
echo "✓ Environment variables configured"
echo ""

# 4. Kill existing processes
echo "🧹 Cleaning up existing processes..."
lsof -ti:8000 2>/dev/null | xargs -r kill -9 || true
pkill -f "main.py" || true
pkill -f "uvicorn" || true
sleep 2

echo "✓ Cleanup done"
echo ""

# 5. Verify Python environment
echo "🔍 Verifying Python environment..."
python3 --version
echo ""

# 6. Quick validation test
echo "🧪 Running quick validation..."
python3 -c "
import cv2
import torch
print(f'  OpenCV: {cv2.__version__}')
print(f'  PyTorch: {torch.__version__}')
print(f'  CUDA Available: {torch.cuda.is_available()}')
" || {
    echo "❌ Validation failed!"
    exit 1
}

echo ""
echo "✅ All checks passed!"
echo ""
echo "=================================================="
echo "🚀 LAUNCHING SERVER..."
echo "=================================================="
echo ""
echo "📱 Access the dashboard at: http://localhost:8000"
echo "⚠️  Press Ctrl+C to stop the server"
echo ""
echo "--------------------------------------------------"
echo ""

# 7. Start server with single worker mode
exec python3 main.py
