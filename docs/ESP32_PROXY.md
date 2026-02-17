# ESP32 Proxy — Virtual Hardware for MQTT Testing

## Problem

You need to test the full MQTT pipeline — button presses trigger automations,
LED strips respond to lighting commands, sensors publish presence data — but
your ESP32 boards are packed away somewhere. You shouldn't need physical
hardware to validate that the message bus works end-to-end.

## Solution

A Python script that simulates ESP32 devices on the MQTT bus. Each "virtual
device" subscribes and publishes exactly like real hardware would. The proxy
runs alongside the server on your dev machine.

When real ESP32s arrive, you swap the proxy for Arduino firmware. The MQTT
topics and message formats are identical — no server changes needed.

## Virtual Devices

### 1. Button Panel (`esp32-proxy-buttons`)
**Simulates**: Physical buttons (big red self-destruct, keypad, toggles)

**Publishes to:**
- `marchog/action/self-destruct` — big red button
- `marchog/action/red-alert` — alert toggle
- `marchog/action/all-clear` — reset
- `marchog/action/lockdown` — keypad code entry

**Proxy interface:** HTTP API or keyboard input
- `POST /proxy/button/self-destruct` triggers publish
- Or keyboard: press `1` = self-destruct, `2` = red-alert, `3` = all-clear

**Real ESP32 equivalent:** Button + ESP32 + WiFi, ~20 lines of Arduino

### 2. LED Strip Controller (`esp32-proxy-leds`)
**Simulates**: NeoPixel/WS2812B LED strips per-zone

**Subscribes to:**
- `marchog/lighting/all`
- `marchog/lighting/room/{room_id}`
- `marchog/lighting/zone/{zone_id}`

**Receives commands like:**
```json
{
  "type": "lighting",
  "mode": "red-alert",
  "color": "#ff0000",
  "brightness": 100,
  "effect": "pulse"
}
```

**Proxy output:** Prints color/effect to terminal with ANSI colors
- `🔴 ZONE corridor-a: RED PULSE brightness=100`
- `🟢 ZONE corridor-a: GREEN SOLID brightness=50`

**Real ESP32 equivalent:** ESP32 + NeoPixel strip + FastLED library

### 3. Motion Sensor (`esp32-proxy-motion`)
**Simulates**: PIR motion sensor in a zone

**Publishes to:**
- `marchog/sensor/{sensor_id}/motion` — motion detected
- `marchog/presence/room/{room_id}` — occupancy state

**Proxy interface:** Timer-based or keyboard
- Auto-publishes motion every N seconds (simulates walk-through)
- Or keyboard: `m` = motion detected, `c` = cleared

**Real ESP32 equivalent:** ESP32 + PIR sensor, publishes on interrupt

### 4. Audio Controller (`esp32-proxy-audio`)
**Simulates**: Raspberry Pi with speakers

**Subscribes to:**
- `marchog/audio/all`
- `marchog/audio/room/{room_id}`

**Receives commands like:**
```json
{
  "type": "audio",
  "action": "play",
  "file": "klaxon.mp3",
  "loop": true,
  "volume": 80
}
```

**Proxy output:** Plays audio files from a local sounds folder using system audio
- Falls back to printing `🔊 PLAY klaxon.mp3 vol=80 loop=true` if no audio

**Real equivalent:** RPi + speakers + Python paho-mqtt + pygame

---

## Architecture

```
┌──────────────────────┐
│   ESP32 Proxy        │
│   (Python script)    │
│                      │
│  ┌─ Button Panel ──┐ │       ┌──────────────┐
│  │ keyboard/HTTP   │─┼──────►│              │
│  │ → publishes     │ │  MQTT │  Mosquitto   │
│  └─────────────────┘ │       │  Broker      │
│                      │       │  :1883       │
│  ┌─ LED Strip ─────┐ │       │              │
│  │ subscribes      │◄┼───────│              │
│  │ → prints color  │ │       │              │       ┌──────────────┐
│  └─────────────────┘ │       │              │◄─────►│  FastAPI     │
│                      │       │              │ MQTT  │  Server      │
│  ┌─ Motion Sensor ─┐ │       │              │       │              │
│  │ timer/keyboard  │─┼──────►│              │       └──────────────┘
│  │ → publishes     │ │       │              │
│  └─────────────────┘ │       │              │       ┌──────────────┐
│                      │       │              │◄═════►│  Browser     │
│  ┌─ Audio Ctrl ────┐ │       │              │  WS   │  Screens     │
│  │ subscribes      │◄┼───────│              │bridge │              │
│  │ → plays sound   │ │       └──────────────┘       └──────────────┘
│  └─────────────────┘ │
└──────────────────────┘
```


## Implementation

Single Python script: `server/esp32_proxy.py`

```python
# Run alongside server:
# python esp32_proxy.py
#
# Keyboard controls:
#   1 = Self-destruct button
#   2 = Red alert toggle
#   3 = All clear
#   4 = Lockdown
#   m = Motion detected
#   c = Motion cleared
#   q = Quit
```

**Dependencies:** `aiomqtt` (already installed), optionally `pygame` for audio

**Key design points:**
- Uses same `aiomqtt` + `SelectorEventLoop` pattern as mqtt_bus.py
- Each virtual device is an async task
- Keyboard input via `asyncio` stdin reader (or HTTP API via aiohttp)
- LED output uses ANSI escape codes for colored terminal output
- Audio output via `pygame.mixer` if available, otherwise prints
- All message formats match what real ESP32 firmware would send/receive
- Configurable room/zone assignment via command-line args or config

## What This Proves

Before buying/finding any hardware:
1. **Button → Automation → Screens**: Press `1`, self-destruct page loads on all door-panels
2. **Lighting cascade**: Red alert automation triggers, proxy shows red pulse on LED virtual device
3. **Presence detection**: Motion sensor fires, screens in that zone wake from standby
4. **Audio integration**: Self-destruct plays klaxon through proxy audio output
5. **Full choreography**: Timed sequence across all virtual device types

## Migration to Real Hardware

When ESP32s are found/purchased:
1. Flash Arduino firmware that uses `PubSubClient` (MQTT library)
2. Same topic subscriptions as proxy
3. Same JSON message format
4. Server sees identical messages — zero server changes
5. Proxy and real hardware can coexist (useful for mixed testing)

## Stretch: Web-based Proxy UI

Instead of keyboard controls, a small HTML page with buttons:
- Big red SELF DESTRUCT button
- Toggle switches for each action
- LED strip visualization (CSS animations matching the commands received)
- Live log of all MQTT messages flowing through
- Could be another page in the MarchogSystemsOps client (`client/pages/proxy.html`)

This gives you a visual "hardware simulator" in the browser while
the real MQTT messages flow through the actual broker.
