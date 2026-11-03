import cv2
import json
import time
import datetime
import os
from pathlib import Path
import sys
import numpy as np

sys.path.append(str(Path(__file__).resolve().parent.parent))
from .detector import ObjectDetector
from .behavior_analyzer import BehaviorAnalyzer
# JANGAN import FaceRecognizer di top-level (cause segfault at uvicorn startup)
# Will be lazy-loaded in VisionPipeline.__init__()
from config import VIOLATION_CROP_DIR, BASE_DIR

class VideoRecorder:
    def __init__(self, filename, fps=10):
        # Standardisasi resolusi VideoWriter agar stabil
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.out = None
        try:
            self.out = cv2.VideoWriter(filename, fourcc, fps, (640, 480))
            self.active = True
        except Exception as e:
            print(f"[VIDEO REC INIT ERROR] {e}")
            self.active = False
        self.start_time = time.time()
        self.duration = 5 # seconds
        self.last_frame_size = (640, 480)

    def write(self, frame):
        if not self.active or self.out is None:
            return

        try:
            # Resize frame ke resolusi standar untuk mencegah segfault
            if hasattr(frame, 'shape') and len(frame.shape) == 3:
                if frame.shape[0] != self.last_frame_size[1] or frame.shape[1] != self.last_frame_size[0]:
                    frame = cv2.resize(frame, self.last_frame_size)
                self.out.write(frame)
        except Exception as e:
            # Jangan crash, coba lanjut
            pass

        if time.time() - self.start_time > self.duration:
            self.active = False
            try:
                self.out.release()
            except:
                pass

class VisionPipeline:
    def __init__(self):
        self.detector = ObjectDetector()
        
        # === FIX SEGMENTATION FAULT ===
        # Lazy load FaceRecognizer untuk avoid crash saat uvicorn startup
        self.face_recognizer = None
        try:
            print("[INFO] VisionPipeline: Lazy-loading FaceRecognizer...")
            from .face_recognizer import FaceRecognizer
            self.face_recognizer = FaceRecognizer()
            print("[INFO] VisionPipeline: FaceRecognizer loaded successfully")
        except Exception as e:
            print(f"[WARNING] VisionPipeline: Failed to load FaceRecognizer: {e}")
            self.face_recognizer = None
        # =============================
        
        self.cooldowns = {} # Mencegah spam database
        self._roi_cache = {}  # camera_id -> (timestamp, polygon_json)
        self._roi_ttl = 10.0
        self.active_recordings = {} # camera_id -> VideoRecorder

    def _get_roi_polygon(self, camera_id, roi_polygon_json):
        # Gunakan cache internal untuk mengurangi parse berulang
        now = time.time()
        cached = self._roi_cache.get(camera_id)
        if cached and now - cached[0] < self._roi_ttl:
            return cached[1]
        # Parse dari input
        roi_polygon = []
        if roi_polygon_json:
            try:
                roi_polygon = json.loads(roi_polygon_json)
            except Exception:
                pass
        self._roi_cache[camera_id] = (now, roi_polygon)
        return roi_polygon

    def process_frame(self, camera_id: str, frame, roi_polygon_json: str, db_session):
        if frame is None or not isinstance(frame, np.ndarray):
            return frame
        
        # Validasi frame untuk mencegah error decoding
        if len(frame.shape) != 3 or frame.shape[2] != 3:
            return frame
        
        # Guard against empty/corrupt frames
        if frame.size == 0:
            return frame

        try:
            # --- VIDEO RECORDING ---
            if camera_id in self.active_recordings and self.active_recordings[camera_id].active:
                self.active_recordings[camera_id].write(frame)
        except Exception as e:
            # Jangan crash jika recording error
            pass

        roi_polygon = self._get_roi_polygon(camera_id, roi_polygon_json)

        # Downscale untuk performa stabil 8 stream
        try:
            h, w = frame.shape[:2]
            if h <= 0 or w <= 0:
                return frame
            max_w = 960
            if w > max_w:
                scale = max_w / w
                new_w = max_w
                new_h = int(h * scale)
                frame_small = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
            else:
                frame_small = frame
                new_w, new_h = w, h

            # 1. Deteksi YOLO pada frame kecil
            person_boxes, trash_boxes = self.detector.detect_and_track(frame_small)
        except Exception as e:
            # Jika error processing, kembalikan frame asli tanpa overlay
            return frame

        # 2. Analisis Perilaku Buang Sampah
        violations = BehaviorAnalyzer.detect_littering(person_boxes, trash_boxes, roi_polygon)

        # 3. Logika Cooldown (Cegah Spam 1 Pelanggaran = Banyak Foto)
        current_time = time.time()
        last_time = self.cooldowns.get(camera_id, 0)
        can_log = (current_time - last_time) > 5.0 # Delay 5 Detik

        if violations and can_log:
            self.cooldowns[camera_id] = current_time

            # --- VIDEO RECORDING START ---
            try:
                if camera_id not in self.active_recordings or not self.active_recordings[camera_id].active:
                    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    # Ensure the directory exists
                    rec_dir = BASE_DIR / "frontend/static/violations/"
                    os.makedirs(rec_dir, exist_ok=True)
                    record_path = rec_dir / f"record_{camera_id}_{timestamp_str}.mp4"

                    self.active_recordings[camera_id] = VideoRecorder(str(record_path))
                    self.active_recordings[camera_id].write(frame)
            except Exception as e:
                print(f"[RECORDING ERROR] {e}")

            # --- SCREENSHOT FULL FRAME ---
            timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"VIOLATION_{camera_id}_{timestamp_str}.jpg"
            save_path = VIOLATION_CROP_DIR / filename
            cv2.imwrite(str(save_path), frame) # Save full frame

            # --- FACE RECOGNITION (RUN ON ALL PEOPLE) ---
            identified_person = "Tidak Dikenali"
            for v in violations:
                if v['person_box']:
                    px1, py1, px2, py2 = v['person_box']
                    # Map back to original frame size if downscaled
                    scale_x = w / new_w
                    scale_y = h / new_h
                    px1, py1, px2, py2 = int(px1 * scale_x), int(py1 * scale_y), int(px2 * scale_x), int(py2 * scale_y)
                    
                    # Increase crop area
                    crop_px1, crop_py1 = max(0, px1-50), max(0, py1-50)
                    crop_px2, crop_py2 = min(w, px2+50), min(h, py2+50)
                    person_crop = frame[crop_py1:crop_py2, crop_px1:crop_px2]
                    
                    if person_crop.size > 0:
                        person_id, sim_score = self.face_recognizer.identify_face(person_crop)
                        if person_id != "Tidak Dikenali":
                            identified_person = person_id
                            break
            
            # --- LOG TO DB ---
            from backend_api.database.models import ViolationLog
            new_log = ViolationLog(
                camera_id=camera_id,
                identified_person_id=identified_person,
                similarity_score="0.0", 
                image_proof_path=f"/static/violations/{filename}"
            )
            db_session.add(new_log)
            db_session.commit()
            print(f"[ALERT] Pelanggaran Tersimpan! ID: {camera_id}, Pelaku: {identified_person}")

            # --- TELEGRAM (asynchronous to prevent blocking) ---
            from tele_bot import kirim_peringatan_telegram
            import threading
            try:
                threading.Thread(target=kirim_peringatan_telegram, args=(str(save_path), identified_person), daemon=True).start()
                print(f"[TELEGRAM] Notifikasi dikirim ke {identified_person} (asynchronous)")
            except Exception as e:
                print(f"[TELEGRAM ERROR] Gagal mengirim notifikasi: {e}")
            
        # 4. Gambar Overlay Bounding Box
        self._draw_overlays(frame, person_boxes, trash_boxes, roi_polygon, violations)
        return frame

    def _draw_overlays(self, frame, person_boxes, trash_boxes, roi_polygon, violations):
        try:
            if frame is None or not isinstance(frame, np.ndarray):
                return
            h, w = frame.shape[:2]
            if h <= 0 or w <= 0 or len(frame.shape) != 3:
                return
            # Hitung faktor skala untuk mapping kembali ke frame asli
            # Kita perlu tahu ukuran 'frame_small' yang digunakan untuk deteksi
            max_w = 960
            scale_x, scale_y = 1.0, 1.0
            if w > max_w:
                scale = max_w / w
                new_w = max_w
                new_h = int(h * scale)
                scale_x = w / new_w
                scale_y = h / new_h
        except Exception:
            return

        # 1. Gambar ROI Polygon HANYA GARIS TEPI
        if roi_polygon and len(roi_polygon) >= 3:
            try:
                pts = np.array(roi_polygon, np.int32)
                if pts.shape[0] >= 3:
                    pts = pts.reshape((-1, 1, 2))
                    cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 255), thickness=2)
                    cv2.putText(frame, "ROI", (int(pts[0][0][0]), int(pts[0][0][1]) - 5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            except Exception:
                pass

        # 2. Gambar target normal (Orang: Hijau, Sampah: Biru)
        for box in person_boxes:
            try:
                x1, y1, x2, y2, t_id = map(int, box[:5])
                x1, y1, x2, y2 = int(x1*scale_x), int(y1*scale_y), int(x2*scale_x), int(y2*scale_y)
                if 0 <= x1 < w and 0 <= y1 < h and 0 <= x2 < w and 0 <= y2 < h:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, "Orang", (x1, max(0, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            except Exception:
                pass

        for box in trash_boxes:
            try:
                x1, y1, x2, y2, t_id = map(int, box[:5])
                x1, y1, x2, y2 = int(x1*scale_x), int(y1*scale_y), int(x2*scale_x), int(y2*scale_y)
                if 0 <= x1 < w and 0 <= y1 < h and 0 <= x2 < w and 0 <= y2 < h:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    cv2.putText(frame, "Sampah", (x1, max(0, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            except Exception:
                pass

        # 3. Peringatan Visual Pelanggaran
        for v in violations:
            try:
                tx1, ty1, tx2, ty2 = map(int, v['trash_box'])
                tx1, ty1, tx2, ty2 = int(tx1*scale_x), int(ty1*scale_y), int(tx2*scale_x), int(ty2*scale_y)

                # Jika ada orang yang terkait
                if v['person_box']:
                    px1, py1, px2, py2 = map(int, v['person_box'])
                    px1, py1, px2, py2 = int(px1*scale_x), int(py1*scale_y), int(px2*scale_x), int(py2*scale_y)

                    if 0 <= px1 < w and 0 <= py1 < h:
                        cv2.rectangle(frame, (px1, py1), (px2, py2), (0, 0, 255), 4)
                        cv2.putText(frame, "PELANGGARAN!", (px1, max(0, py1 - 30)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)
                        person_center = ((px1 + px2) // 2, (py1 + py2) // 2)
                        trash_center = ((tx1 + tx2) // 2, (ty1 + ty2) // 2)
                        cv2.line(frame, person_center, trash_center, (0, 0, 255), 2)
                else:
                    # Jika tidak ada orang terdeteksi dekat
                    if 0 <= tx1 < w and 0 <= ty1 < h:
                        cv2.rectangle(frame, (tx1, ty1), (tx2, ty2), (0, 0, 255), 4)
                        cv2.putText(frame, "SAMPAH DI ROI!", (tx1, max(0, ty1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)
            except Exception:
                pass