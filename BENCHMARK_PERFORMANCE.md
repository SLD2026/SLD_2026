# 🌊 River Monitoring System - Performance & Stability Patch

## Patch Stability RTSP Decoding H.264

**Tanggal**: 2024
**Versi**: 2.2.0 - Production Stable

### Masalah yang Diperbaiki

1. **Error Decoding H.264**: 
   ```
   [h264 @ ...] left block unavailable for requested intra4x4 mode -1
   [h264 @ ...] error while decoding MB 0 25, bytestream 119357
   [h264 @ ...] cabac decode of qscale diff failed
   ```
   Penyebab: packet loss UDP, stream corrupt dari NVR, buffer underrun.

2. **Dashboard Crash/Freeze**: Terjadi saat frame corrupt masuk ke pipeline AI tanpa validasi.

### Perbaikan yang Diterapkan

#### 1. Config.py - FFMPEG Options
```python
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = 
"rtsp_transport;udp|reorder_queue_size;100|stimeout;5000000|buffer_size;2048000|
analyzeduration;5000000|probesize;5000000|max_delay;500000"
```
- `analyzeduration` + `probesize`: Lebih toleran terhadap stream tidak stabil
- `max_delay`: Batasi latency maksimum

#### 2. stream_manager.py - StreamReader Anti-Crash
- Validasi frame: `len(frame.shape) == 3 and frame.shape[2] == 3`
- `consecutive_failures` counter dengan auto-reconnect strategy
- Reconnect otomatis setelah 3 kegagalan berturut-turut
- `CAP_PROP_FPS = 15` untuk stabilitas
- Exception handling di thread update

#### 3. vision_pipeline.py - Guard Klas
- Validasi frame di awal `process_frame`: `frame is None`, `frame.size == 0`, shape check
- Try-except di seluruh pipeline processing
- Frame corrupt → return frame asli tanpa overlay (stream tetap hidup)
- `_draw_overlays` dengan validasi koordinat bounding box
- `VideoRecorder` dengan init safety dan try-except write

#### 4. detector.py - Safe Detection
- Try-except wrapper di `detect_and_track`
- Return empty boxes jika error, tidak crash pipeline
- Validasi per-box saat iterasi

#### 5. stream_routes.py - MJPEG Resilient
- `consecutive_errors` counter dengan auto-reinit stream
- Frame processing dengan try-except, fallback ke frame asli
- Encode JPEG dengan fallback ke `last_frame`
- GPU semaphore non-blocking dengan graceful degradation

### Prinsip Desain

**Fail-Safe, Not Fail-Fast**
- Stream selalu hidup meski AI gagal
- Frame corrupt → skip processing, tetap tampilkan frame terakhir valid
- Error di satu kamera tidak menjatuhkan kamera lain
- Logging error tanpa crash

### Monitoring

Error decoding H.264 sekarang:
- Tidak crash dashboard
- Di-log saja di console
- Stream otomatis recover dalam 1-2 detik

### Testing

Disarankan test dengan:
1. Network throttling
2. Multiple camera concurrent (4-8 stream)
3. Long run 24 jam
4. NVR Hikvision load tinggi

Sistem siap untuk penelitian jangka panjang dan deployment lapangan.
