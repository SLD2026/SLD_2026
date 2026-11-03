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
from core_engine.face_recognizer import FaceRecognizer # <-- 1. Import FaceRecognizer di sini
# -----------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Inisialisasi Database SQLite
    print("[INFO] Menginisialisasi Database...")
    init_db()

    # --- 2. INISIALISASI FACE RECOGNIZER DI SINI ---
    print("[INFO] Memuat sistem pengenalan wajah...")
    try:
        global face_system
        face_system = FaceRecognizer() # Otomatis meload folder database_wajah
    except Exception as e:
        print(f"[WARNING] Gagal memuat FaceRecognizer: {e}")
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
    uvicorn.run("main:app", host=HOST, port=PORT, reload=False)