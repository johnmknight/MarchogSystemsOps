# Raspberry Pi Kiosk Setup for MarchogSystemsOps

**Date:** April 11, 2026  
**Status:** In Progress (1 of 2 screens operational)

## Overview

This document describes the setup of Raspberry Pi devices as MarchogSystemsOps display clients in kiosk mode. These devices auto-boot into Chromium fullscreen, connect to the production server, and register as controllable screens.

## Hardware Inventory

| Device | Hostname | IP | Model | Architecture | Status |
|--------|----------|-----|-------|--------------|--------|
| **pi5screen11** | pi5screen11 | 192.168.5.53 | Raspberry Pi 5 Model B | aarch64 | ✅ Operational |
| **Zero1** | Zero1 | 192.168.5.54 | Raspberry Pi Zero | armv6l | ❌ **INCOMPATIBLE** |

### Credentials
- **Username:** `john`
- **Password:** `JebMun42`
- **SSH:** Enabled on both devices

## Critical Discovery: Raspberry Pi Zero Incompatibility

### The Problem

Modern Chromium (v92+) **does not run on Raspberry Pi Zero** devices. The Pi Zero uses ARMv6l architecture which lacks SIMD/NEON extensions required by current Chromium builds.

**Error:** `Illegal instruction`

**Technical Details:**
- Pi Zero: ARMv6 (ARM1176 CPU, no NEON)
- Chromium requirement: ARMv7+ with NEON SIMD instructions
- First broken: Chromium v92 (Bullseye release)
- Affects: All Pi Zero, Pi Zero W models
- Does NOT affect: Pi Zero 2 W (ARMv8), Pi 3+, Pi 4, Pi 5

### Impact

Zero1 cannot be used as a MarchogSystemsOps kiosk display. **Both Chromium and Firefox ESR fail with "Illegal instruction" errors** due to ARMv6 incompatibility. Lightweight browser alternatives (NetSurf, Links2, Midori) lack the modern web features required by MarchogSystemsOps (WebSocket, Three.js, modern CSS/JS).

**Tested browsers on Zero1:**
- ❌ Chromium v92+ - Illegal instruction (missing NEON)
- ❌ Firefox ESR 128 - Illegal instruction (missing NEON)
- ❌ Lightweight browsers - Missing required web features

### Resolution Options

1. **Replace Zero1 with Pi Zero 2 W** (ARMv8, Chromium compatible) ✅ RECOMMENDED
2. **Use only pi5screen11** as the test screen
3. **Repurpose Zero1** for non-browser tasks (MQTT client, sensor node, etc.)

## Raspberry Pi OS Evolution & Kiosk Configuration

### Critical Change: Window Manager Transition

Raspberry Pi OS has migrated away from LXDE, breaking traditional autostart configurations:

| OS Version | Codename | Window Manager | Autostart File |
|------------|----------|----------------|----------------|
| Debian 10 | Buster | LXDE | `~/.config/lxsession/LXDE-pi/autostart` |
| Debian 12 | Bookworm | Wayland/Wayfire | `~/.config/wayfire.ini` |
| **Debian 13** | **Trixie** | **labwc** | `~/.config/labwc/autostart` |

**Both pi5screen11 and Zero1 run Trixie (Debian 13)** and therefore require `~/.config/labwc/autostart`.

### Initial Mistake: Wrong Autostart Location

Initial setup created `~/.config/lxsession/LXDE-pi/autostart` which is **completely ignored** on Trixie. Chromium appeared to install correctly but never launched on boot because labwc doesn't read LXDE config files.

## Working Configuration (pi5screen11)

### Auto-Login Setup

Configure the Pi to auto-login to graphical desktop:

```bash
sudo raspi-config nonint do_boot_behaviour B4
```

This sets:
- Boot target: `graphical.target`
- Auto-login: Enabled for user `john`

### labwc Autostart File

**Location:** `/home/john/.config/labwc/autostart`

**Contents:**
```bash
chromium-browser --no-first-run --password-store=basic --noerrdialogs --disable-infobars --kiosk http://192.168.4.148:8082?id=pi5screen11
```

### Key Chromium Flags

| Flag | Purpose |
|------|---------|
| `--no-first-run` | Skip first-run setup wizard |
| `--password-store=basic` | Suppress keyring unlock dialog |
| `--noerrdialogs` | Disable error popups |
| `--disable-infobars` | Remove info bars |
| `--kiosk` | Fullscreen mode, no browser UI |

**Important Notes:**
- **No backgrounding (`&`)** - labwc expects foreground commands
- **No xset commands** - labwc handles screen blanking configuration separately
- **Simple is better** - Complex flag combinations can cause display issues with Wayland

### Screen Blanking (Optional)

To disable screen blanking in labwc, add to `~/.config/labwc/autostart` before the chromium line:

```bash
xset s off
xset -dpms
xset s noblank
```

### Cursor Hiding

**Problem:** `unclutter` does not work with Wayland/labwc.

**Status:** No known working solution for hiding cursor in labwc kiosk mode as of April 2026.

**Workaround:** Acceptable for most use cases; cursor auto-hides during inactivity in some contexts.

## Installation Steps (pi5screen11)

### 1. Initial Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y chromium-browser unclutter xdotool
```

### 2. Configure Auto-Login

```bash
sudo raspi-config nonint do_boot_behaviour B4
```

### 3. Create labwc Autostart

```bash
mkdir -p ~/.config/labwc

cat > ~/.config/labwc/autostart << 'EOF'
chromium-browser --no-first-run --password-store=basic --noerrdialogs --disable-infobars --kiosk http://192.168.4.148:8082?id=pi5screen11
EOF
```

### 4. Reboot

```bash
sudo reboot
```

### 5. Verify

After reboot:
- Pi should auto-login to desktop
- Chromium should launch in fullscreen
- Display should show MarchogSystemsOps at `http://192.168.4.148:8082?id=pi5screen11`
- Screen should appear in config panel at `http://192.168.4.148:8082/config`

## Troubleshooting

### Chromium Not Launching

**Check if labwc is running:**
```bash
ps aux | grep labwc
```

**Check autostart file exists and is readable:**
```bash
cat ~/.config/labwc/autostart
ls -la ~/.config/labwc/
```

**Test Chromium manually:**
```bash
DISPLAY=:0 chromium-browser --kiosk http://192.168.4.148:8082?id=pi5screen11
```

### Wrong Autostart File Location

**Symptom:** Chromium installed but doesn't launch on boot.

**Diagnosis:** Check if wrong autostart file exists:
```bash
ls ~/.config/lxsession/LXDE-pi/autostart
```

**Fix:** Delete LXDE autostart (it's ignored anyway) and create labwc version:
```bash
rm -rf ~/.config/lxsession
mkdir -p ~/.config/labwc
cat > ~/.config/labwc/autostart << 'EOF'
chromium-browser --no-first-run --password-store=basic --noerrdialogs --disable-infobars --kiosk http://192.168.4.148:8082?id=SCREEN_ID_HERE
EOF
```

### Chrome Web Store Opens on Boot

**Symptom:** Chromium launches but shows Chrome Web Store instead of MarchogSystemsOps.

**Cause:** Missing `--no-first-run` flag or Chromium first-run state not cleared.

**Fix:** Add `--no-first-run` flag and clear Chromium config:
```bash
rm -rf ~/.config/chromium
```

Then recreate autostart file with proper flags.

### Illegal Instruction Error

**Symptom:** `Illegal instruction` when running Chromium.

**Diagnosis:**
```bash
uname -m
# If output is "armv6l" → INCOMPATIBLE
# If output is "aarch64" or "armv7l" → Compatible
```

**Resolution:** Replace with Pi Zero 2 W, Pi 3+, Pi 4, or Pi 5.

## Known Issues & Limitations

### 1. Raspberry Pi Zero Incompatibility
- **Status:** Unfixable hardware limitation
- **Affected:** All ARMv6 devices (Pi Zero, Pi Zero W)
- **Not Affected:** Pi Zero 2 W, Pi 3+, Pi 4, Pi 5

### 2. Cursor Visibility in Wayland
- **Status:** No working solution as of Trixie
- **Workaround:** None currently available
- **Traditional Fix:** `unclutter` (does not work with Wayland)

### 3. SSH Output Capture on Windows
- **Issue:** Desktop Commander on Windows loses stdout from external .exe programs (including SSH)
- **Impact:** Interactive SSH sessions don't show output properly via automation
- **Workaround:** Use ProcessStartInfo wrapper or run commands directly on Pi via keyboard/monitor

## Production Server Configuration

**Server:** appserv1 (192.168.4.148)  
**Port:** 8082  
**URL Pattern:** `http://192.168.4.148:8082?id={screen_id}`  
**Config Panel:** `http://192.168.4.148:8082/config`

### Screen IDs
- `pi5screen11` - Raspberry Pi 5 at 192.168.5.53
- `Zero1` - (Incompatible, not in use)

## Future Work

### Short Term
1. ✅ Configure pi5screen11 as operational kiosk display
2. ⬜ Acquire Pi Zero 2 W to replace Zero1
3. ⬜ Test multi-screen scene activation and playlists
4. ⬜ Document cursor hiding solution if one becomes available for labwc

### Long Term
1. ⬜ Android kiosk app (see `KIOSK_APP_REQUIREMENTS.md`)
2. ⬜ Content sync for offline operation
3. ⬜ Automated health monitoring and restart
4. ⬜ Remote screenshot capability

## References

### Raspberry Pi OS Documentation
- [Official Kiosk Mode Tutorial](https://www.raspberrypi.com/tutorials/how-to-use-a-raspberry-pi-in-kiosk-mode/)
- [Raspberry Pi Forums - labwc autostart](https://forums.raspberrypi.com/viewtopic.php?t=392472)
- [Raspberry Pi Forums - Wayland kiosk issues](https://forums.raspberrypi.com/viewtopic.php?t=363992)

### Known Issues
- [Chromium ARMv6 illegal instruction (GitHub)](https://github.com/RPi-Distro/chromium-browser/issues/21)
- [Pi Zero Chromium incompatibility (Forums)](https://forums.raspberrypi.com/viewtopic.php?t=323478)

### MarchogSystemsOps Docs
- `README.md` - Project overview and architecture
- `KIOSK_APP_REQUIREMENTS.md` - Future Android app specifications
- `SCREEN_DEVICE_TYPES.md` - Device taxonomy and screen management

---

**Document Status:** Living document, updated as configuration evolves  
**Last Updated:** April 11, 2026  
**Maintained By:** John M. Knight
