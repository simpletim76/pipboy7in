# PIP-BOY 3000 MkV — Raspberry Pi Dashboard

A Fallout-themed system status screen for Raspberry Pi 5 with 7" display.

## Files

| File | Purpose |
|------|---------|
| `pipboy.html` | The dashboard UI (Chromium kiosk) |
| `stats_server.py` | Flask API serving live system stats |
| `launch.sh` | One-shot setup & launch script |
| `pipboy.service` | Systemd unit for boot auto-start |

---

## Quick Start

```bash
# 1. Clone or copy this folder to your Pi
scp -r pipboy/ pi@raspberrypi.local:~/pipboy

# 2. SSH in
ssh pi@raspberrypi.local

# 3. Make launch script executable and run
chmod +x ~/pipboy/launch.sh
~/pipboy/launch.sh
```

That's it — the script installs dependencies, starts the stats server, and opens Chromium in kiosk mode.

---

## Auto-Start on Boot (Recommended)

```bash
# Edit pipboy.service and update all paths from /home/pi to your username
nano ~/pipboy/pipboy.service

# Install and enable
sudo cp ~/pipboy/pipboy.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pipboy
sudo systemctl start pipboy

# Check status
sudo systemctl status pipboy
```

---

## Display Setup

For the **Head Sun 7" 1024x600** display, if the resolution doesn't auto-detect:

```bash
# Add to /boot/config.txt (legacy) or /boot/firmware/config.txt (Pi 5)
sudo nano /boot/firmware/config.txt
```

Add at the bottom:
```
hdmi_group=2
hdmi_mode=87
hdmi_cvt=1024 600 60 6 0 0 0
hdmi_drive=1
```

Then reboot.

---

## Customizing

### Change the Vault quotes
Edit `stats_server.py` → `VAULT_QUOTES` list.

### Change poll interval
Edit `pipboy.html` → bottom of `<script>` → `setInterval(fetchStats, 3000)` (ms).

### Add more data
The Flask `/stats` endpoint is easy to extend — add any fields to the JSON and display them in the HTML.

### Run on a different port
Edit `stats_server.py` → `app.run(port=5000)` and update `pipboy.html` → `const API = 'http://localhost:5000/stats'`.

---

## Troubleshooting

**Stats server won't start:**
```bash
cat ~/pipboy/stats_server.log
```

**Chromium won't open / black screen:**
```bash
export DISPLAY=:0
chromium-browser --kiosk "file://$HOME/pipboy/pipboy.html"
```

**Temperature always shows `--`:**
Make sure `vcgencmd` is available: `which vcgencmd`. On Pi 5 with recent OS it should be at `/usr/bin/vcgencmd`.

**WiFi SSID not showing:**
Install wireless tools: `sudo apt install wireless-tools`

---

## Requirements

- Raspberry Pi 5 (works on Pi 4 too)
- Raspberry Pi OS (Bookworm or Bullseye)
- 7" display at 1024×600
- Python 3.10+
- Chromium browser (pre-installed on Raspberry Pi OS Desktop)
