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

        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 2)
        self.capture.set(cv2.CAP_PROP_FPS, 15)
        
        self.current_frame = None
        self.status = False
        self.is_running = True
        
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        consecutive_failures = 0
        while self.is_running:
            try:
                if self.capture.isOpened():
                    ret, frame = self.capture.read()
                    if ret and frame is not None and frame.size > 0:
                        # Validasi frame dasar
                        if len(frame.shape) == 3 and frame.shape[2] == 3:
                            self.status = True
                            self.current_frame = frame
                            consecutive_failures = 0
                        else:
                            consecutive_failures += 1
                            if consecutive_failures > 5:
                                self.status = False
                                self.capture.release()
                    else:
                        consecutive_failures += 1
                        if consecutive_failures > 5:
                            self.status = False
                            self.capture.release()
                            time.sleep(1)
                        else:
                            time.sleep(0.05)
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
        if self.status and self.current_frame is not None:
            return True, self.current_frame.copy()
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