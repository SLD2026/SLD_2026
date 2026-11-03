#!/bin/bash
# Script untuk monitoring GPU usage real-time

echo "🔍 Monitoring GPU Usage - Press Ctrl+C to stop"
echo "================================================"
echo ""

while true; do
    clear
    echo "🖥️  GPU USAGE MONITOR"
    echo "$(date '+%Y-%m-%d %H:%M:%S')"
    echo "================================================"
    
    if command -v nvidia-smi &> /dev/null; then
        nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,utilization.memory,memory.used,memory.total --format=csv,noheader,nounits | while IFS=, read -r idx name temp gpu_util mem_util mem_used mem_total; do
            echo ""
            echo "GPU $idx: $name"
            echo "  🌡️  Temperature: ${temp}°C"
            echo "  ⚡ GPU Usage: ${gpu_util}%"
            echo "  💾 Memory Usage: ${mem_util}% (${mem_used}MB / ${mem_total}MB)"
        done
        
        echo ""
        echo "================================================"
        echo "🔄 Refreshing in 2 seconds..."
        echo "   (Start streaming kamera untuk lihat usage naik)"
    else
        echo "❌ nvidia-smi not found"
        echo "   Install: sudo apt install nvidia-utils"
        exit 1
    fi
    
    sleep 2
done
