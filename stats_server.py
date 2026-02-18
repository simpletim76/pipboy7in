#!/usr/bin/env python3
"""
Pip-Boy Stats Server
Serves system stats as JSON AND the dashboard HTML.
Run with: python3 stats_server.py
Dashboard: http://<pi-ip>:5000
Stats API: http://<pi-ip>:5000/stats
"""

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import psutil
import subprocess
import socket
import datetime
import random
import os

app = Flask(__name__)
CORS(app)

# Directory where pipboy.html lives (same folder as this script)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

VAULT_QUOTES = [
    "War. War never changes.",
    "Please stand by.",
    "Ad Victoriam.",
    "Welcome to Vault 111.",
    "The future is here.",
    "Reclamation Day.",
    "War never changes, but men do.",
    "America will never be destroyed from outside.",
    "Atom guide your path.",
    "May your roads lead to sweet water.",
    "Remember: Vault-Tec cares.",
    "Safety. Security. Certainty.",
    "A better tomorrow, today.",
    "Stay safe. Stay inside. Stay alive.",
    "Precision. Power. Performance.",
]

def get_cpu_temp():
    try:
        result = subprocess.run(
            ['vcgencmd', 'measure_temp'],
            capture_output=True, text=True, timeout=2
        )
        temp_str = result.stdout.strip()  # e.g. "temp=47.2'C"
        temp = float(temp_str.replace("temp=", "").replace("'C", ""))
        return round(temp, 1)
    except Exception:
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                return round(int(f.read()) / 1000, 1)
        except Exception:
            return None

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "N/A"

def get_wifi_ssid():
    try:
        result = subprocess.run(
            ['iwgetid', '-r'],
            capture_output=True, text=True, timeout=2
        )
        ssid = result.stdout.strip()
        return ssid if ssid else "Not connected"
    except Exception:
        return "N/A"

def get_disk():
    usage = psutil.disk_usage('/')
    return {
        "total_gb": round(usage.total / (1024**3), 1),
        "used_gb": round(usage.used / (1024**3), 1),
        "percent": usage.percent
    }

@app.route('/')
def index():
    return send_from_directory(SCRIPT_DIR, 'pipboy.html')

@app.route('/stats')
def stats():
    cpu_percent = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = get_disk()
    cpu_temp = get_cpu_temp()
    uptime_seconds = int(datetime.datetime.now().timestamp() - psutil.boot_time())
    uptime_hours = uptime_seconds // 3600
    uptime_minutes = (uptime_seconds % 3600) // 60

    return jsonify({
        "cpu_percent": cpu_percent,
        "ram_percent": mem.percent,
        "ram_used_mb": round(mem.used / (1024**2)),
        "ram_total_mb": round(mem.total / (1024**2)),
        "cpu_temp": cpu_temp,
        "ip": get_ip(),
        "wifi_ssid": get_wifi_ssid(),
        "disk": disk,
        "uptime": f"{uptime_hours:02d}h {uptime_minutes:02d}m",
        "hostname": socket.gethostname(),
        "quote": random.choice(VAULT_QUOTES),
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    ip = socket.gethostbyname(socket.gethostname())
    print(f"🟢 NERD-O-VISION 5000 running!")
    print(f"   Local:   http://localhost:5000")
    print(f"   Network: http://{ip}:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
