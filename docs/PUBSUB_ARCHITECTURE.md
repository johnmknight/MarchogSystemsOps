# Pub/Sub Architecture — MQTT Message Bus

## Overview

MarchogSystemsOps adopts MQTT as its core message bus. Every device — screens,
physical buttons, sensors, lighting controllers, audio systems, props — is a
participant on the bus. The server is one participant, not the hub. This enables
device types beyond web browsers, chained automations, and zero-code integration
for any MQTT-capable hardware.

---

## Why MQTT

- **Universal protocol** — ESP32, Arduino, Raspberry Pi, Android, Python, JS all speak it
- **Topic-based routing** — maps directly to our room/zone/device-type hierarchy
- **Retained messages** — new devices get current state immediately on subscribe
- **Last Will and Testament** — broker knows when a device disconnects
- **Lightweight** — runs on a Pi, sub-millisecond delivery on LAN
- **Decoupled** — publishers don't know subscribers, nothing breaks when you add/remove devices
- **Bridgeable** — multiple brokers can federate across buildings/networks

---

## Broker

**Mosquitto** — open source, battle-tested, runs on any platform.

Install:
- Windows: `choco install mosquitto` or download from mosquitto.org
- Linux/Pi: `apt install mosquitto mosquitto-clients`
- Config: listener on port 1883 (no TLS for LAN), WebSocket listener on 9001

The server runs the broker OR connects to an existing one. For single-server
installs, Mosquitto runs alongside the FastAPI server. For multi-server or
HA-integrated setups, it can be external.

---

## Topic Hierarchy

```
marchog/
├── screen/{screen_id}          # Direct to specific screen
├── type/{device_type}          # All screens of a device type
├── zone/{zone_id}              # All devices in a zone
├── room/{room_id}              # All devices in a room
├── all                         # Every connected device
├── action/{action_name}        # Named automation triggers
├── event/{source}/{event}      # Events from devices/UI
├── audio/{scope}               # Sound system commands
├── lighting/{scope}            # Lighting commands
├── prop/{prop_id}              # Physical prop control
├── sensor/{sensor_id}          # Sensor data inbound
├── presence/{scope}            # Occupancy/presence
├── heartbeat/{device_id}       # Device health pings
├── state/{device_id}           # Retained current state
└── alert/{alert_type}          # System alerts
```

### Scope patterns
- `marchog/lighting/all` — all lighting devices
- `marchog/lighting/room/bridge` — lighting in the bridge
- `marchog/lighting/zone/corridor-a` — lighting in corridor A
- `marchog/audio/room/cantina` — audio in the cantina

### Retained messages
These topics use retained messages (broker stores last value):
- `marchog/state/{device_id}` — current page/mode
- `marchog/heartbeat/{device_id}` — last known alive time
- `marchog/presence/{scope}` — current occupancy state

---

## Device Subscriptions

Each device subscribes to topics based on its identity:

### Screen (e.g. door panel in Bridge Entrance, Smugglers Room)
```
marchog/all
marchog/room/smugglers-room
marchog/zone/bridge-entrance
marchog/type/door-panel              ← primary type
marchog/type/navigation-panel        ← secondary type (if set)
marchog/screen/scr-abc123            ← direct addressing
```

### ESP32 Button
```
Publishes to: marchog/action/self-destruct
Subscribes to: nothing (fire-and-forget)
```

### ESP32 LED Strip (corridor lighting)
```
marchog/all
marchog/lighting/all
marchog/lighting/room/smugglers-room
marchog/lighting/zone/corridor-a
```

### Raspberry Pi Audio (bridge speakers)
```
marchog/all
marchog/audio/all
marchog/audio/room/bridge
```

### Motion Sensor
```
Publishes to: marchog/sensor/corridor-a-motion
Subscribes to: nothing
```

---

## Message Format

All messages are JSON:

```json
{
  "type": "navigate",
  "page_id": "selfdestruct",
  "params": { "countdown": 60, "abort_at": 10 },
  "source": "automation:self-destruct-sequence",
  "timestamp": "2026-02-17T02:00:00Z"
}
```

```json
{
  "type": "lighting",
  "mode": "red-alert",
  "color": "#ff0000",
  "brightness": 100,
  "effect": "pulse",
  "source": "automation:red-alert",
  "timestamp": "2026-02-17T02:00:00Z"
}
```

```json
{
  "type": "audio",
  "action": "play",
  "file": "klaxon.mp3",
  "loop": true,
  "volume": 80,
  "source": "automation:self-destruct-sequence",
  "timestamp": "2026-02-17T02:00:00Z"
}
```

```json
{
  "type": "heartbeat",
  "device_id": "scr-abc123",
  "device_type": "door-panel",
  "status": "online",
  "page": "standby",
  "uptime": 3600,
  "timestamp": "2026-02-17T02:00:00Z"
}
```

---

## Server Role

The FastAPI server becomes a participant, not the hub:

### Server publishes:
- `marchog/state/{screen_id}` — when it assigns a page
- `marchog/alert/device-offline` — when heartbeat monitoring detects dropout
- Automation results to relevant topics

### Server subscribes:
- `marchog/heartbeat/#` — track device health
- `marchog/sensor/#` — ingest sensor data for automations
- `marchog/event/#` — capture events for logging and automation triggers
- `marchog/action/#` — listen for automation trigger requests

### Server bridges:
- MQTT ↔ WebSocket for browser-based screens
- Browser screens can't speak MQTT natively, so the server subscribes on
  their behalf and forwards messages over WebSocket
- The Android kiosk app can speak MQTT directly, bypassing the bridge

---

## Automation System Changes

### Current model
```json
{
  "actions": [{
    "type": "navigate",
    "page_id": "selfdestruct",
    "params": { "countdown": 60 },
    "targets": ["scr-abc", "scr-def"]
  }]
}
```

### New model with pub/sub targeting
```json
{
  "actions": [{
    "type": "navigate",
    "page_id": "selfdestruct",
    "params": { "countdown": 60 },
    "publish_to": ["marchog/type/door-panel", "marchog/type/airlock-panel"]
  }],
  "triggers": [{
    "type": "mqtt",
    "topic": "marchog/action/self-destruct"
  }]
}
```

### Backward compatible
- `targets: [screen_ids]` still works — server publishes to each `marchog/screen/{id}`
- `publish_to: [topics]` is the new way — direct topic publishing
- `scope` + `filter` from the UI resolves to topic list at save time

---

## Choreography — Chained Sequences

Automations can chain by publishing events that trigger other automations:

```
Self Destruct Sequence (master):
  T=0:   publish marchog/type/door-panel       → lockdown page
         publish marchog/action/red-alert       → triggers Red Alert automation
  T=5:   publish marchog/type/all-screens       → selfdestruct page
         publish marchog/audio/all              → klaxon.mp3
  T=25:  publish marchog/lighting/all           → strobe white
  T=30:  publish marchog/prop/fog-machine       → fire
         publish marchog/lighting/all           → flash then blackout

Red Alert (triggered by marchog/action/red-alert):
  publish marchog/lighting/all                  → red pulse
  publish marchog/audio/all                     → alert tone
```

The master sequence doesn't know about lighting hardware or audio equipment.
It publishes to topics. Whatever is subscribed gets the message.

---

## Device Types That Benefit Immediately

### Physical buttons (ESP32)
- $3 hardware, 20 lines of Arduino code
- Big red button → `marchog/action/self-destruct`
- Keypad → `marchog/action/{code-entered}`
- Toggle switch → `marchog/sensor/airlock-switch/state`

### LED lighting (ESP32 + NeoPixel)
- Subscribe to `marchog/lighting/zone/{zone}`
- Receive color, brightness, effect commands
- Independent of Home Assistant
- Per-zone, per-room, or global control

### Audio (Raspberry Pi + speakers)
- Subscribe to `marchog/audio/room/{room}`
- Play files, control volume, loop
- Ambient soundscapes, alerts, effects

### Motion/presence sensors (ESP32 + PIR/BLE)
- Publish to `marchog/presence/room/{room}`
- Screens wake on entry, sleep on empty
- Visitor counting for guest mode

### Physical props (ESP32 + relay/servo/solenoid)
- Door locks, fog machines, motorized panels
- Subscribe to `marchog/prop/{prop_id}`
- Participate in choreographed sequences

---

## Browser Screen MQTT Bridge

Browser clients can't connect to MQTT directly (without a JS MQTT library
over WebSockets). Two options:

### Option A: Server-side bridge (recommended for now)
- Server subscribes to all topics relevant to connected screens
- Forwards messages over existing WebSocket connections
- Screen registration tells server what topics to subscribe for it
- Minimal client-side changes

### Option B: Client-side MQTT.js (future)
- Mosquitto WebSocket listener on port 9001
- Browser loads mqtt.js library
- Screen subscribes directly to its topics
- Server bridge no longer needed for screens
- Better for scale, but adds client complexity

### Recommendation
Start with Option A. The existing WebSocket infrastructure stays. The server
gains MQTT as a second transport. Browser screens don't change at all — they
still receive the same JSON messages over WebSocket. The server just gets
those messages from MQTT instead of generating them internally.

The Android kiosk app uses MQTT natively from day one.

---

## Implementation Phases

### Phase 1: Broker + Server Integration
- Install Mosquitto alongside server
- Add `aiomqtt` (async MQTT client) to server dependencies
- Server connects to broker on startup
- Server publishes automation results to MQTT topics
- Server subscribes to `marchog/action/#` for external triggers
- Existing WebSocket flow unchanged — server bridges MQTT → WebSocket

### Phase 2: Device Type Targeting
- Add `device_type` and `device_type_secondary` to screen_configs
- UI dropdown for device type selection
- Automation editor: scope + filter → resolved to MQTT topics
- Server subscribes on behalf of each browser screen based on its types

### Phase 3: Heartbeat + State
- Screens publish heartbeat every 30s via server bridge
- Server monitors heartbeats, publishes offline alerts
- Retained messages for current state — new devices get instant state
- Config UI shows health status from heartbeat data

### Phase 4: Physical Devices
- ESP32 button example with Arduino sketch
- ESP32 LED strip example with NeoPixel
- Document topic conventions for hardware builders
- Test: button press → automation → screens + lights respond

### Phase 5: Choreography
- Timed sequence support in automations
- Chained automation triggers via MQTT events
- Audio integration example
- Full "Self Destruct" demo: screens + lights + sound + props

---

## Dependencies

- **Mosquitto** — MQTT broker (install on server machine)
- **aiomqtt** — Python async MQTT client (`pip install aiomqtt`)
- **paho-mqtt** — underlying MQTT library (installed with aiomqtt)

No cloud services. No external APIs. Everything runs on LAN.

---

## Migration Path

The existing system continues working throughout migration:
1. WebSocket connections remain for browser screens
2. Automations with `targets: [screen_ids]` keep working
3. MQTT adds new capabilities alongside existing ones
4. Nothing breaks — MQTT is additive, not replacement

When the Android kiosk app arrives, it speaks MQTT natively.
When ESP32 devices arrive, they speak MQTT natively.
Browser screens get MQTT messages bridged through the server.

The bus is the backbone. Everything else plugs in.

---

## Related Documents
- [SCREEN_DEVICE_TYPES.md](./SCREEN_DEVICE_TYPES.md) — Device type taxonomy
- [KIOSK_APP_REQUIREMENTS.md](./KIOSK_APP_REQUIREMENTS.md) — Android kiosk app
- [PITCH_BRIAN.md](./PITCH_BRIAN.md) — Project pitch
