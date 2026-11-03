document.addEventListener("DOMContentLoaded", function () {
    loadActiveCameras();
});

function loadActiveCameras() {
    fetch("/api/cameras/list")
        .then(response => response.json())
        .then(cameras => {
            const grid = document.getElementById("camera-grid");
            const countBadge = document.getElementById("active-count");
            
            grid.innerHTML = "";
            
            // Hitung hanya kamera yang sedang aktif (Live)
            const activeCount = cameras.filter(cam => cam.is_active).length;
            countBadge.innerText = `${activeCount} Kamera Live`;

            if (cameras.length === 0) {
                grid.innerHTML = `
                    <div class="col-12 text-center py-5 text-muted">
                        <h5>Belum ada kamera RTSP terdaftar.</h5>
                        <p>Silakan tambahkan kamera melalui menu <strong>Kelola Kamera</strong>.</p>
                    </div>`;
                return;
            }

            cameras.forEach(cam => {
                const col = document.createElement("div");
                col.className = "col-lg-4 col-md-6 col-12"; // Menggunakan ukuran kolom yang sedikit lebih lebar

                // Penentuan tampilan berdasarkan status aktif
                const statusBadge = cam.is_active 
                    ? '<span class="badge bg-danger text-uppercase">LIVE</span>' 
                    : '<span class="badge bg-secondary text-uppercase">OFFLINE</span>';
                
                const imgSrc = cam.is_active 
                    ? `/api/stream/${cam.camera_id}` 
                    : 'https://via.placeholder.com/640x360/222222/FFFFFF?text=STREAM+DIHENTIKAN';
                
                // INI ADALAH TOMBOL YANG AKAN MUNCUL DI AREA LINGKARAN MERAH ANDA
                const actionBtn = cam.is_active 
                    ? `<button class="btn btn-danger w-100 fw-bold" onclick="toggleStream('${cam.camera_id}', 'stop')">⏹ Stop Kamera</button>`
                    : `<button class="btn btn-success w-100 fw-bold" onclick="toggleStream('${cam.camera_id}', 'start')">▶ Start Kamera</button>`;

                col.innerHTML = `
                    <div class="cctv-card d-flex flex-column shadow-sm" style="background-color: #1e1e1e; border: 1px solid #333; border-radius: 8px; overflow: hidden;">
                        
                        <!-- Header / Judul Kamera -->
                        <div class="cctv-header d-flex justify-content-between align-items-center p-2" style="background-color: #252525; border-bottom: 1px solid #333;">
                            <span class="fw-bold text-white small">${cam.name} (${cam.camera_id})</span>
                            ${statusBadge}
                        </div>
                        
                        <!-- Area Video Stream -->
                        <div class="cctv-stream-container position-relative" style="width: 100%; padding-top: 56.25%; background-color: #000;">
                            <img src="${imgSrc}" alt="Stream ${cam.camera_id}" class="position-absolute top-0 start-0 w-100 h-100" style="object-fit: cover;">
                        </div>
                        
                        <!-- Area Footer (Tempat Tombol Start/Stop di Lingkaran Merah) -->
                        <div class="cctv-footer p-3" style="background-color: #1a1a1a; border-top: 1px solid #333;">
                            ${actionBtn}
                        </div>

                    </div>
                `;
                grid.appendChild(col);
            });
        })
        .catch(err => console.error("Gagal memuat daftar kamera:", err));
}

// Fungsi untuk mengirim perintah Start/Stop ke backend FastAPI
function toggleStream(cameraId, action) {
    fetch(`/api/cameras/${cameraId}/${action}`, { 
        method: "POST" 
    })
    .then(response => response.json())
    .then(data => {
        // Render ulang grid untuk memperbarui status gambar dan tombol
        loadActiveCameras();
    })
    .catch(err => console.error("Gagal mengubah status stream:", err));
}