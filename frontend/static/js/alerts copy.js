document.addEventListener("DOMContentLoaded", function () {
    fetch("/api/logs/")
        .then(response => response.json())
        .then(logs => {
            const grid = document.getElementById("log-grid");
            grid.innerHTML = "";

            if (logs.length === 0) {
                grid.innerHTML = `<div class="col-12 text-center text-muted mt-5"><h5>Belum ada pelanggaran yang terekam.</h5></div>`;
                return;
            }

            logs.forEach(log => {
                // Format tanggal agar lebih mudah dibaca
                const dateObj = new Date(log.timestamp);
                const timeString = dateObj.toLocaleString('id-ID');

                grid.innerHTML += `
                    <div class="col-md-3">
                        <div class="card bg-secondary text-white shadow-sm" style="border: 1px solid #444;">
                            <img src="${log.image_proof_path}" class="card-img-top" alt="Bukti Foto" style="height: 200px; object-fit: cover;">
                            <div class="card-body text-center">
                                <h6 class="text-warning mb-1">${log.identified_person_id}</h6>
                                <p class="mb-1 small text-light">Akurasi Wajah: ${log.similarity_score}%</p>
                                <p class="mb-0 text-secondary small"><small>Kamera: ${log.camera_id}</small></p>
                                <p class="text-secondary small"><small>${timeString}</small></p>
                            </div>
                        </div>
                    </div>
                `;
            });
        })
        .catch(err => console.error("Gagal memuat log:", err));
});