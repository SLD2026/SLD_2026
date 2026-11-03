#!/bin/bash

# ==================================================
# 🌊 LIVING LAB SEKANAK CONNECT
#    River Monitoring System - Launcher
# ==================================================

clear
echo "=================================================="
echo "🌊 LIVING LAB SEKANAK CONNECT"
echo "   Smart Littering Detector System"
echo "=================================================="
echo ""

# Warna untuk output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Fungsi print
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

# Pindah ke direktori aplikasi
cd /home/noc/river_monitoring_system

# Check dependencies
print_info "Memeriksa dependencies..."
python3 -c "
import sys
try:
    import fastapi, uvicorn, cv2, torch
    from ultralytics import YOLO
    print('✅ All dependencies OK')
    sys.exit(0)
except ImportError as e:
    print(f'❌ Missing dependency: {e}')
    sys.exit(1)
" 2>/dev/null

if [ $? -ne 0 ]; then
    print_error "Dependencies tidak lengkap!"
    echo ""
    echo "Jalankan installer terlebih dahulu:"
    echo "  bash install_dependencies.sh"
    echo ""
    exit 1
fi

print_success "Dependencies lengkap!"
echo ""

# Check database directory
if [ ! -d "backend_api/database" ]; then
    print_info "Membuat direktori database..."
    mkdir -p backend_api/database
fi

# Check evidence directory
if [ ! -d "frontend/static/violations" ]; then
    print_info "Membuat direktori violations..."
    mkdir -p frontend/static/violations
fi

# Add local bin to PATH (untuk uvicorn, fastapi scripts)
export PATH="/home/noc/.local/bin:$PATH"

# Check CUDA availability
print_info "Checking GPU availability..."
python3 -c "
import torch
if torch.cuda.is_available():
    print(f'✅ GPU Ready: {torch.cuda.get_device_name(0)}')
    print(f'   CUDA Version: {torch.version.cuda}')
else:
    print('⚠️  GPU not available, using CPU mode')
" 2>/dev/null

echo ""
print_info "Menjalankan Face Recognition initialization..."
python3 -c "
try:
    from core_engine.face_recognizer import FaceRecognizer
    print('✅ Face Recognition ready')
except Exception as e:
    print(f'⚠️  Face Recognition: {str(e)[:60]}...')
" 2>/dev/null

echo ""
echo "=================================================="
echo "🚀 STARTING SERVER"
echo "=================================================="
echo ""
print_info "Server akan berjalan di:"
echo ""
echo "   🌐 Local:   http://127.0.0.1:8000"
echo "   🌐 Network: http://$(hostname -I | awk '{print $1}'):8000"
echo ""
print_warning "Tekan Ctrl+C untuk menghentikan server"
echo ""
echo "=================================================="
echo ""

# Jalankan server dengan auto-reload
python3 main.py

# Jika server berhenti
echo ""
print_info "Server stopped."
