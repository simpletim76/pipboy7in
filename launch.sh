#!/bin/bash
# ============================================================
# Pip-Boy Dashboard Setup & Launch Script
# For Raspberry Pi 5 with 7" display
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

echo ""
echo "  ██████╗ ██╗██████╗       ██████╗  ██████╗ ██╗   ██╗"
echo "  ██╔══██╗██║██╔══██╗      ██╔══██╗██╔═══██╗╚██╗ ██╔╝"
echo "  ██████╔╝██║██████╔╝█████╗██████╔╝██║   ██║ ╚████╔╝ "
echo "  ██╔═══╝ ██║██╔═══╝ ╚════╝██╔══██╗██║   ██║  ╚██╔╝  "
echo "  ██║     ██║██║           ██████╔╝╚██████╔╝   ██║   "
echo "  ╚═╝     ╚═╝╚═╝           ╚═════╝  ╚═════╝    ╚═╝   "
echo ""
echo "  VAULT-TEC DASHBOARD — SETUP & LAUNCH"
echo "  ======================================="
echo ""

# ---- 1. Install system dependencies ----
echo "[1/4] Checking system packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3-pip python3-venv python3-psutil \
    wireless-tools chromium-browser unclutter 2>/dev/null || true

# ---- 2. Python virtual environment ----
echo "[2/4] Setting up Python environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
pip install -q flask flask-cors psutil

# ---- 3. Start the stats server in background ----
echo "[3/4] Starting stats server..."
pkill -f stats_server.py 2>/dev/null || true
sleep 1
nohup python3 "$SCRIPT_DIR/stats_server.py" > "$SCRIPT_DIR/stats_server.log" 2>&1 &
SERVER_PID=$!
echo "      Server PID: $SERVER_PID (log: stats_server.log)"
sleep 2

# Verify server started
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "      ✓ Server is running"
else
    echo "      ✗ Server may not be ready yet — check stats_server.log"
fi

# ---- 4. Launch Chromium in kiosk mode ----
echo "[4/4] Launching dashboard in kiosk mode..."
export DISPLAY=:0

# Hide mouse cursor
unclutter -idle 0.1 -root &

# Set screen resolution for Head Sun 7" (1024x600)
xrandr --output HDMI-1 --mode 1024x600 2>/dev/null || \
xrandr --output DSI-1 --mode 1024x600 2>/dev/null || true

# Launch Chromium kiosk
chromium-browser \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --no-first-run \
    --disable-restore-session-state \
    --disable-component-update \
    --window-position=0,0 \
    --window-size=1024,600 \
    --app="file://$SCRIPT_DIR/pipboy.html" &

echo ""
echo "  ✓ Pip-Boy dashboard launched!"
echo "  ✓ Stats server: http://localhost:5000/stats"
echo ""
echo "  Press Ctrl+C to stop, or run: pkill -f stats_server.py"
echo ""

wait $SERVER_PID
