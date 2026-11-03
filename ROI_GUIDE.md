# 🎯 Panduan Penggunaan ROI (Region of Interest)

## Apa itu ROI?

**ROI (Region of Interest)** adalah area spesifik dalam frame video yang akan dimonitor oleh sistem AI. Hanya aktivitas yang terjadi di dalam area ROI yang akan terdeteksi dan dicatat sebagai pelanggaran.

## Mengapa ROI Penting?

1. **Fokus Monitoring**: Memusatkan deteksi hanya pada area kritis (misalnya: tepi sungai)
2. **Mengurangi False Positive**: Menghindari deteksi dari area yang tidak relevan (jalan raya, bangunan, dll)
3. **Efisiensi Komputasi**: Sistem hanya memproses objek dalam area ROI
4. **Privasi**: Mengabaikan area privat yang tidak perlu dimonitor

## Cara Menggunakan ROI Editor

### 1. Akses ROI Editor

Buka browser dan akses halaman ROI Editor:
```
http://localhost:8000/roi
```

Atau klik menu **"🎯 ROI Editor"** di navigasi dashboard.

### 2. Pilih Kamera

- Di panel kiri, pilih kamera dari dropdown **"Pilih Kamera"**
- Sistem akan otomatis memuat live stream dari kamera tersebut
- Informasi kamera (nama, status) akan ditampilkan

### 3. Menggambar ROI Polygon

**Langkah-langkah:**

1. **Klik pada video** untuk menandai titik-titik ROI
2. Setiap klik akan menambahkan satu titik
3. **Minimal 3 titik** diperlukan untuk membuat polygon
4. Titik-titik akan terhubung secara otomatis membentuk area

**Tips Menggambar ROI:**
- Mulai dari sudut kiri atas area yang ingin dimonitor
- Klik searah jarum jam untuk hasil terbaik
- Pastikan semua area kritis (tepi sungai, jembatan) tercakup
- Hindari area yang tidak relevan (langit, bangunan jauh, jalan raya)

**Visualisasi:**
- **Titik Merah**: Lokasi setiap titik yang Anda klik
- **Angka Putih**: Nomor urut titik
- **Garis Hijau**: Border polygon ROI
- **Area Hijau Transparan**: Area yang akan dimonitor

### 4. Mengelola Titik ROI

**Melihat Daftar Titik:**
- Semua titik ditampilkan di panel kiri
- Format: `Titik N: (X, Y)` - koordinat pixel

**Menghapus Titik Tertentu:**
- Klik tombol **✕** di sebelah titik yang ingin dihapus
- Titik akan terhapus dan polygon akan diupdate otomatis

**Reset Semua Titik:**
- Klik tombol **"🔄 Reset Titik"**
- Semua titik akan dihapus dan Anda bisa mulai dari awal

### 5. Menyimpan ROI

Setelah ROI selesai digambar:

1. Klik tombol **"💾 Simpan ROI"**
2. ROI akan disimpan ke database
3. Sistem akan menampilkan pesan konfirmasi: ✅ **"ROI berhasil disimpan!"**

**Penting**: ROI yang disimpan akan langsung aktif untuk deteksi AI pada kamera tersebut.

### 6. Memuat ROI yang Tersimpan

Untuk melihat ROI yang sudah disimpan sebelumnya:

1. Pilih kamera dari dropdown
2. Klik tombol **"📥 Load ROI Tersimpan"**
3. ROI akan ditampilkan di video
4. Anda bisa mengedit dengan menambah/menghapus titik

### 7. Menghapus ROI

Untuk menghapus ROI dari database:

1. Klik tombol **"🗑️ Hapus ROI dari Database"**
2. Konfirmasi penghapusan
3. ROI akan dihapus dan monitoring akan kembali ke mode full-frame

## Contoh Konfigurasi ROI

### Scenario 1: Monitoring Tepi Sungai
```
Titik 1: Pojok kiri atas tepi sungai
Titik 2: Pojok kanan atas tepi sungai  
Titik 3: Pojok kanan bawah air
Titik 4: Pojok kiri bawah air
```

### Scenario 2: Monitoring Jembatan Penyeberangan
```
Titik 1-8: Mengikuti kontur jembatan secara melingkar
```

### Scenario 3: Multiple ROI (Untuk Kamera Wide)
Saat ini sistem mendukung **1 polygon per kamera**.
Untuk multiple area, gunakan polygon yang mencakup semua area kritis.

## Integrasi dengan Sistem AI

### Bagaimana ROI Bekerja?

1. **Frame Capture**: Sistem mengambil frame dari RTSP stream
2. **Object Detection**: YOLOv8 mendeteksi orang dan sampah
3. **ROI Filtering**: Sistem hanya memproses objek yang **centerpoint-nya** berada dalam polygon ROI
4. **Behavior Analysis**: Analisis littering dilakukan hanya untuk objek dalam ROI
5. **Alert & Logging**: Pelanggaran dicatat dengan bukti visual

### Visualisasi ROI di Live Stream

Saat streaming aktif di dashboard utama (`/`):
- **Polygon ROI** akan terlihat sebagai **overlay Cyan** di video
- **Area ROI** ditandai dengan fill transparan cyan
- **Label "ROI ZONE"** ditampilkan di pojok ROI
- Deteksi objek akan tetap menampilkan semua objek, tapi hanya yang dalam ROI yang dianalisis

## Format Data ROI

ROI disimpan dalam database sebagai **JSON string**:

```json
[
  [120, 50],
  [640, 50],
  [640, 480],
  [120, 480]
]
```

Format: Array of `[x, y]` coordinates dalam pixel.

## API Endpoints ROI

### 1. Update ROI
```http
POST /api/cameras/{camera_id}/roi
Content-Type: application/json

{
  "roi_polygon": "[[120,50],[640,50],[640,480],[120,480]]"
}
```

### 2. Get ROI
```http
GET /api/cameras/{camera_id}/roi
```

Response:
```json
{
  "camera_id": "CAM_01",
  "roi_polygon": "[[120,50],[640,50],[640,480],[120,480]]"
}
```

## Troubleshooting

### ❌ Video tidak muncul
**Penyebab**: Kamera tidak aktif atau stream error
**Solusi**: 
- Pastikan kamera sudah di-start di halaman "Kelola Kamera"
- Cek koneksi RTSP ke NVR
- Lihat log error di console browser (F12)

### ❌ Tombol "Simpan ROI" disabled
**Penyebab**: Jumlah titik kurang dari 3
**Solusi**: Klik minimal 3 titik pada video untuk membuat polygon valid

### ⚠️ ROI tidak terlihat di Live Stream
**Penyebab**: Cache browser atau stream belum reload
**Solusi**: 
- Refresh halaman dashboard (F5)
- Hard refresh dengan Ctrl+Shift+R
- Restart stream kamera

### ⚠️ Deteksi masih terjadi di luar ROI
**Penyebab**: Bug di vision pipeline atau ROI tidak ter-load
**Solusi**:
- Cek database: ROI tersimpan dengan benar?
- Restart aplikasi: `python3 main.py`
- Verifikasi `roi_polygon` di database tidak `[]` atau `null`

## Best Practices

### ✅ DO:
- Gambar ROI yang **mencakup area kritis** secara lengkap
- Beri **margin** 10-20 pixel dari tepi frame
- Test dengan **load ROI** setelah menyimpan untuk verifikasi
- Update ROI saat ada **perubahan angle kamera** atau **kondisi cahaya**

### ❌ DON'T:
- Jangan buat polygon terlalu kecil (minimal 30% dari frame)
- Jangan gunakan titik yang terlalu rapat (minimal jarak 20px)
- Jangan lupa save setelah menggambar ROI
- Jangan restart server saat sedang menggambar ROI (data belum tersimpan)

## Fitur Lanjutan (Coming Soon)

- [ ] Multiple ROI per kamera
- [ ] ROI dengan exclusion zone (area yang di-exclude)
- [ ] ROI dengan time scheduling (aktif hanya jam tertentu)
- [ ] ROI template untuk kamera sejenis
- [ ] ROI auto-adjustment berdasarkan lighting

## Support

Jika ada masalah dengan fitur ROI:
1. Cek file log: `backend_api/logs/app.log`
2. Cek database: `backend_api/database/river_monitor.db`
3. Gunakan console browser (F12) untuk debug JavaScript
4. Hubungi administrator sistem

---

**Living Lab Sekanak Connect** © 2024
Sistem Monitoring Pembuangan Sampah Berbasis AI
