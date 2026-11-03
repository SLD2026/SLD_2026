import cv2
import numpy as np

class BehaviorAnalyzer:
    @staticmethod
    def _point_in_polygon(pt, polygon):
        if not polygon or len(polygon) < 3:
            return True
        pts = np.array(polygon, dtype=np.int32)
        # cv2.pointPolygonTest mengembalikan >0 jika di dalam
        res = cv2.pointPolygonTest(pts, pt, False)
        return res >= 0

    @staticmethod
    def detect_littering(person_boxes, trash_boxes, roi_polygon):
        violations = []
        # Jika ROI kosong, anggap semua area valid
        roi_exists = bool(roi_polygon and len(roi_polygon) >= 3)
        for t_box in trash_boxes:
            tx1, ty1, tx2, ty2, t_id = t_box
            trash_center = (int((tx1 + tx2) / 2), int((ty1 + ty2) / 2))
            
            # 1. Filter utama: sampah harus berada di dalam ROI
            if roi_exists and not BehaviorAnalyzer._point_in_polygon(trash_center, roi_polygon):
                continue

            # 2. Cek apakah sampah sedang dipegang oleh seseorang
            is_held = False
            closest_person = None
            min_dist = float('inf')

            for p_box in person_boxes:
                px1, py1, px2, py2, p_id = p_box
                person_center = (int((px1 + px2) / 2), int((py1 + py2) / 2))
                dist = np.sqrt((trash_center[0] - person_center[0])**2 + (trash_center[1] - person_center[1])**2)

                if dist < min_dist:
                    min_dist = dist
                    closest_person = p_box

                # Hitung Intersection over Area (IoA) untuk cek apakah sedang dipegang
                overlap_x = max(0, min(px2, tx2) - max(px1, tx1))
                overlap_y = max(0, min(py2, ty2) - max(py1, ty1))
                overlap_area = overlap_x * overlap_y
                trash_area = (tx2 - tx1) * (ty2 - ty1)
                
                if trash_area > 0 and (overlap_area / trash_area) > 0.2:
                    is_held = True
                    break # Jika sedang dipegang, jangan anggap sebagai sampah yang dibuang

            # 3. Jika tidak dipegang (berarti dilempar/diletakkan di ROI), catat sebagai pelanggaran
            if not is_held:
                violations.append({
                    "person_box": [int(closest_person[0]), int(closest_person[1]), int(closest_person[2]), int(closest_person[3])] if closest_person is not None else None,
                    "trash_box": [int(tx1), int(ty1), int(tx2), int(ty2)],
                    "trash_center": trash_center
                })
        return violations