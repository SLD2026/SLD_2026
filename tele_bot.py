import requests

def kirim_peringatan_telegram(foto_path, nama_pelaku="Tidak Dikenal"):
    # Masukkan Token dan Chat ID Anda di sini
    TOKEN = "8932628687:AAEJpZVdIc1i_b4YKruEdpkPS1fpa13rMQY"
    CHAT_ID = "-5233880846"
    
    pesan = f"🚨 PERINGATAN PELANGGARAN!\n\nSistem memantau aktivitas membuang sampah ke sungai.\nPelaku teridentifikasi: {nama_pelaku}"
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    
    try:
        with open(foto_path, 'rb') as foto:
            payload = {'chat_id': CHAT_ID, 'caption': pesan}
            files = {'photo': foto}
            response = requests.post(url, data=payload, files=files, timeout=10)
            
        if response.status_code == 200:
            print("[INFO] Notifikasi dan barang bukti berhasil terkirim ke Telegram!")
        else:
            print(f"[GAGAL] Error Telegram: {response.text}")
            
    except Exception as e:
        print(f"[ERROR] Gagal mengirim file: {e}")

# Cara tes langsung jalankan file ini:
if __name__ == "__main__":
    # Pastikan Anda punya gambar contoh bernama 'dummy_bukti.jpg' di folder yang sama
    kirim_peringatan_telegram("Marsa_1.PNG", "Marsa")