import cv2
import threading
import time
import platform

class RTSPStreamReader:
    def __init__(self, camera_id: str, rtsp_url: str):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url

        # Cek apakah input berupa angka (Webcam) atau teks link (RTSP)
        # Trim whitespace untuk handle edge cases
        rtsp_url_str = str(self.rtsp_url).strip()
        if rtsp_url_str.isdigit():
            self.video_source = int(rtsp_url_str)
            # Gunakan backend yang sesuai dengan OS
            system_platform = platform.system().lower()
            if system_platform == 'windows':
                backend = cv2.CAP_DSHOW
            elif system_platform == 'linux':
                backend = cv2.CAP_V4L2
            else:
                backend = cv2.CAP_ANY
            self.capture = cv2.VideoCapture(self.video_source, backend)
        else:
            self.video_source = self.rtsp_url
            self.capture = cv2.VideoCapture(self.video_source, cv2.CAP_FFMPEG)

        # === OPTIMASI UNTUK HANDLE CORRUPTED H.264 FRAMES ===
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Buffer minimal untuk real-time
        self.capture.set(cv2.CAP_PROP_FPS, 10)  # Turunkan FPS untuk stabilitas
        
        # Tambahan properti untuk handle Hikvision stream
        try:
            # Drop corrupted frames instead of blocking
            self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))
        except:
            pass
        # ===================================================
        
        self.current_frame = None
        self.last_good_frame = None  # Backup frame untuk saat ada corrupted frame
        self.status = False
        self.is_running = True
        self.frame_count = 0
        self.corrupted_count = 0

        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        consecutive_failures = 0
        skip_corrupted_frames = 0
        
        while self.is_running:
            try:
                if self.capture.isOpened():
                    ret, frame = self.capture.read()
                    
                    # === HANDLE CORRUPTED H.264 FRAMES ===
                    if ret and frame is not None and frame.size > 0:
                        # Validasi frame lebih ketat
                        if len(frame.shape) == 3 and frame.shape[2] == 3:
                            # Cek apakah frame valid (bukan semua hitam/rusak)
                            mean_brightness = frame.mean()
                            
                            # Frame valid jika brightness antara 1-254 (bukan pure black/white)
                            if 1 < mean_brightness < 254:
                                self.status = True
                                self.current_frame = frame
                                self.last_good_frame = frame.copy()  # Backup
                                self.frame_count += 1
                                consecutive_failures = 0
                                skip_corrupted_frames = 0
                            else:
                                # Frame corrupted (all black/white), gunakan last good frame
                                self.corrupted_count += 1
                                skip_corrupted_frames += 1
                                
                                # Jika ada backup frame, pakai itu
                                if self.last_good_frame is not None and skip_corrupted_frames < 10:
                                    self.current_frame = self.last_good_frame
                                    self.status = True
                                else:
                                    consecutive_failures += 1
                                    
                                # Log setiap 50 corrupted frames
                                if self.corrupted_count % 50 == 0:
                                    print(f"[WARN] {self.camera_id}: {self.corrupted_count} corrupted frames detected (using last good frame)")
                        else:
                            consecutive_failures += 1
                            if consecutive_failures > 5:
                                self.status = False
                    else:
                        consecutive_failures += 1
                        if consecutive_failures > 10:
                            self.status = False
                            self.capture.release()
                            time.sleep(1)
                        else:
                            time.sleep(0.05)
                    # ===================================
                else:
                    time.sleep(0.1)
            except Exception as e:
                # Menangkap error C++ OpenCV agar thread tidak crash/mati total
                self.status = False
                consecutive_failures += 1
                time.sleep(0.5)
                # Reconnect strategy
                if consecutive_failures >= 3:
                    try:
                        self.capture.release()
                    except:
                        pass
                    time.sleep(1)
                    if str(self.video_source).strip().isdigit():
                        system_platform = platform.system().lower()
                        backend = cv2.CAP_V4L2 if system_platform == 'linux' else cv2.CAP_ANY
                        self.capture = cv2.VideoCapture(self.video_source, backend)
                    else:
                        self.capture = cv2.VideoCapture(self.video_source, cv2.CAP_FFMPEG)
                    consecutive_failures = 0

    def get_latest_frame(self):
        # Prioritaskan current frame, fallback ke last good frame
        if self.status and self.current_frame is not None:
            return True, self.current_frame.copy()
        elif self.last_good_frame is not None:
            # Stream sempat terputus, tapi kita punya backup frame
            return True, self.last_good_frame.copy()
        return False, None

    def stop(self):
        self.is_running = False
        
        def release_camera_safely():
            try:
                if self.capture.isOpened():
                    self.capture.release()
            except Exception:
                pass

        threading.Thread(target=release_camera_safely, daemon=True).start()

class StreamManager:
    def __init__(self):
        self.active_streams = {}
        self.lock = threading.Lock()

    def add_stream(self, camera_id: str, rtsp_url: str):
        with self.lock:
            if camera_id not in self.active_streams:
                self.active_streams[camera_id] = RTSPStreamReader(camera_id, rtsp_url)

    def remove_stream(self, camera_id: str):
        with self.lock:
            if camera_id in self.active_streams:
                self.active_streams[camera_id].stop()
                del self.active_streams[camera_id]

    def get_frame(self, camera_id: str):
        with self.lock:
            if camera_id in self.active_streams:
                return self.active_streams[camera_id].get_latest_frame()
            return False, None

    def stop_all(self):
        with self.lock:
            for stream in self.active_streams.values():
                stream.stop()
            self.active_streams.clear()

stream_manager = StreamManager()