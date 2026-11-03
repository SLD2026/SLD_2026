import cv2
import json
import time
import datetime
from pathlib import Path
import sys
import numpy as np

sys.path.append(str(Path(__file__).resolve().parent.parent))
from .detector import ObjectDetector
from .behavior_analyzer import BehaviorAnalyzer
from .face_recognizer import FaceRecognizer
from config import VIOLATION_CROP_DIR

class VisionPipeline:
    def __init__(self):
        self.detector = ObjectDetector()
        self.face_recognizer = FaceRecognizer()
        self.cooldowns = {} # Mencegah spam database

    def process_frame(self, camera_id: str, frame, roi_polygon_json: str, db_session):
        if frame is None:
            return None

        roi_polygon = []
        if roi_polygon_json:
            try:
                roi_polygon = json.loads(roi_polygon_json)
            except Exception:
                pass

        # 1. Deteksi YOLO
        person_boxes, trash_boxes = self.detector.detect_and_track(frame)

        # 2. Analisis Perilaku Buang Sampah
        violations = BehaviorAnalyzer.detect_littering(person_boxes, trash_boxes, roi_polygon)

        # 3. Logika Cooldown (Cegah Spam 1 Pelanggaran = Banyak Foto)
        current_time = time.time()
        last_time = self.cooldowns.get(camera_id, 0)
        can_log = (current_time - last_time) > 5.0 # Delay 5 Detik

        if violations and can_log:
            self.cooldowns[camera_id] = current_time 
            
            # Ambil orang pertama yang terdeteksi melanggar pada frame ini
            v = violations[0] 
            px1, py1, px2, py2 = v['person_box']
            
            # Crop gambar untuk disimpan
            h, w, _ = frame.shape
            crop_px1, crop_py1 = max(0, px1-20), max(0, py1-20)
            crop_px2, crop_py2 = min(w, px2+20), min(h, py2+20)
            person_crop = frame[crop_py1:crop_py2, crop_px1:crop_px2]

            if person_crop.size > 0:
                # Ekstrak Wajah
                person_id, sim_score = self.face_recognizer.identify_face(person_crop)

                # Simpan Foto ke Direktori
                timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"VIOLATION_{camera_id}_{timestamp_str}.jpg"
                save_path = VIOLATION_CROP_DIR / filename
                cv2.imwrite(str(save_path), person_crop)

                # Tulis Data ke SQLite
                from backend_api.database.models import ViolationLog
                new_log = ViolationLog(
                    camera_id=camera_id,
                    identified_person_id=person_id,
                    similarity_score=f"{sim_score:.2f}",
                    image_proof_path=f"/static/violations/{filename}"
                )
                db_session.add(new_log)
                db_session.commit()
                print(f"[ALERT] Pelanggaran Tersimpan! ID: {camera_id}")

        # 4. Gambar Overlay Bounding Box
        self._draw_overlays(frame, person_boxes, trash_boxes, roi_polygon, violations)
        return frame

    def _draw_overlays(self, frame, person_boxes, trash_boxes, roi_polygon, violations):
        # Gambar target normal (Orang: Hijau, Sampah: Biru)
        for box in person_boxes:
            x1, y1, x2, y2, t_id = map(int, box)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, "Orang", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        for box in trash_boxes:
            x1, y1, x2, y2, t_id = map(int, box)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.putText(frame, "Sampah", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            
        # Peringatan Visual Pelanggaran (Ubah kotak orang jadi Merah Tebal)
        for v in violations:
            px1, py1, px2, py2 = v['person_box']
            cv2.rectangle(frame, (px1, py1), (px2, py2), (0, 0, 255), 4)
            cv2.putText(frame, "PELANGGARAN!", (px1, py1 - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)