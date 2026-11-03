from pathlib import Path
import sys

# Mengatur agar folder root proyek terbaca di urutan pertama path Python
root_dir = str(Path(__file__).resolve().parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import cv2
import time
import threading

from backend_api.database.models import SessionLocal, Camera
from core_engine.stream_manager import stream_manager
from core_engine.vision_pipeline import VisionPipeline

from concurrent.futures import ThreadPoolExecutor
import threading

router = APIRouter(tags=["Streaming"])

# === FIX SEGMENTATION FAULT ===
# JANGAN instantiate VisionPipeline di sini (akan crash saat uvicorn startup)
# Gunakan lazy loading dengan function getter
pipeline = None

def get_pipeline():
    """Lazy load VisionPipeline untuk avoid segfault saat uvicorn startup"""
    global pipeline
    if pipeline is None:
        pipeline = VisionPipeline()
        print("[INFO] VisionPipeline lazy-loaded successfully")
    return pipeline
# =============================

# Semaphore GPU untuk membatasi max concurrent inference (RTX 3050 aman di 4 thread simultan)
gpu_semaphore = threading.Semaphore(4)

# Cache ROI di-handle oleh VisionPipeline, DB hanya dibaca jika cache kosong/stale
_db_roi_cache = {}

def _get_camera_rtsp(camera_id: str) -> str:
    db = SessionLocal()
    rtsp_url = ""
    try:
        cam_obj = db.query(Camera).filter(Camera.camera_id == camera_id).first()
        if cam_obj:
            rtsp_url = cam_obj.rtsp_url
    except Exception:
        pass
    finally:
        db.close()
    return rtsp_url

def _get_camera_roi(camera_id: str) -> str:
    now = time.time()
    cached = _db_roi_cache.get(camera_id)
    if cached and now - cached[0] < 5.0: # TTL 5 detik
        return cached[1]

    db = SessionLocal()
    roi_json = None
    try:
        cam_obj = db.query(Camera).filter(Camera.camera_id == camera_id).first()
        roi_json = cam_obj.roi_polygon if cam_obj else None
    except Exception:
        pass
    finally:
        db.close()
    _db_roi_cache[camera_id] = (now, roi_json)
    return roi_json

def generate_frames(camera_id: str):
    """Generator frame video real-time yang memproses AI YOLO dan kotak pembatas"""
    skip_count = 0
    last_frame = None
    consecutive_errors = 0
    while True:
        success, frame = stream_manager.get_frame(camera_id)
        if not success or frame is None:
            consecutive_errors += 1
            if consecutive_errors > 30:
                # Re-initialize stream jika terlalu lama gagal
                try:
                    stream_manager.stop_stream(camera_id)
                    stream_manager.add_stream(camera_id, _get_camera_rtsp(camera_id))
                except:
                    pass
                consecutive_errors = 0
            time.sleep(0.05)
            continue
        consecutive_errors = 0

        # Skip frames: proses AI tiap 6 frame untuk mengurangi beban GPU/CPU
        skip_count += 1
        if skip_count % 6 != 0:
            out_frame = last_frame if last_frame is not None else frame
            # Jangan encode jika frame sama untuk mengurangi bandwidth
            if out_frame is not None:
                ret, buffer = cv2.imencode('.jpg', out_frame, [cv2.IMWRITE_JPEG_QUALITY, 65, cv2.IMWRITE_JPEG_OPTIMIZE, 1])
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.033)
            continue

        # Ambil ROI dari cache
        roi_json = _get_camera_roi(camera_id)

        # Proses frame dengan batasan konkurensi GPU
        acquired = gpu_semaphore.acquire(blocking=False)
        if acquired:
            db = SessionLocal()
            try:
                processed_frame = get_pipeline().process_frame(camera_id, frame, roi_json, db)
                if processed_frame is not None:
                    frame = processed_frame
            except Exception as e:
                # Jangan crash stream, gunakan frame asli
                pass
            finally:
                db.close()
                gpu_semaphore.release()
        # Jika GPU sedang penuh, tetap pakai frame asli untuk menjaga stream tetap hidup

        if frame is not None:
            import numpy as np
            last_frame = np.ascontiguousarray(frame)

        if frame is None:
            continue

        # Gunakan frame terbaru, fallback ke last_frame jika encode gagal
        try:
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 65, cv2.IMWRITE_JPEG_OPTIMIZE, 1])
            if not ret:
                # Coba pakai last_frame
                if last_frame is not None:
                    ret, buffer = cv2.imencode('.jpg', last_frame, [cv2.IMWRITE_JPEG_QUALITY, 65])
                if not ret:
                    continue
            last_frame = frame.copy()
        except Exception:
            if last_frame is not None:
                try:
                    ret, buffer = cv2.imencode('.jpg', last_frame, [cv2.IMWRITE_JPEG_QUALITY, 65])
                    if not ret:
                        continue
                except Exception:
                    continue
            else:
                continue

        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@router.get("/api/stream/{camera_id}")
def video_stream(camera_id: str):
    """Endpoint utama streaming video CCTV ber-AI untuk dashboard"""
    return StreamingResponse(
        generate_frames(camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )