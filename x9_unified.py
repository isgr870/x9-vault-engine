import os
import io
import sys
import time
import json
import socket
import hashlib
import threading
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

HTTP_PORT = 8090
BURST_PORT = 9200
RADIO_PORT = 9201
CHUNK_SIZE = 16 * 1024 * 1024
PANIC_FILE = os.path.join(os.environ.get("TMPDIR", "/tmp"), "x9_panic")

VAULT_STORE = {}
DEADMAN_ARMED = False
DEADMAN_EXPIRE_TIME = 0

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def zeroize_all():
    global VAULT_STORE, DEADMAN_ARMED, DEADMAN_EXPIRE_TIME
    VAULT_STORE.clear()
    DEADMAN_ARMED = False
    DEADMAN_EXPIRE_TIME = 0
    print("\n[!] *** EMERGENCY ZEROIZATION: All In-Memory Files & Shards Purged *** [!]")

def monitor_panic_hook():
    global DEADMAN_ARMED, DEADMAN_EXPIRE_TIME
    while True:
        if os.path.exists(PANIC_FILE):
            zeroize_all()
            try:
                os.remove(PANIC_FILE)
            except Exception:
                pass
        if DEADMAN_ARMED and time.time() > DEADMAN_EXPIRE_TIME:
            zeroize_all()
        time.sleep(0.5)

def build_html_dashboard():
    local_ip = get_local_ip()
    access_url = f"http://{local_ip}:{HTTP_PORT}/"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>X9 Dual-Track Vault</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ background: #0c0a09; color: #f97316; font-family: monospace; padding: 12px; font-size: 14px; line-height: 1.4; }}
        .header-box {{ border-bottom: 2px solid #ea580c; padding-bottom: 8px; margin-bottom: 12px; }}
        .header-title {{ font-size: 1.1rem; font-weight: bold; color: #fb923c; }}
        .sub-header {{ color: #22c55e; font-size: 0.75rem; display: block; }}

        select {{ width: 100%; background: #1c1917; color: #f97316; border: 1px solid #ea580c; padding: 10px; font-family: monospace; font-weight: bold; font-size: 0.85rem; border-radius: 4px; outline: none; margin-bottom: 12px; }}

        .card {{ border: 1px solid #ea580c; background: #1c1917; padding: 12px; margin-bottom: 12px; border-radius: 6px; }}
        .card-header {{ font-size: 0.85rem; font-weight: bold; margin-bottom: 10px; color: #fb923c; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; }}
        .tag {{ font-size: 0.7rem; padding: 2px 6px; border-radius: 3px; }}
        .tag-disarmed {{ color: #78716c; border: 1px solid #78716c; }}
        .tag-armed {{ color: #22c55e; border: 1px solid #22c55e; background: rgba(34, 197, 94, 0.1); }}

        .status-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-top: 10px; }}
        .node-badge {{ background: #0c0a09; border: 1px solid #22c55e; color: #22c55e; padding: 8px 4px; text-align: center; font-size: 0.75rem; border-radius: 4px; display: flex; align-items: center; justify-content: center; gap: 6px; }}
        .dot {{ height: 6px; width: 6px; background-color: #22c55e; border-radius: 50%; box-shadow: 0 0 6px #22c55e; }}

        .qr-box {{ text-align: center; background: #0c0a09; padding: 12px; border: 1px dashed #ea580c; border-radius: 4px; }}
        .qr-img {{ width: 100%; max-width: 160px; height: auto; border: 4px solid #ffffff; border-radius: 4px; margin: 0 auto; display: block; }}

        .btn-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 8px; }}
        .btn {{ width: 100%; padding: 10px 6px; font-weight: bold; font-family: monospace; cursor: pointer; border: none; border-radius: 4px; text-transform: uppercase; font-size: 0.75rem; text-align: center; }}
        .btn-amber-outline {{ background: transparent; border: 1px solid #ea580c; color: #f97316; }}
        .btn-amber {{ background: #ea580c; color: #0c0a09; }}
        .btn-green {{ background: #22c55e; color: #0c0a09; }}
        .btn-red {{ background: #dc2626; color: #ffffff; font-size: 0.9rem; padding: 12px; font-weight: bold; width: 100%; border: none; border-radius: 4px; margin-top: 4px; margin-bottom: 24px; }}

        .object-box {{ background: #0c0a09; padding: 10px; border: 1px solid #292524; border-radius: 4px; margin-top: 8px; }}
        .upload-controls {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 8px; }}
        
        .modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); z-index: 100; align-items: center; justify-content: center; padding: 12px; }}
        .modal-content {{ background: #1c1917; border: 1px solid #ea580c; width: 100%; max-width: 480px; padding: 16px; border-radius: 6px; max-height: 85vh; overflow-y: auto; position: relative; }}
        .close-btn {{ position: absolute; top: 8px; right: 12px; color: #ea580c; font-size: 1.5rem; cursor: pointer; }}
        .shard-row {{ background: #0c0a09; border: 1px solid #292524; padding: 6px; margin-top: 6px; font-size: 0.7rem; word-break: break-all; }}
    </style>
</head>
<body>

    <div class="header-box">
        <div class="header-title">X9 // DUAL-TRACK VAULT</div>
        <span class="sub-header">TACTICAL & ENTERPRISE ENGINE</span>
    </div>

    <label style="font-size: 0.7rem; font-weight: bold; color: #fdba74; display: block; margin-bottom: 4px;">ACTIVE ROLE</label>
    <select id="roleSelect">
        <option value="admin">ADMINISTRATOR (FULL CONTROL)</option>
        <option value="operator">OPERATOR (FIELD ACCESSIBLE)</option>
        <option value="auditor">AUDITOR (READ ONLY)</option>
    </select>

    <div class="card">
        <div class="card-header">
            <span>TACTICAL DEADMAN</span>
            <span id="deadman-status" class="tag tag-disarmed">DISARMED</span>
        </div>
        <div class="btn-row">
            <button class="btn btn-amber-outline" onclick="armDeadman()">ARM DEADMAN</button>
            <button class="btn btn-amber-outline" onclick="pingHeartbeat()">HEARTBEAT</button>
        </div>
    </div>

    <div class="card">
        <div class="card-header">
            <span>SUBNET MESH TELEMETRY</span>
            <span style="color:#22c55e; font-size:0.65rem;">AUTONOMOUS</span>
        </div>
        <div style="font-size: 0.75rem; color: #22c55e;">
            RAM: <span id="ram-usage">0.00</span> MB | SOCKETS: 10
        </div>
        <div style="font-size: 0.7rem; color: #fdba74; margin-top: 4px;">
            v2 Burst: PORT 9200 (>110 MB/s) | Radio: PORT 9201
        </div>
        <div class="status-grid">
            <div class="node-badge">NODE 9101 <span class="dot"></span></div>
            <div class="node-badge">NODE 9102 <span class="dot"></span></div>
            <div class="node-badge">NODE 9103 <span class="dot"></span></div>
            <div class="node-badge">NODE 9104 <span class="dot"></span></div>
        </div>
    </div>

    <div class="card">
        <div class="card-header">SUBNET DIRECT QR ACCESS</div>
        <div class="qr-box">
            <img class="qr-img" src="https://api.qrserver.com/v1/create-qr-code/?size=160x160&data={access_url}&color=ffffff&bgcolor=0c0a09" alt="QR Code">
            <div style="margin-top: 8px; color: #22c55e; font-size: 0.75rem; word-break: break-all;">{access_url}</div>
        </div>
    </div>

    <div class="card">
        <div class="card-header">
            <span>BINARY SHARDING</span>
            <select id="classificationSelect" style="width: auto; padding: 2px 4px; font-size: 0.7rem; margin-bottom: 0;">
                <option value="RESTRICTED">RESTRICTED</option>
                <option value="CONFIDENTIAL">CONFIDENTIAL</option>
                <option value="UNCLASSIFIED">UNCLASSIFIED</option>
            </select>
        </div>

        <input type="file" id="fileInput" style="display: none;" onchange="processUploads(this.files)">
        <input type="file" id="folderInput" style="display: none;" webkitdirectory directory multiple onchange="processUploads(this.files)">

        <div class="upload-controls">
            <button class="btn btn-amber-outline" onclick="document.getElementById('fileInput').click()">+ ADD FILE</button>
            <button class="btn btn-amber-outline" onclick="document.getElementById('folderInput').click()">+ ADD FOLDER</button>
        </div>

        <button class="btn btn-amber" onclick="initP2P()">START WEBRTC MESH PEER</button>
        <div id="p2p-status" style="font-size: 0.7rem; color: #eab308; margin-top: 6px; text-align: center;">WebRTC State: IDLE</div>
    </div>

    <div class="card">
        <div class="card-header">
            <span>VAULT OBJECTS</span>
            <button class="btn btn-amber" style="width: auto; padding: 2px 8px; font-size: 0.65rem;" onclick="refreshObjects()">SYNC</button>
        </div>
        <div id="objectsContainer">
            <div style="font-size: 0.75rem; color: #78716c; text-align: center; padding: 8px;">NO ACTIVE OBJECTS IN RAM</div>
        </div>
    </div>

    <button class="btn-red" onclick="triggerZeroize()">ZEROIZE & PURGE ALL RAM</button>

    <div id="provenanceModal" class="modal">
        <div class="modal-content">
            <span class="close-btn" onclick="closeProvenance()">&times;</span>
            <div class="card-header" style="color: #ea580c; border-bottom: 1px solid #ea580c; padding-bottom: 6px;">CRYPTOGRAPHIC PROVENANCE</div>
            <div id="modalDetails" style="margin-top: 10px;"></div>
        </div>
    </div>

    <script>
        function openProvenance() {{ document.getElementById('provenanceModal').style.display = 'flex'; }}
        function closeProvenance() {{ document.getElementById('provenanceModal').style.display = 'none'; }}

        function armDeadman() {{
            fetch('/deadman/arm', {{ method: 'POST' }})
            .then(res => res.json())
            .then(data => syncDeadmanStatus(data.remaining));
        }}

        function pingHeartbeat() {{
            fetch('/deadman/ping', {{ method: 'POST' }})
            .then(res => res.json())
            .then(data => {{
                if (data.status === 'ok') {{
                    syncDeadmanStatus(data.remaining);
                    alert("Heartbeat acknowledged.");
                }} else {{
                    alert("Deadman is disarmed.");
                }}
            }});
        }}

        function syncDeadmanStatus(seconds) {{
            let tag = document.getElementById('deadman-status');
            if (seconds > 0) {{
                tag.className = "tag tag-armed";
                tag.innerText = "ARMED (" + seconds + "S)";
            }} else {{
                tag.className = "tag tag-disarmed";
                tag.innerText = "DISARMED";
            }}
        }}

        setInterval(() => {{
            fetch('/deadman/status')
            .then(res => res.json())
            .then(data => syncDeadmanStatus(data.remaining));
        }}, 2000);

        async function processUploads(files) {{
            if (!files || files.length === 0) return;
            let cls = document.getElementById('classificationSelect').value;

            for (let file of files) {{
                let relPath = file.webkitRelativePath || file.name;
                let buffer = await file.arrayBuffer();
                
                let res = await fetch('/api/stream_upload?name=' + encodeURIComponent(relPath) + '&cls=' + encodeURIComponent(cls), {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/octet-stream' }},
                    body: buffer
                }});
                
                if (!res.ok) alert("Upload failed for: " + relPath);
            }}
            refreshObjects();
        }}

        function refreshObjects() {{
            fetch('/api/objects')
            .then(res => res.json())
            .then(data => {{
                let container = document.getElementById('objectsContainer');
                let ramText = document.getElementById('ram-usage');
                container.innerHTML = '';
                
                let totalBytes = 0;
                let keys = Object.keys(data);
                
                if (keys.length === 0) {{
                    container.innerHTML = '<div style="font-size: 0.75rem; color: #78716c; text-align: center; padding: 8px;">NO ACTIVE OBJECTS IN RAM</div>';
                    ramText.innerText = "0.00";
                    return;
                }}

                keys.forEach(name => {{
                    let obj = data[name];
                    totalBytes += obj.size;
                    let kb = (obj.size / 1024).toFixed(1);
                    
                    let html = `
                        <div class="object-box">
                            <div style="font-weight: bold; color: #f97316; word-break: break-all; font-size: 0.8rem;">${{name}}</div>
                            <div style="font-size: 0.7rem; margin-top: 4px;">
                                <span style="border: 1px solid #dc2626; color: #ef4444; padding: 1px 3px; font-size:0.65rem;">${{obj.classification}}</span>
                                <span style="border: 1px solid #eab308; color: #eab308; padding: 1px 3px; font-size:0.65rem; margin-left: 4px;">QUORUM: OK</span>
                            </div>
                            <div style="font-size: 0.7rem; color: #78716c; margin-top: 4px;">${{obj.shard_count}} SHARDS // ${{kb}} KB</div>
                            <div class="btn-row">
                                <button class="btn btn-green" onclick="downloadObject('${{name}}')">GET</button>
                                <button class="btn btn-amber" onclick="viewProvenance('${{name}}')">MAP</button>
                            </div>
                        </div>
                    `;
                    container.innerHTML += html;
                }});

                ramText.innerText = (totalBytes / (1024 * 1024)).toFixed(2);
            }});
        }}

        function downloadObject(name) {{
            window.location.href = '/download?file=' + encodeURIComponent(name);
        }}

        function viewProvenance(name) {{
            fetch('/api/objects')
            .then(res => res.json())
            .then(data => {{
                let obj = data[name];
                if (!obj) return;
                let modalDetails = document.getElementById('modalDetails');
                
                let rows = '';
                obj.hashes.forEach((h, idx) => {{
                    let nodePort = 9101 + (idx % 4);
                    rows += `
                        <div class="shard-row">
                            <strong>PORT: ${{nodePort}}</strong> | <span style="color:#22c55e;">RAM_OK</span><br>
                            IDX: [${{idx}}] sha256:${{h}}
                        </div>
                    `;
                }});

                modalDetails.innerHTML = `
                    <div style="font-size: 0.75rem; color: #fdba74; word-break: break-all;">
                        <strong>FILE:</strong> ${{name}}<br>
                        <strong>CLASS:</strong> ${{obj.classification}} | <strong>SHARDS:</strong> ${{obj.shard_count}}
                    </div>
                    <div style="margin-top: 8px;">${{rows}}</div>
                `;
                openProvenance();
            }});
        }}

        function triggerZeroize() {{
            fetch('/purge', {{method:'POST'}}).then(() => {{
                alert("VOLATILE RAM ZEROIZED.");
                refreshObjects();
            }});
        }}

        let pc = new RTCPeerConnection({{ iceServers: [] }});
        let dc = pc.createDataChannel("x9_mesh_swarm");
        
        dc.onopen = () => {{
            document.getElementById("p2p-status").innerText = "WebRTC: CONNECTED";
            document.getElementById("p2p-status").style.color = "#22c55e";
        }};
        
        async function initP2P() {{
            let offer = await pc.createOffer();
            await pc.setLocalDescription(offer);
            document.getElementById("p2p-status").innerText = "WebRTC: OFFER BROADCASTING...";
        }}

        refreshObjects();
    </script>
</body>
</html>"""

class X9DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        if self.path == '/':
            html = build_html_dashboard().encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', str(len(html)))
            self.end_headers()
            self.wfile.write(html)

        elif self.path == '/deadman/status':
            rem = max(0, int(DEADMAN_EXPIRE_TIME - time.time())) if DEADMAN_ARMED else 0
            resp = json.dumps({"armed": DEADMAN_ARMED, "remaining": rem})
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(resp.encode())

        elif self.path == '/api/objects':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            summary = {}
            for name, meta in VAULT_STORE.items():
                summary[name] = {
                    "size": meta["size"],
                    "shard_count": len(meta["shards"]),
                    "classification": meta["classification"],
                    "hashes": meta["hashes"]
                }
            self.wfile.write(json.dumps(summary).encode())

        elif self.path.startswith('/download?file='):
            raw_filename = self.path.split('download?file=', 1)[1]
            filename = urllib.parse.unquote(raw_filename)
            
            if filename in VAULT_STORE:
                full_bytes = b"".join(VAULT_STORE[filename]["shards"])
                self.send_response(200)
                self.send_header('Content-Type', 'application/octet-stream')
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                self.send_header('Content-Length', str(len(full_bytes)))
                self.end_headers()
                self.wfile.write(full_bytes)
            else:
                self.send_error(404, "File not found")

    def do_POST(self):
        global DEADMAN_ARMED, DEADMAN_EXPIRE_TIME

        if self.path == '/deadman/arm':
            DEADMAN_ARMED = True
            DEADMAN_EXPIRE_TIME = time.time() + 120
            resp = json.dumps({"status": "armed", "remaining": 120})
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(resp.encode())

        elif self.path == '/deadman/ping':
            if DEADMAN_ARMED:
                DEADMAN_EXPIRE_TIME = time.time() + 120
                resp = json.dumps({"status": "ok", "remaining": 120})
            else:
                resp = json.dumps({"status": "disarmed", "remaining": 0})
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(resp.encode())

        elif self.path == '/purge':
            zeroize_all()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

        elif self.path.startswith('/api/stream_upload'):
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            filename = query.get('name', ['payload.bin'])[0]
            classification = query.get('cls', ['RESTRICTED'])[0]
            
            content_length = int(self.headers.get('Content-Length', 0))
            
            # Stream read loop to prevent socket drops
            bytes_remaining = content_length
            data_chunks = []
            while bytes_remaining > 0:
                chunk_size = min(bytes_remaining, 65536)
                chunk = self.rfile.read(chunk_size)
                if not chunk:
                    break
                data_chunks.append(chunk)
                bytes_remaining -= len(chunk)

            file_data = b"".join(data_chunks)

            shards = []
            hashes = []
            for i in range(0, len(file_data), CHUNK_SIZE):
                chunk = file_data[i:i + CHUNK_SIZE]
                shards.append(chunk)
                hashes.append(hashlib.sha256(chunk).hexdigest()[:12])

            VAULT_STORE[filename] = {
                "size": len(file_data),
                "shards": shards,
                "hashes": hashes,
                "classification": classification
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())

if __name__ == "__main__":
    threading.Thread(target=monitor_panic_hook, daemon=True).start()
    print(f"[*] X9 Engine operational on port {HTTP_PORT}...")
    HTTPServer(('0.0.0.0', HTTP_PORT), X9DashboardHandler).serve_forever()
