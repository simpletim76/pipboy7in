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
import urllib.request
import urllib.error
import json as json_lib

# ── REMOTE HOST CONFIG ──────────────────────────────────────────────────────
PIHOLE_HOST      = "192.168.1.2"          # Change to your Pi-hole IP
PIHOLE_API_TOKEN = "your_api_token_here"  # Pi-hole API token (Settings > API)
DOCKER_HOST      = "192.168.1.3"          # Change to your Docker host IP
DOCKER_PORT      = 2375                   # Docker TCP API port (unauthenticated)
# ────────────────────────────────────────────────────────────────────────────

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

@app.route('/pihole')
def pihole():
    """Fetch Pi-hole summary stats. Tries v6 API first, falls back to v5."""
    result = {
        "online": False,
        "error": None,
        "queries_today": None,
        "ads_blocked_today": None,
        "ads_percentage_today": None,
        "gravity_count": None,
        "status": "unknown"
    }
    try:
        # ── Try Pi-hole v6 API first ──────────────────────────────────────
        url_v6 = f"http://{PIHOLE_HOST}/api/stats/summary"
        req = urllib.request.Request(
            url_v6,
            headers={"X-FTL-Auth": PIHOLE_API_TOKEN}
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json_lib.loads(resp.read())
        queries = data.get("queries", {})
        result.update({
            "online": True,
            "queries_today": queries.get("total", 0),
            "ads_blocked_today": queries.get("blocked", 0),
            "ads_percentage_today": round(float(queries.get("percent_blocked", 0.0)), 1),
            "gravity_count": data.get("gravity", {}).get("domains_being_blocked", 0),
            "status": "enabled"
        })
    except Exception as e_v6:
        # ── Fall back to Pi-hole v5 API ───────────────────────────────────
        try:
            url_v5 = (
                f"http://{PIHOLE_HOST}/admin/api.php"
                f"?summaryRaw&auth={PIHOLE_API_TOKEN}"
            )
            with urllib.request.urlopen(url_v5, timeout=4) as resp:
                data = json_lib.loads(resp.read())
            result.update({
                "online": True,
                "queries_today": data.get("dns_queries_today", 0),
                "ads_blocked_today": data.get("ads_blocked_today", 0),
                "ads_percentage_today": round(float(data.get("ads_percentage_today", 0.0)), 1),
                "gravity_count": data.get("domains_being_blocked", 0),
                "status": data.get("status", "unknown")
            })
        except Exception as e_v5:
            result["error"] = f"v6: {str(e_v6)[:60]} | v5: {str(e_v5)[:60]}"
    return jsonify(result)

@app.route('/docker')
def docker_containers():
    """Fetch container list from Docker TCP API."""
    result = {
        "online": False,
        "error": None,
        "containers": []
    }
    try:
        url = f"http://{DOCKER_HOST}:{DOCKER_PORT}/containers/json?all=true"
        with urllib.request.urlopen(url, timeout=4) as resp:
            data = json_lib.loads(resp.read())
        containers = []
        for c in data:
            raw_names = c.get("Names", [])
            name = raw_names[0].lstrip("/") if raw_names else c.get("Id", "")[:12]
            containers.append({
                "name": name,
                "image": c.get("Image", "unknown"),
                "status": c.get("Status", ""),
                "state": c.get("State", "")
            })
        # Sort: running first, then paused, then everything else
        state_order = {"running": 0, "paused": 1}
        containers.sort(key=lambda x: state_order.get(x["state"], 2))
        result.update({
            "online": True,
            "containers": containers
        })
    except Exception as e:
        result["error"] = str(e)[:120]
    return jsonify(result)

if __name__ == '__main__':
    ip = socket.gethostbyname(socket.gethostname())
    print(f"🟢 NERD-O-VISION 5000 running!")
    print(f"   Local:   http://localhost:5000")
    print(f"   Network: http://{ip}:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
