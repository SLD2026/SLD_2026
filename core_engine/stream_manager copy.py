import cv2
import threading
import time

class RTSPStreamReader:
    def __init__(self, camera_id: str, rtsp_url: str):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        
        # Cek apakah input berupa angka (Webcam) atau teks link (RTSP)
        if str(self.rtsp_url).isdigit():
            self.video_source = int(self.rtsp_url)
            self.capture = cv2.VideoCapture(self.video_source, cv2.CAP_DSHOW) 
        else:
            self.video_source = self.rtsp_url
            self.capture = cv2.VideoCapture(self.video_source, cv2.CAP_FFMPEG)
            
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        self.current_frame = None
        self.status = False
        self.is_running = True
        
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        while self.is_running:
            try:
                if self.capture.isOpened():
                    ret, frame = self.capture.read()
                    if ret and frame is not None:
                        self.status = True
                        self.current_frame = frame
                    else:
                        self.status = False
                        self.capture.release()
                        time.sleep(2)
                        
                        if not self.is_running:
                            break
                            
                        if str(self.video_source).isdigit():
                            self.capture = cv2.VideoCapture(self.video_source, cv2.CAP_DSHOW)
                        else:
                            self.capture = cv2.VideoCapture(self.video_source, cv2.CAP_FFMPEG)
                else:
                    time.sleep(0.1)
            except Exception as e:
                # Menangkap error C++ OpenCV agar thread tidak crash/mati total
                self.status = False
                time.sleep(1)

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