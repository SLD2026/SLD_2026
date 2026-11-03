import cv2
import numpy as np
import os
from insightface.app import FaceAnalysis
from pathlib import Path

class FaceRecognizer:
    def __init__(self, db_path="database_wajah"):
        # Gunakan path absolut
        BASE_DIR = Path(__file__).resolve().parent.parent
        self.db_path = BASE_DIR / db_path
        
        try:
            # Menggunakan CPUExecutionProvider saja untuk stabilitas (Face Rec tidak butuh real-time GPU)
            providers = ['CPUExecutionProvider']
        except Exception:
            providers = ['CPUExecutionProvider']
        self.app = FaceAnalysis(name='buffalo_l', providers=providers)
        ctx_id = -1 # -1 untuk CPU
        self.app.prepare(ctx_id=ctx_id, det_size=(640, 640), det_thresh=0.5)

        self.known_embeddings = []
        self.known_names = []

        # Otomatis muat database wajah saat program dinyalakan
        self.load_database()

    def load_database(self):
        """Memuat semua foto dari folder database_wajah"""
        if not self.db_path.exists():
            print(f"[ERROR] Folder database tidak ditemukan di: {self.db_path}")
            return

        print(f"[INFO] Memuat database wajah dari: {self.db_path}")
        count = 0
        for filename in os.listdir(self.db_path):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                # Ambil nama asli dari nama file (Contoh: "Andi_1.jpg" menjadi "Andi")
                name_part = filename.split('_')[0]

                img_path = str(self.db_path / filename)
                img = cv2.imread(img_path)

                if img is not None:
                    faces = self.app.get(img)
                    if len(faces) > 0:
                        # Ambil wajah dengan bbox terbesar
                        faces = sorted(faces, key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)
                        embedding = faces[0].embedding
                        self.known_embeddings.append(embedding)
                        self.known_names.append(name_part)
                        count += 1
                        print(f"[LOADED] Berhasil memuat: {filename} sebagai '{name_part}'")
                    else:
                        print(f"[WARNING] Tidak ada wajah yang terdeteksi di file: {filename}")

        print(f"[INFO] Total {count} referensi wajah berhasil dimuat.")

    def identify_face(self, frame_crop):
        """Mencocokkan crop wajah pelaku dengan database yang sudah dimuat"""
        if frame_crop is None or frame_crop.size == 0:
            return "Wajah Tidak Jelas", 0.0

        faces = self.app.get(frame_crop)

        if len(faces) == 0:
            return "Wajah Tidak Terlihat", 0.0

        # Ambil wajah dengan deteksi skor tertinggi pada crop tersebut
        best_face = max(faces, key=lambda f: f.det_score)
        unknown_embedding = best_face.embedding

        if len(self.known_embeddings) == 0:
            return "Database Kosong", float(best_face.det_score) * 100

        # Hitung kemiripan kosinus (Cosine Similarity) dengan semua foto di database
        similarities = []
        for known_emb in self.known_embeddings:
            # Rumus kemiripan vektor InsightFace
            sim = np.dot(unknown_embedding, known_emb) / (np.linalg.norm(unknown_embedding) * np.linalg.norm(known_emb))
            similarities.append(sim)

        best_match_index = np.argmax(similarities)
        best_similarity = similarities[best_match_index]

        # Tentukan ambang batas kemiripan (Threshold = 0.4 atau 40% kemiripan fitur)
        THRESHOLD = 0.4 

        if best_similarity >= THRESHOLD:
            nama_terdeteksi = self.known_names[best_match_index]
            akurasi = float(best_similarity) * 100
            return nama_terdeteksi, akurasi
        else:
            return "Tidak Dikenal", float(best_similarity) * 100