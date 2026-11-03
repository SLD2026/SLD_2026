import os
from pathlib import Path

# --- Trik wajib untuk menembus keamanan NVR Hikvision ---
# Menambah stimeout dan reorder_queue_size untuk stabilitas stream RTSP
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp|reorder_queue_size;100|stimeout;5000000|buffer_size;2048000|analyzeduration;5000000|probesize;5000000|max_delay;500000"

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