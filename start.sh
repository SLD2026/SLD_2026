#!/bin/bash

# Quick Start Script untuk River Monitoring System
# Living Lab Sekanak Connect

echo "=================================================="
echo "🌊 LIVING LAB SEKANAK CONNECT"
echo "   Quick Start Guide"
echo "=================================================="
echo ""

cd /home/noc/river_monitoring_system

# Check apakah dependencies sudah terinstall
if [ -d "venv_linux" ]; then
    echo "✅ Virtual environment ditemukan"
    source venv_linux/bin/activate
    
    # Check apakah FastAPI terinstall
    python3 -c "import fastapi" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ Dependencies terdeteksi"
        echo ""
        echo "🚀 Menjalankan server..."
        echo ""
        python3 main.py
    else
        echo "⚠️  Dependencies belum lengkap"
        echo ""
        echo "Jalankan installer terlebih dahulu:"
        echo "  bash install_dependencies.sh"
        exit 1
    fi
else
    echo "⚠️  Virtual environment belum dibuat"
    echo ""
    echo "Jalankan installer terlebih dahulu:"
    echo "  bash install_dependencies.sh"
    exit 1
fi
