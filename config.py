import os
from pathlib import Path

# --- Trik wajib untuk menembus keamanan NVR Hikvision ---
# Konfigurasi FFMPEG untuk stabilitas stream RTSP dan handle corrupted frames
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
    "rtsp_transport;tcp|"  # TCP lebih stabil dari UDP untuk menghindari packet loss
    "reorder_queue_size;500|"  # Tingkatkan buffer untuk handle frame reordering
    "stimeout;10000000|"  # Socket timeout 10 detik
    "buffer_size;8192000|"  # Buffer 8MB untuk menampung frame burst
    "max_delay;1000000|"  # Max delay 1 detik
    "analyzeduration;2000000|"  # Analisis stream 2 detik
    "probesize;2000000|"  # Probe size 2MB
    "fflags;nobuffer|"  # Disable buffering untuk real-time
    "flags;low_delay|"  # Low latency mode
    "fflags;discardcorrupt"  # PENTING: Discard corrupted frames instead of showing black
)

BASE_DIR = Path(__file__).resolve().parent

# --- Pengaturan Direktori & Database ---
DATABASE_URL = f"sqlite:///{BASE_DIR}/backend_api/database/river_monitor.db"
YOLO_MODEL_PATH = BASE_DIR / "dataset_training/weights/yolo_trash_best.pt"
FACE_EMBEDDINGS_PATH = BASE_DIR / "dataset_training/weights/face_embeddings.npz"

YOLO_CONFIDENCE = 0.65
FACE_MATCH_THRESHOLD = 0.60

VIOLATION_CROP_DIR = BASE_DIR / "frontend/static/violations/"
os.makedirs(VIOLATION_CROP_DIR, exist_ok=True)
os.makedirs(BASE_DIR / "backend_api/database", exist_ok=True)

HOST = "0.0.0.0"
PORT = 8000