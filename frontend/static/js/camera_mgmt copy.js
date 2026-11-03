document.addEventListener("DOMContentLoaded", function () {
    loadCameraTable();

    document.getElementById("add-camera-form").addEventListener("submit", function (e) {
        e.preventDefault();

        const btn = this.querySelector('button[type="submit"]');
        btn.disabled = true;
        btn.innerText = "Menyimpan...";

        const payload = {
            camera_id: document.getElementById("cam-id").value.trim(),
            name: document.getElementById("cam-name").value.trim(),
            rtsp_url: document.getElementById("cam-rtsp").value.trim(),
            roi_polygon: "[]" // Placeholder ROI
        };

        fetch("/api/cameras/add", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            if (data.detail) {
                alert("Error: " + data.detail);
            } else {
                alert("Kamera berhasil ditambahkan!");
                document.getElementById("add-camera-form").reset();
                loadCameraTable();
            }
        })
        .catch(err => console.error(err))
        .finally(() => {
            btn.disabled = false;
            btn.innerText = "Simpan & Aktifkan Kamera";
        });
    });
});

function loadCameraTable() {
    fetch("/api/cameras/list")
        .then(response => response.json())
        .then(cameras => {
            const tbody = document.getElementById("camera-table-body");
            tbody.innerHTML = "";

            if (cameras.length === 0) {
                tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted">Belum ada kamera.</td></tr>`;
                return;
            }

            cameras.forEach(cam => {
                tbody.innerHTML += `
                    <tr>
                        <td>${cam.camera_id}</td>
                        <td>${cam.name}</td>
                        <td><span class="badge bg-success">Aktif</span></td>
                        <td>
                            <button class="btn btn-sm btn-danger" onclick="deleteCamera('${cam.camera_id}')">Hapus</button>
                        </td>
                    </tr>
                `;
            });
        });
}

function deleteCamera(cameraId) {
    if (confirm(`Yakin ingin menghapus kamera ${cameraId}?`)) {
        fetch(`/api/cameras/remove/${cameraId}`, { method: "DELETE" })
            .then(res => res.json())
            .then(data => {
                alert(data.message || data.detail);
                loadCameraTable();
            });
    }
}