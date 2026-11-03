# 🔧 H.264 Stream Corruption Fix

## Masalah yang Diperbaiki
- ❌ `[h264 @ ...] error while decoding MB` - Corrupted macroblock
- ❌ `reference picture missing during reorder` - Missing keyframe
- ❌ Dashboard kadang gelap/hitam
- ❌ Stream kadang freeze/lag

## Solusi yang Diterapkan

### 1. **FFMPEG Configuration** (`config.py`)
```python
rtsp_transport;tcp          # TCP lebih stabil dari UDP
reorder_queue_size;500      # Buffer besar untuk handle packet reordering
buffer_size;8192000         # 8MB buffer untuk burst frames
fflags;discardcorrupt       # Buang frame rusak, jangan render hitam
```

### 2. **Frame Validation** (`stream_manager.py`)
- Validasi brightness frame (1-254) - deteksi frame hitam
- Backup last good frame sebagai fallback
- Skip corrupted frames tapi tetap streaming
- Counter untuk monitoring corrupted frames

### 3. **Error Suppression** (`main.py`)
```python
OPENCV_FFMPEG_LOGLEVEL=-8   # Quiet FFMPEG errors
OPENCV_LOG_LEVEL=ERROR      # Hanya tampilkan critical error
```

### 4. **Buffer Management**
- Buffer size: 1 frame (real-time, low latency)
- FPS target: 10 fps (stabilitas > smoothness)
- Auto-reconnect setelah 10 consecutive failures

## Behavior Baru

### ✅ Sebelum Fix:
- Stream gelap/hitam saat ada corrupted frame
- Error spam di console
- Stream freeze/restart

### ✅ Setelah Fix:
- Gunakan last good frame saat ada corruption
- Log bersih (error hanya di-log setiap 50 frames)
- Stream tetap smooth meski ada packet loss
- Auto-recovery dari network issues

## Monitoring

Check corrupted frame counter di logs:
```
[WARN] SEKANAK_CONECT8: 50 corrupted frames detected (using last good frame)
```

Jika terlalu banyak (>500 per menit), artinya:
1. Network unstable (check WiFi/LAN)
2. CCTV encoding settings terlalu tinggi
3. NVR overloaded

## Rekomendasi Network

### Untuk Stream Stabil:
- ✅ Gunakan LAN cable (bukan WiFi)
- ✅ Dedicated VLAN untuk CCTV
- ✅ QoS prioritas tinggi untuk RTSP traffic
- ✅ Bandwidth minimum: 2 Mbps per camera
- ✅ Ping ke NVR: <10ms, packet loss <1%

### Setting di Hikvision NVR:
1. Video Encoding: H.264+ (bukan H.265)
2. Frame Rate: 15 fps (jangan 25/30)
3. Bitrate: 2048 Kbps (jangan terlalu tinggi)
4. I-Frame Interval: 2x frame rate (30 untuk 15fps)
5. Resolution: 1280x720 (bukan 1920x1080 untuk stabilitas)

## Testing

Test stream stability:
```bash
cd /home/noc/river_monitoring_system
python3 test_kamera.py
```

Monitor logs saat streaming:
```bash
tail -f /tmp/river_monitor.log | grep -i "corrupted\|error"
```

---
**Update:** 2026-11-03
