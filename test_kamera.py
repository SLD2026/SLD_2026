import cv2
import os

# TRIK JITU: Paksa OpenCV untuk menggunakan protokol TCP seperti VLC
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

# Masukkan password yang baru saja Anda buat untuk akun kamera_ai
url_nvr = "rtsp://kamera_ai:Password12@192.168.99.10:554/Streaming/Channels/101"

print(f"Mencoba menyambung ke: {url_nvr} (Mode TCP Terkunci)")
print("Mohon tunggu sebentar...")

# Buka kamera menggunakan FFmpeg
cap = cv2.VideoCapture(url_nvr, cv2.CAP_FFMPEG)

if not cap.isOpened():
    print("GAGAL! Python masih tidak bisa membaca link.")
else:
    print("BERHASIL! Tekan tombol 'q' di keyboard untuk menutup jendela video.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Video terputus.")
            break
        
        # Mengecilkan sedikit ukuran layar agar pas di laptop
        frame_kecil = cv2.resize(frame, (800, 600))
        cv2.imshow("Video Langsung NVR", frame_kecil)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()