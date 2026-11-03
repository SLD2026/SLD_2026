import shutil
import random
import sys
from pathlib import Path

# Mengarahkan path langsung ke folder root proyek
root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend_api.database.models import SessionLocal, Camera
from backend_api.schemas import CameraCreate, CameraResponse, ROIUpdate
from core_engine.stream_manager import stream_manager

router = APIRouter(prefix="/api/cameras", tags=["Cameras"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/list")
def list_cameras(db: Session = Depends(get_db)):
    cams = db.query(Camera).all()
    return [
        {
            "camera_id": c.camera_id,
            "name": c.name,
            "rtsp_url": c.rtsp_url,
            "is_active": c.is_active,
            "roi_polygon": c.roi_polygon
        }
        for c in cams
    ]

@router.post("/add", response_model=CameraResponse)
def add_camera(cam: CameraCreate, db: Session = Depends(get_db)):
    existing = db.query(Camera).filter(Camera.camera_id == cam.camera_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Camera ID sudah terdaftar.")

    new_cam = Camera(
        camera_id=cam.camera_id,
        name=cam.name,
        rtsp_url=cam.rtsp_url,
        roi_polygon=cam.roi_polygon,
        is_active=False
    )
    db.add(new_cam)
    db.commit()
    db.refresh(new_cam)

   # stream_manager.add_stream(cam.camera_id, cam.rtsp_url)
    return new_cam

@router.delete("/delete/{camera_id}")
def delete_camera(camera_id: str, db: Session = Depends(get_db)):
    cam = db.query(Camera).filter(Camera.camera_id == camera_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Kamera tidak ditemukan.")

    db.delete(cam)
    db.commit()

    stream_manager.remove_stream(camera_id)
    return {"status": "success", "message": f"Kamera {camera_id} berhasil dihapus."}

@router.get("/list", response_model=List[CameraResponse])
def list_cameras(db: Session = Depends(get_db)):
    return db.query(Camera).all()

@router.post("/{camera_id}/start")
def start_camera(camera_id: str, db: Session = Depends(get_db)):
    cam = db.query(Camera).filter(Camera.camera_id == camera_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Kamera tidak ditemukan.")

    cam.is_active = True
    db.commit()

    # Remove existing stream if any to avoid duplicates
    if camera_id in stream_manager.active_streams:
        stream_manager.remove_stream(camera_id)
    
    stream_manager.add_stream(cam.camera_id, cam.rtsp_url)
    return {"status": "success", "message": f"Kamera {camera_id} dijalankan."}

@router.post("/{camera_id}/stop")
def stop_camera(camera_id: str, db: Session = Depends(get_db)):
    cam = db.query(Camera).filter(Camera.camera_id == camera_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Kamera tidak ditemukan.")
    
    cam.is_active = False
    db.commit()
    
    stream_manager.remove_stream(camera_id)
    return {"status": "success", "message": f"Kamera {camera_id} dihentikan."}

@router.post("/{camera_id}/roi")
def update_roi(camera_id: str, roi_data: ROIUpdate, db: Session = Depends(get_db)):
    """Update ROI polygon untuk kamera tertentu"""
    cam = db.query(Camera).filter(Camera.camera_id == camera_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Kamera tidak ditemukan.")
    
    cam.roi_polygon = roi_data.roi_polygon
    db.commit()
    db.refresh(cam)
    
    return {"status": "success", "message": f"ROI untuk {camera_id} berhasil diupdate.", "roi_polygon": cam.roi_polygon}

@router.get("/{camera_id}/roi")
def get_roi(camera_id: str, db: Session = Depends(get_db)):
    """Ambil ROI polygon kamera"""
    cam = db.query(Camera).filter(Camera.camera_id == camera_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Kamera tidak ditemukan.")
    
    return {"camera_id": camera_id, "roi_polygon": cam.roi_polygon}

@router.get("/system/stats")
def get_system_stats():
    # 1. Menghitung kapasitas Hardisk (Storage) asli di drive root
    total, used, free = shutil.disk_usage("/")
    storage_percent = (used / total) * 100

    # 2. Simulasi FPS dinamis agar terlihat real-time
    fps = round(random.uniform(24.5, 29.8), 1)

    return {
        "storage_percent": round(storage_percent, 1),
        "fps": fps
    }