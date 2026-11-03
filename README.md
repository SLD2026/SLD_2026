# 🌊 Living Lab Sekanak Connect - Smart Littering Detector

Sistem monitoring otomatis pembuangan sampah ke sungai berbasis AI dengan YOLOv8 dan Face Recognition.

## 📋 Daftar Isi

- [Fitur Utama](#fitur-utama)
- [Teknologi Stack](#teknologi-stack)
- [Instalasi](#instalasi)
- [Cara Menjalankan](#cara-menjalankan)
- [Fitur ROI (Region of Interest)](#fitur-roi)
- [Konfigurasi](#konfigurasi)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Fitur Utama

### ✅ Yang Sudah Diimplementasikan

1. **Multi-Camera RTSP Streaming**
   - Support 8+ kamera concurrent
   - Auto-reconnect saat stream terputus
   - Buffer management untuk real-time processing

2. **AI Object Detection**
   - YOLOv8 untuk deteksi person, bottle, cup
   - CUDA GPU acceleration (RTX 3050)
   - Real-time tracking dengan persistence

3. **Face Recognition**
   - InsightFace buffalo_l model
   - Database wajah dengan 7 orang (21 foto)
   - Cosine similarity matching

4. **Behavior Analysis**
   - Deteksi aktivitas membuang sampah
   - Proximity detection (600px radius)
   - IoA (Intersection over Area) calculation

5. **ROI (Region of Interest)** ⭐ **BARU!**
   - Interactive polygon drawing
   - Per-camera ROI configuration
   - Visual overlay di live stream
   - Database persistence

6. **Evidence Management**
   - Auto-capture screenshot pelaku
   - Crop & save ke `barang_bukti/`
   - Database logging dengan timestamp

7. **Telegram Integration**
   - Real-time notification
   - Photo evidence attachment
   - Identified person name

8. **Web Dashboard**
   - Live stream monitoring
   - Camera management (CRUD)
   - ROI editor interface
   - Violation logs gallery
   - System metrics (FPS, storage)

---

## 💻 Teknologi Stack

### Backend
- **Python 3.10+**
- **FastAPI** - Modern web framework
- **SQLAlchemy** - Database ORM
- **SQLite** - Database
- **Uvicorn** - ASGI server

### AI & Computer Vision
- **YOLOv8** (Ultralytics) - Object detection
- **InsightFace** - Face recognition
- **OpenCV** - Image processing
- **PyTorch** - Deep learning framework
- **CUDA 11.8** - GPU acceleration

### Frontend
- **HTML5 + JavaScript**
- **Bootstrap 5** - UI framework
- **MJPEG Streaming** - Video display

---

## 🚀 Instalasi

### Metode 1: Installer Otomatis (Recommended)

```bash
cd /home/noc/river_monitoring_system
bash install_dependencies.sh
```

Script akan otomatis:
- ✅ Membuat virtual environment Linux
- ✅ Install semua dependencies
- ✅ Verifikasi instalasi
- ✅ Menampilkan panduan quick start

### Metode 2: Manual Installation

```bash
# 1. Buat virtual environment
python3 -m venv venv_linux

# 2. Aktivasi virtual environment
source venv_linux/bin/activate

# 3. Upgrade pip
pip install --upgrade pip setuptools wheel

# 4. Install dependencies
pip install -r requirements.txt

# 5. Install PyTorch dengan CUDA (opsional tapi recommended)
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu118

# 6. Install AI libraries
pip install ultralytics==8.0.220 insightface==0.7.3 onnxruntime-gpu==1.16.3
```

### System Requirements

**Minimum:**
- OS: Ubuntu 20.04+ / Windows 10+
- RAM: 8GB
- Storage: 100GB
- GPU: NVIDIA GTX 1650 (4GB VRAM)

**Recommended:**
- OS: Ubuntu 22.04 LTS
- RAM: 16GB
- Storage: 500GB SSD
- GPU: NVIDIA RTX 3050 (8GB VRAM)
- CUDA: 11.8+

---

## 🎬 Cara Menjalankan

### Metode 1: Quick Start Script

```bash
cd /home/noc/river_monitoring_system
bash start.sh
```

### Metode 2: Manual Start

```bash
cd /home/noc/river_monitoring_system
source venv_linux/bin/activate
python3 main.py
```

### Akses Dashboard

Buka browser dan akses:
```
http://localhost:8000
```

Atau dari komputer lain di jaringan yang sama:
```
http://192.168.x.x:8000
```
*(Ganti dengan IP server Anda)*

---

## 🎯 Fitur ROI (Region of Interest)

### Apa itu ROI?

ROI adalah area spesifik dalam frame video yang akan dimonitor. Hanya aktivitas di dalam ROI yang akan terdeteksi.

### Cara Menggunakan ROI Editor

1. **Akses ROI Editor**
   ```
   http://localhost:8000/roi
   ```

2. **Pilih Kamera**
   - Pilih dari dropdown di panel kiri

3. **Gambar Polygon ROI**
   - Klik pada video untuk menandai titik
   - Minimal 3 titik untuk membuat polygon
   - Titik akan terhubung otomatis

4. **Simpan ROI**
   - Klik tombol "💾 Simpan ROI"
   - ROI akan aktif untuk kamera tersebut

5. **Load ROI Tersimpan**
   - Klik "📥 Load ROI Tersimpan" untuk melihat ROI yang sudah ada

### Visualisasi ROI

- **Cyan Overlay**: Area ROI di live stream
- **Red Points**: Lokasi titik-titik ROI
- **Green Border**: Border polygon ROI

📖 **Panduan lengkap**: Lihat file `ROI_GUIDE.md`

---

## ⚙️ Konfigurasi

### File: `config.py`

```python
# Database
DATABASE_URL = "sqlite:///backend_api/database/river_monitor.db"

# AI Models
YOLO_MODEL_PATH = "dataset_training/weights/yolo_trash_best.pt"
YOLO_CONFIDENCE = 0.65

# Face Recognition
FACE_MATCH_THRESHOLD = 0.60

# Evidence Storage
VIOLATION_CROP_DIR = "frontend/static/violations/"

# Server
HOST = "0.0.0.0"
PORT = 8000
```

### Kamera RTSP

Format URL RTSP untuk Hikvision NVR:
```
rtsp://username:password@IP_NVR:554/Streaming/Channels/101
```

Contoh:
```
rtsp://kamera_ai:Password12@192.168.99.10:554/Streaming/Channels/101
```

Channel mapping:
- Channel 101 = Kamera 1
- Channel 201 = Kamera 2
- Channel 301 = Kamera 3
- dst...

### Database Wajah

Format folder `database_wajah/`:
```
database_wajah/
├── Nama1_1.PNG
├── Nama1_2.PNG
├── Nama1_3.PNG
├── Nama2_1.PNG
└── ...
```

**Aturan penamaan**: `NamaOrang_NomorFoto.extension`

Sistem akan otomatis:
- Load semua foto saat startup
- Extract face embeddings
- Match dengan wajah terdeteksi

---

## 📡 API Documentation

### Camera Management

#### Get All Cameras
```http
GET /api/cameras/list
```

#### Add Camera
```http
POST /api/cameras/add
Content-Type: application/json

{
  "camera_id": "CAM_01",
  "name": "Kamera Jembatan",
  "rtsp_url": "rtsp://user:pass@192.168.1.10:554/stream",
  "roi_polygon": "[]"
}
```

#### Start Camera
```http
POST /api/cameras/{camera_id}/start
```

#### Stop Camera
```http
POST /api/cameras/{camera_id}/stop
```

#### Delete Camera
```http
DELETE /api/cameras/delete/{camera_id}
```

### ROI Management

#### Update ROI
```http
POST /api/cameras/{camera_id}/roi
Content-Type: application/json

{
  "roi_polygon": "[[120,50],[640,50],[640,480],[120,480]]"
}
```

#### Get ROI
```http
GET /api/cameras/{camera_id}/roi
```

### Video Streaming

#### Get MJPEG Stream
```http
GET /api/stream/{camera_id}
```

### System Stats

#### Get System Metrics
```http
GET /api/cameras/system/stats
```

Response:
```json
{
  "storage_percent": 45.2,
  "fps": 27.3
}
```

---

## 🗂️ Struktur Direktori

```
river_monitoring_system/
│
├── main.py                      # Entry point
├── config.py                    # Configuration
├── requirements.txt             # Python dependencies
├── install_dependencies.sh      # Auto installer
├── start.sh                     # Quick start script
├── ROI_GUIDE.md                 # ROI documentation
│
├── backend_api/
│   ├── schemas.py              # Pydantic models
│   ├── database/
│   │   ├── models.py           # SQLAlchemy models
│   │   └── river_monitor.db    # SQLite database
│   └── routers/
│       ├── camera_routes.py    # Camera API
│       └── stream_routes.py    # Streaming API
│
├── core_engine/
│   ├── detector.py             # YOLOv8 detector
│   ├── face_recognizer.py      # Face recognition
│   ├── behavior_analyzer.py    # Littering detection
│   ├── stream_manager.py       # RTSP manager
│   └── vision_pipeline.py      # AI orchestrator
│
├── frontend/
│   ├── templates/
│   │   ├── index.html          # Dashboard
│   │   ├── cameras.html        # Camera management
│   │   ├── roi_editor.html     # ROI editor ⭐ NEW!
│   │   └── logs.html           # Violation logs
│   └── static/
│       ├── css/                # Stylesheets
│       ├── js/                 # JavaScript
│       └── violations/         # Evidence photos
│
├── database_wajah/             # Face database
│   ├── Nama1_1.PNG
│   └── ...
│
├── dataset_training/
│   └── weights/
│       └── yolo_trash_best.pt  # Custom YOLO model
│
├── barang_bukti/               # Evidence backup
│
├── yolov8s.pt                  # Generic YOLO model
├── yolov8n.pt                  # Nano YOLO model
└── tele_bot.py                 # Telegram integration
```

---

## 🔧 Troubleshooting

### ❌ Error: "Module not found"

**Solusi:**
```bash
source venv_linux/bin/activate
pip install -r requirements.txt
```

### ❌ CUDA Error / GPU not detected

**Solusi:**
```bash
# Check NVIDIA driver
nvidia-smi

# Reinstall PyTorch dengan CUDA
pip uninstall torch torchvision
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu118
```

### ❌ RTSP Stream tidak muncul

**Penyebab:**
- Kamera tidak aktif
- URL RTSP salah
- Firewall blocking port 554

**Solusi:**
```bash
# Test RTSP dengan test_kamera.py
python3 test_kamera.py

# Check konfigurasi di cameras table
# Pastikan rtsp_url benar dan is_active = 1
```

### ❌ Face Recognition tidak berfungsi

**Penyebab:**
- Folder `database_wajah/` kosong
- Format nama file salah

**Solusi:**
```bash
# Check isi folder
ls -la database_wajah/

# Format harus: NamaOrang_NomorFoto.extension
# Contoh: Andi_1.PNG, Andi_2.PNG, Budi_1.PNG
```

### ⚠️ Server lambat / FPS rendah

**Solusi:**
- Kurangi confidence threshold di `detector.py`
- Gunakan model lebih kecil (yolov8n.pt)
- Kurangi jumlah kamera concurrent
- Pastikan GPU digunakan (bukan CPU)

### ⚠️ Database locked error

**Solusi:**
```bash
# Stop semua instance yang running
pkill -f "python3 main.py"

# Hapus lock file (jika ada)
rm -f backend_api/database/*.db-shm
rm -f backend_api/database/*.db-wal

# Restart
python3 main.py
```

---

## 📊 Performance Tips

### Optimasi GPU
```python
# Gunakan half-precision untuk inference lebih cepat
model = YOLO("yolov8s.pt")
model.to('cuda')
results = model.predict(frame, half=True)  # FP16
```

### Optimasi Stream
```python
# Kurangi buffer size
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

# Skip frames jika perlu
if frame_count % 2 == 0:  # Process every 2nd frame
    continue
```

### Optimasi Database
```sql
-- Create index untuk query lebih cepat
CREATE INDEX idx_camera_id ON violation_logs(camera_id);
CREATE INDEX idx_timestamp ON violation_logs(timestamp);
```

---

## 📝 TODO / Future Features

- [ ] PostgreSQL support untuk production
- [ ] Video recording (not just screenshots)
- [ ] WhatsApp integration
- [ ] Email notifications
- [ ] Multi-language support
- [ ] Dark/Light theme toggle
- [ ] User authentication & authorization
- [ ] Advanced analytics dashboard
- [ ] Export reports (PDF, Excel)
- [ ] Mobile app (React Native)

---

## 🤝 Contributing

Untuk kontribusi atau bug report, hubungi administrator sistem.

---

## 📄 License

Proprietary - Living Lab Sekanak Connect © 2024

---

## 👥 Credits

**Developed for**: Living Lab Sekanak Connect  
**AI Models**: YOLOv8 (Ultralytics), InsightFace  
**Framework**: FastAPI, OpenCV, PyTorch  

---

## 📞 Support

Jika ada masalah:
1. Cek dokumentasi di `ROI_GUIDE.md`
2. Lihat logs di terminal
3. Gunakan browser console (F12) untuk debug frontend
4. Hubungi administrator sistem

---

**Last Updated**: 2024-10-24  
**Version**: 2.0.0 (dengan ROI Feature)
