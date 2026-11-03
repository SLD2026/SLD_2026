import cv2

# Masukkan link RTSP Anda di sini (Pastikan angka 101 sesuai dengan lubang colokan NVR)
url_nvr = "rtsp://admin:password12@192.168.99.10:554/Streaming/Channels/101"

print(f"Mencoba menyambung ke: {url_nvr}")
print("Mohon tunggu sebentar...")

# Menggunakan FFmpeg untuk membaca RTSP
cap = cv2.VideoCapture(url_nvr, cv2.CAP_FFMPEG)

if not cap.isOpened():
    print("GAGAL! NVR masih menolak akses (Error 401).")
    print("Solusi wajib: Cabut listrik NVR selama 10 detik sekarang untuk mereset blokir.")
else:
    print("BERHASIL! Tekan tombol 'q' di keyboard untuk menutup jendela video.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Video terputus.")
            break
        
        # Mengecilkan sedikit ukuran layar agar tidak kebesaran di laptop
        frame_kecil = cv2.resize(frame, (800, 600))
        cv2.imshow("Video Langsung NVR", frame_kecil)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()