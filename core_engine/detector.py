from ultralytics import YOLO
import sys
import cv2
import math
import time
import threading  # Agar video tidak macet saat kirim pesan
import os         # Untuk membuat folder otomatis
from pathlib import Path

# IMPORT FUNGSI TELEGRAM
from tele_bot import kirim_peringatan_telegram

sys.path.append(str(Path(__file__).resolve().parent.parent))

class ObjectDetector:
    def __init__(self):
        # KITA KEMBALI PAKAI 1 MODEL BAWAAN YOLO SEMENTARA WAKTU
        # Model ini sudah bisa mendeteksi Orang (0), Botol (39), dan Gelas (41)
        self.model = YOLO("yolov8s.pt")
        try:
            import torch
            if torch.cuda.is_available():
                self.model.to('cuda')
            else:
                self.model.to('cpu')
        except Exception:
            pass
        
        self.last_alert = {} 

    def detect_and_track(self, frame):
        try:
            if frame is None or not hasattr(frame, 'shape'):
                return [], []
            
            # Gunakan bytetrack.yaml untuk menghindari error GMC pada tracking
            results = self.model.track(frame, persist=True, device=0, verbose=False, conf=0.15, tracker="bytetrack.yaml")[0]

            person_boxes, trash_boxes = [], []

            if results.boxes is not None and results.boxes.id is not None:
                boxes = results.boxes.xyxy.cpu().numpy()
                track_ids = results.boxes.id.cpu().numpy()
                clss = results.boxes.cls.cpu().numpy()

                for box, track_id, cls in zip(boxes, track_ids, clss):
                    try:
                        if int(cls) == 0:  # Manusia
                            person_boxes.append([*box, track_id])
                        # COCO Dataset classes untuk sampah:
                        # 39: bottle, 41: cup, 42: fork, 43: knife, 44: spoon, 45: bowl, 47: apple, 49: orange, 50: broccoli, 51: carrot, 52: hot dog, 53: pizza, 54: donut, 55: cake
                        elif int(cls) in [39, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56]:  # Jenis sampah/objek lain
                            trash_boxes.append([*box, track_id])
                    except Exception:
                        continue

            return person_boxes, trash_boxes
        except Exception as e:
            # Return empty boxes on error, don't crash
            return [], []