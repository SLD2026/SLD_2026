#!/bin/bash

# Script Installer untuk River Monitoring System
# Living Lab Sekanak Connect
# Created: 2024-10-24

echo "=================================================="
echo "🌊 LIVING LAB SEKANAK CONNECT"
echo "   Installer Dependencies"
echo "=================================================="
echo ""

# Warna untuk output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fungsi untuk menampilkan status
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check jika script dijalankan dari direktori yang benar
if [ ! -f "main.py" ]; then
    print_error "Script harus dijalankan dari direktori river_monitoring_system!"
    echo "Gunakan: cd /home/noc/river_monitoring_system && bash install_dependencies.sh"
    exit 1
fi

print_status "Memeriksa Python installation..."
if ! command -v python3 &> /dev/null; then
    print_error "Python3 tidak ditemukan! Silakan install Python 3.10+ terlebih dahulu."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
print_success "Python $PYTHON_VERSION terdeteksi"

# Check apakah virtual environment sudah ada
if [ -d "venv_linux" ]; then
    print_warning "Virtual environment 'venv_linux' sudah ada."
    read -p "Hapus dan buat ulang? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Menghapus virtual environment lama..."
        rm -rf venv_linux
    else
        print_status "Menggunakan virtual environment yang ada..."
    fi
fi

# Buat virtual environment jika belum ada
if [ ! -d "venv_linux" ]; then
    print_status "Membuat virtual environment baru..."
    python3 -m venv venv_linux
    if [ $? -eq 0 ]; then
        print_success "Virtual environment berhasil dibuat"
    else
        print_error "Gagal membuat virtual environment"
        exit 1
    fi
fi

# Aktivasi virtual environment
print_status "Mengaktifkan virtual environment..."
source venv_linux/bin/activate

if [ $? -eq 0 ]; then
    print_success "Virtual environment aktif"
else
    print_error "Gagal mengaktifkan virtual environment"
    exit 1
fi

# Update pip, setuptools, wheel
print_status "Updating pip, setuptools, dan wheel..."
pip install --upgrade pip setuptools wheel

echo ""
echo "=================================================="
echo "📦 INSTALASI DEPENDENCIES"
echo "=================================================="
echo ""

# Install dependencies bertahap
print_status "Step 1/6: Installing Web Framework & Server..."
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 python-multipart==0.0.6 jinja2==3.1.2

print_status "Step 2/6: Installing Database & ORM..."
pip install sqlalchemy==2.0.23 alembic==1.12.1

print_status "Step 3/6: Installing Core Utilities..."
pip install numpy==1.24.3 pillow==10.1.0 requests==2.31.0 python-dotenv==1.0.0 pydantic==2.5.0 psutil==5.9.6

print_status "Step 4/6: Installing OpenCV..."
pip install opencv-python==4.8.1.78 opencv-contrib-python==4.8.1.78

echo ""
print_warning "Langkah berikutnya akan menginstall PyTorch dan library AI (cukup besar)"
print_warning "Pastikan Anda memiliki koneksi internet yang stabil"
read -p "Lanjutkan? (y/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Step 5/6: Installing PyTorch (CUDA 11.8)..."
    pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu118
    
    print_status "Step 6/6: Installing YOLOv8 & InsightFace..."
    pip install ultralytics==8.0.220
    pip install insightface==0.7.3 onnxruntime-gpu==1.16.3
else
    print_warning "Instalasi PyTorch dan AI libraries dilewati"
    print_warning "Anda perlu menginstall secara manual nanti:"
    echo "  - torch, torchvision"
    echo "  - ultralytics (YOLOv8)"
    echo "  - insightface"
    echo "  - onnxruntime-gpu"
fi

echo ""
echo "=================================================="
echo "✅ INSTALASI SELESAI!"
echo "=================================================="
echo ""

# Verifikasi instalasi
print_status "Memverifikasi instalasi..."
python3 -c "
import sys
packages = {
    'fastapi': 'FastAPI',
    'uvicorn': 'Uvicorn',
    'cv2': 'OpenCV',
    'sqlalchemy': 'SQLAlchemy',
    'numpy': 'NumPy',
    'PIL': 'Pillow',
    'requests': 'Requests',
}

print('\n📋 Status Dependencies:\n')
missing = []
for module, name in packages.items():
    try:
        __import__(module)
        print(f'  ✓ {name}')
    except ImportError:
        print(f'  ✗ {name} (MISSING)')
        missing.append(name)

# Check optional AI libraries
ai_packages = {
    'torch': 'PyTorch',
    'ultralytics': 'YOLOv8',
    'insightface': 'InsightFace',
}

print('\n📋 Status AI Libraries (Optional):\n')
for module, name in ai_packages.items():
    try:
        __import__(module)
        print(f'  ✓ {name}')
    except ImportError:
        print(f'  ⚠ {name} (OPTIONAL - Not Installed)')

if missing:
    print(f'\n⚠️  Ada {len(missing)} package yang gagal terinstall')
    sys.exit(1)
else:
    print('\n✅ Semua core dependencies berhasil terinstall!')
    sys.exit(0)
"

VERIFY_STATUS=$?

echo ""
if [ $VERIFY_STATUS -eq 0 ]; then
    print_success "Verifikasi berhasil!"
    echo ""
    echo "=================================================="
    echo "🚀 CARA MENJALANKAN SISTEM"
    echo "=================================================="
    echo ""
    echo "1. Aktifkan virtual environment:"
    echo "   source venv_linux/bin/activate"
    echo ""
    echo "2. Jalankan server:"
    echo "   python3 main.py"
    echo ""
    echo "3. Buka browser dan akses:"
    echo "   http://localhost:8000"
    echo ""
    echo "=================================================="
    echo "📝 CATATAN PENTING"
    echo "=================================================="
    echo ""
    echo "- Pastikan CUDA drivers terinstall untuk GPU acceleration"
    echo "- Folder database_wajah/ berisi foto referensi wajah"
    echo "- Edit config.py untuk konfigurasi RTSP dan threshold"
    echo "- Gunakan ROI Editor (/roi) untuk mengatur area monitoring"
    echo ""
else
    print_error "Beberapa dependencies gagal terinstall"
    echo ""
    echo "Silakan cek error di atas dan install manual jika perlu."
    echo "Untuk install manual, gunakan:"
    echo "  source venv_linux/bin/activate"
    echo "  pip install -r requirements.txt"
    echo ""
fi

print_status "Script installer selesai."
echo ""
