import os
import sys

# === FIX SEGMENTATION FAULT ===
# Set environment variables SEBELUM import library lain
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

# Disable OpenCV threading untuk mencegah konflik dengan uvicorn
os.environ['OPENCV_OPENCL_RUNTIME'] = ''
os.environ['OPENCV_OPENCL_DEVICE'] = 'disabled'

# === SUPPRESS H.264 DECODER ERROR MESSAGES ===
# Menghilangkan spam error "[h264 @ ...] error while decoding MB"
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'  # Only show critical errors
os.environ['OPENCV_FFMPEG_LOGLEVEL'] = '-8'  # Quiet mode for FFMPEG
os.environ['OPENCV_VIDEOIO_DEBUG'] = '0'  # Disable debug output
# =========================================

# Set multiprocessing start method ke 'spawn' untuk Linux
import multiprocessing
try:
    multiprocessing.set_start_method('spawn', force=True)
except RuntimeError:
    pass  # Already set
# =============================

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from contextlib import asynccontextmanager

from config import HOST, PORT, BASE_DIR

# --- IMPORT MODUL ANDA ---
from backend_api.database.models import init_db, SessionLocal, Camera
from backend_api.routers import camera_routes, stream_routes
from core_engine.stream_manager import stream_manager
# JANGAN import FaceRecognizer di sini - akan di-import lazy di dalam lifespan()
# -----------------------

# Global variable untuk face system (akan di-load di lifespan)
face_system = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Inisialisasi Database SQLite
    print("[INFO] Menginisialisasi Database...")
    init_db()

    # --- 2. FACE RECOGNIZER AKAN DI-LOAD ON-DEMAND (tidak di sini) ---
    # FaceRecognizer akan di-load otomatis saat pertama kali dibutuhkan
    # oleh VisionPipeline.get_pipeline() untuk avoid blocking uvicorn startup
    print("[INFO] ✓ FaceRecognizer akan di-load on-demand saat dibutuhkan")
    # -----------------------------------------------

    # 3. RESET SEMUA KAMERA KE STATUS STOP SAAT STARTUP
    print("[INFO] Reset semua kamera ke status STOP...")
    db = SessionLocal()
    try:
        # Stop semua stream yang mungkin masih berjalan
        stream_manager.stop_all()
        
        # Update database: set semua kamera ke is_active=False
        db.query(Camera).update({Camera.is_active: False})
        db.commit()
        
        print("[INFO] Semua kamera telah di-reset ke status STOP")
    except Exception as e:
        print(f"[WARNING] Gagal reset kamera: {e}")
    finally:
        db.close()

    print("\n" + "="*50)
    print("🚀 SERVER BERHASIL MENYALA!")
    print("👉 KLIK LINK INI UNTUK DIBUKA DI CHROME: http://127.0.0.1:8000")
    print("="*50 + "\n")

    yield  # Server berjalan

    # 4. Cleanup saat server dimatikan
    print("[INFO] Menjeda semua stream dan membersihkan database...")
    try:
        # Stop semua stream
        stream_manager.stop_all()
        
        # Update database: set semua kamera ke is_active=False
        db = SessionLocal()
        db.query(Camera).update({Camera.is_active: False})
        db.commit()
        db.close()
        
        print("[INFO] Semua kamera telah di-set ke status STOP")
    except Exception as e:
        print(f"[ERROR] Gagal cleanup: {e}")

app = FastAPI(title="River Violation Monitoring System", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=BASE_DIR / "frontend/static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "frontend/templates")

app.include_router(camera_routes.router)
app.include_router(stream_routes.router)

@app.get("/")
def render_index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/cameras")
def render_cameras(request: Request):
    return templates.TemplateResponse(request=request, name="cameras.html")

@app.get("/logs")
def render_logs(request: Request):
    return templates.TemplateResponse(request=request, name="logs.html")

@app.get("/roi")
def render_roi_editor(request: Request):
    return templates.TemplateResponse(request=request, name="roi_editor_final.html")

if __name__ == "__main__":
    # Gunakan loop='asyncio' dan limit_concurrency untuk stabilitas
    uvicorn.run(
        "main:app", 
        host=HOST, 
        port=PORT, 
        reload=False,
        workers=1,  # Single worker untuk avoid fork issues
        loop='asyncio',
        log_level='info',
        access_log=True
    )