import http.server
import socketserver
import os
import json
import urllib.parse
import tarfile
import io

PORT = 8090
UPLOAD_DIR = os.path.abspath("./vault_storage")
os.makedirs(UPLOAD_DIR, exist_ok=True)

HTML_UI = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>X9 Tactical Mesh Vault</title>
    <style>
        body { background: #0b0f12; color: #00ff66; font-family: monospace; margin: 0; padding: 10px; }
        .box { border: 1px dashed #00ff66; padding: 10px; margin-bottom: 10px; background: rgba(0,255,102,0.02); }
        h3 { margin: 0 0 8px 0; font-size: 0.85rem; color: #ff9933; text-transform: uppercase; }
        .object-item { display: flex; justify-content: space-between; align-items: center; padding: 6px 8px; margin-bottom: 6px; background: rgba(0,255,102,0.05); border: 1px solid #00ff66; font-size: 0.7rem; }
        .folder-item { background: rgba(255,123,0,0.1); border: 1px solid #ff7b00; }
        button { background: #00ff66; color: #0b0f12; border: none; padding: 4px 8px; font-family: monospace; font-weight: bold; border-radius: 2px; cursor: pointer; font-size: 0.65rem; }
        .btn-folder { background: #ff7b00; color: #0b0f12; }
    </style>
</head>
<body>
    <div class="box" style="text-align: center;">
        <img id="qrcode" src="https://api.qrserver.com/v1/create-qr-code/?size=130x130&data=http://127.0.0.1:8090/" alt="QR" style="margin-bottom: 5px;"/>
        <div style="font-size: 0.75rem;">http://127.0.0.1:8090/</div>
    </div>

    <div class="box">
        <h3>Vault Objects & Lineage</h3>
        <div id="vault-objects-list" style="max-height: 250px; overflow-y: auto;">
            <div style="color: #888; text-align: center; font-size: 0.75rem;">Scanning RAM...</div>
        </div>
    </div>

    <script>
        function fetchVaultObjects() {
            fetch('/api/status')
                .then(res => res.json())
                .then(data => {
                    let container = document.getElementById('vault-objects-list');
                    container.innerHTML = '';
                    if (!data.files || data.files.length === 0) {
                        container.innerHTML = '<div style="color: #888; text-align: center; font-size: 0.75rem;">No objects in vault.</div>';
                        return;
                    }
                    let dirs = new Set();
                    data.files.forEach(f => {
                        let parts = f.name.split('/');
                        if (parts.length > 1) dirs.add(parts[0]);
                    });
                    dirs.forEach(dir => {
                        let div = document.createElement('div');
                        div.className = 'object-item folder-item';
                        div.innerHTML = '<span style="color: #ff9933; font-weight: bold;">📁 ' + dir + '/</span>' +
                                        '<button class="btn-folder" onclick="window.location.href=\'/api/archive?dir=' + encodeURIComponent(dir) + '\'">TARBALL (.GZ)</button>';
                        container.appendChild(div);
                    });
                    data.files.forEach(file => {
                        let div = document.createElement('div');
                        div.className = 'object-item';
                        div.innerHTML = '<span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 55%;" title="' + file.name + '">' + file.name + '</span>' +
                                        '<div style="display: flex; align-items: center; gap: 6px;">' +
                                        '<span style="color: #00ff66;">' + file.size + ' MB</span>' +
                                        '<button onclick="window.location.href=\'/api/download?file=' + encodeURIComponent(file.name) + '\'">GET</button>' +
                                        '</div>';
                        container.appendChild(div);
                    });
                }).catch(err => console.error(err));
        }
        setInterval(fetchVaultObjects, 2000);
        fetchVaultObjects();
    </script>
</body>
</html>
"""

class VaultHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == '/' or path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_UI.encode('utf-8'))
        elif path == '/api/status':
            files = []
            for root, dirs, filenames in os.walk(UPLOAD_DIR):
                for filename in filenames:
                    filepath = os.path.join(root, filename)
                    relpath = os.path.relpath(filepath, UPLOAD_DIR)
                    size_mb = round(os.path.getsize(filepath) / (1024 * 1024), 2)
                    files.append({"name": relpath.replace("\\", "/"), "size": size_mb})
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"files": files}).encode('utf-8'))
        elif path == '/api/download':
            filename = query.get('file', [None])[0]
            if filename:
                safe_path = os.path.normpath(os.path.join(UPLOAD_DIR, filename))
                if safe_path.startswith(UPLOAD_DIR) and os.path.exists(safe_path) and os.path.isfile(safe_path):
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/octet-stream')
                    self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(filename)}"')
                    self.end_headers()
                    with open(safe_path, 'rb') as f:
                        self.wfile.write(f.read())
                    return
            self.send_response(404)
            self.end_headers()
        elif path == '/api/archive':
            dirname = query.get('dir', [None])[0]
            if dirname:
                target_path = os.path.normpath(os.path.join(UPLOAD_DIR, dirname))
                if target_path.startswith(UPLOAD_DIR) and os.path.exists(target_path):
                    tar_buffer = io.BytesIO()
                    with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
                        tar.add(target_path, arcname=os.path.basename(target_path))
                    tar_bytes = tar_buffer.getvalue()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/gzip')
                    self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(dirname)}.tar.gz"')
                    self.end_headers()
                    self.wfile.write(tar_bytes)
                    return
            self.send_response(404)
            self.end_headers()
        else:
            super().do_GET()

if __name__ == '__main__':
    with socketserver.TCPServer(("", PORT), VaultHandler) as httpd:
        print(f"[+] X9 Tactical Vault running at http://127.0.0.1:{PORT}")
        httpd.serve_forever()
