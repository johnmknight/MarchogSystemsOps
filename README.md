# MarchogSystemsOps

Star Wars inspired multi-screen display controller for themed room builds. Manage any number of screens from one control panel — assign pages, trigger scenes, run playlists. Built for kiosk deployment on local networks with no cloud dependency.

## Architecture

```
client/
  index.html              # Shell — iframe manager, WebSocket, playlists
  config.html             # Control panel — screens, rooms, pages, automations
  fonts/                  # Tabler Icons + Aurebesh font families
  pages/                  # Individual page files (loaded as iframes)
    pages.json            # Page registry with params (JSON, not DB)
    hyperspace.html       # Hyperspace jump canvas animation
    viewfinder.html       # Targeting computer HUD with Aurebesh
    standby.html          # Maintenance/standby screen + 3D logo
    logo-3d.html          # Animated 3D Marchog Systems logo
    video.html            # Video player (YouTube/MP4) + themed borders
    hangar-scan.html      # 3D wireframe perspective scanner
    selfdestruct.html     # Countdown timer with configurable abort
server/
  main.py                 # FastAPI + WebSocket + MQTT bridge + health monitor
  database.py             # SQLite: scenes, screen_configs, playlists, device types
  mqtt_bus.py             # MQTT client (threaded SelectorEventLoop for Windows)
  pages.py                # JSON-backed page CRUD
  rooms.py                # JSON-backed room/zone CRUD
  automations.json        # Automation definitions (triggers + actions)
  mosquitto.conf          # Mosquitto broker config (MQTT :1883, WS :9001)
docs/
  PUBSUB_ARCHITECTURE.md  # MQTT message bus design + implementation status
  ESP32_PROXY.md          # Virtual hardware simulator design
  SCREEN_DEVICE_TYPES.md  # 30 device types across 8 categories
  ARCHITECTURE_DIAGRAMS.html  # C4 diagrams, topic tree, message flows
  KIOSK_APP_REQUIREMENTS.md   # Android kiosk app spec
```

## Key Concepts

### Pages
Individual full-screen experiences loaded as iframes. Each page is a self-contained HTML file in `client/pages/`. Page definitions live in `pages.json` — a flat JSON array with id, name, file, icon, category, and an optional `params` object for page-specific configuration (e.g. video URL + border style for video pages).

### Rooms & Zones
Physical spaces organized hierarchically. A room contains zones (Bar, Airlock Door, Cockpit Bench), and zones contain screen assignments. Defined in `server/rooms.json`.

### Scenes
Named configurations that define what every screen displays. A scene maps screen IDs to either a static page or a playlist. Scenes live in SQLite (relational — they reference screens dynamically). One scene is active at a time; activating a scene pushes assignments to all connected screens instantly via WebSocket.

### Playlists
Ordered lists of pages with durations and transitions. Screens in playlist mode auto-cycle through their assigned pages. Playlist state runs client-side with progress reporting back to the server.

### Screen Management
Each browser window connects as a named screen via `?id=screen-name`. Screens register over WebSocket for real-time bidirectional control. The config panel shows all connected screens with live status, page assignment dropdowns, and remote commands (fullscreen, identify flash).

### Device Types
Each screen is assigned a primary device type (and optional secondary) from a taxonomy of 30 types across 8 categories: Access & Security, Navigation & Command, Engineering & Systems, Viewport & Atmospheric, Entertainment & Media, Display & Collection, Utility & Personal, Specialized. Device types enable group targeting — an automation can address all `door-panel` screens without knowing their IDs.

### MQTT Message Bus
Mosquitto broker runs alongside the server. All communication flows through MQTT topics organized by scope: `marchog/screen/{id}`, `marchog/type/{device_type}`, `marchog/zone/{zone_id}`, `marchog/room/{room_id}`, `marchog/all`. The server bridges MQTT ↔ WebSocket for browser screens. ESP32 devices, Raspberry Pi audio controllers, and LED strips connect directly to the broker via native MQTT.

### Automations
Named actions that trigger page navigation, lighting changes, audio cues, or prop control. Automations can target screens by ID, device type, zone, room, or broadcast. Stored in `automations.json` with trigger definitions and action lists.

### Health Monitoring
Server tracks `last_seen` timestamps for every screen. Background health monitor publishes stale-screen alerts via MQTT. Retained messages on `marchog/state/{id}` and `marchog/heartbeat/{id}` ensure new devices get current state on subscribe.

### Icons
All UI icons use [Tabler Icons](https://tabler.io/icons) webfont (MIT licensed). Icon values are stored as class names (e.g. `ti-rocket`, `ti-player-play`) in JSON configs and rendered as `<i class="ti ti-xxx">` elements. No emoji anywhere in the UI.

## Data Storage

| Data | Storage | Why |
|------|---------|-----|
| Pages | `client/pages/pages.json` | Static config, hand-editable, version-controlled |
| Rooms/Zones | `server/rooms.json` | Static config, rarely changes |
| Scenes | SQLite (`database.py`) | Relational — scenes reference screens dynamically |
| Screen configs | SQLite | Tied to scenes, need joins |
| Playlists | SQLite | Ordered entries tied to screen configs |

## Pages

| Page | Category | Description |
|------|----------|-------------|
| `hyperspace` | ambient | Star Wars hyperspace jump canvas animation |
| `viewfinder` | hud | Targeting computer HUD with Aurebesh fonts and reticles |
| `standby` | maintenance | Attention banner + animated 3D Marchog Systems logo |
| `logo-3d` | ambient | Standalone animated 3D logo |
| `video` | general | Video player (YouTube or direct MP4/WebM URL) with 6 themed border overlays |
| `hangar-scan` | general | 3D wireframe perspective scanner inspired by Last Jedi bridge displays |

### Video Page Border Styles
The video page supports canvas-drawn animated borders: **None**, **HUD** (corner brackets + scan tick), **Imperial** (heavy frame + data readouts), **Hologram** (scan lines + flicker), **Targeting** (rotating reticle + crosshair), **Data Feed** (Aurebesh side columns).

### Page Params
Pages can receive configuration via postMessage. When a page sends `pageReady`, the shell looks up its `params` from `pages.json` and sends a `configure` message. This enables creating multiple named video pages with different URLs and border styles from the config UI.

## API

| Endpoint | Description |
|---|---|
| `GET /api/pages` | List all pages (from JSON) |
| `POST /api/pages` | Register a new page |
| `PUT /api/pages/{id}` | Update page metadata + params |
| `DELETE /api/pages/{id}` | Remove a page registration |
| `POST /api/pages/scan` | Auto-discover new HTML files |
| `GET /api/rooms` | List rooms with zones and screen assignments |
| `POST /api/rooms` | Create a room |
| `PUT /api/rooms/{id}` | Update a room |
| `DELETE /api/rooms/{id}` | Delete room + zones |
| `POST /api/zones` | Create a zone in a room |
| `PUT /api/zones/{id}` | Update a zone |
| `DELETE /api/zones/{id}` | Delete a zone |
| `POST /api/zones/{id}/screens` | Assign a screen to a zone |
| `DELETE /api/zones/{id}/screens/{sid}` | Remove screen from zone |
| `GET /api/scenes` | List all scenes |
| `GET /api/scenes/active` | Get active scene |
| `POST /api/scenes` | Create a scene |
| `POST /api/scenes/{id}/activate` | Activate scene (pushes to all screens) |
| `PUT /api/scenes/{sid}/screens/{scr}` | Set screen config in scene |
| `DELETE /api/scenes/{sid}/screens/{scr}` | Remove screen from scene |
| `GET /api/screens` | List connected screens |
| `POST /api/screens/{id}/navigate` | Send navigation command |
| `PATCH /api/screens/{id}/device-type` | Update device type (primary + secondary) |
| `GET /api/device-types` | Full device type taxonomy (30 types, 8 categories) |
| `GET /api/automations` | List all automations |
| `POST /api/automations` | Create automation |
| `PUT /api/automations/{id}` | Update automation |
| `DELETE /api/automations/{id}` | Delete automation |
| `POST /api/automations/{id}/run` | Execute automation |
| `GET /api/mqtt/status` | MQTT broker connection status |
| `POST /api/mqtt/publish` | Publish to MQTT topic (testing) |
| `GET /api/health/screens` | Per-screen health: status, page, uptime, device type |
| `WS /ws/screen/{id}` | Screen WebSocket connection |

## Quick Start

```bash
start-marchogsystemsops.bat
# Open http://localhost:8082            — screen client
# Open http://localhost:8082?id=bar-tv  — named screen
# Open http://localhost:8082/config     — control panel
```

### Manual Start

```bash
cd server
venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8082 --reload
```

> **Note:** Always invoke via `venv\Scripts\python.exe -m uvicorn` — bare `uvicorn` may not be on PATH.

## Config Panel Features

The config panel (`/config`) provides:

- **Connected Screens** — live status, page assignment dropdowns, remote fullscreen/identify commands
- **Rooms & Zones** — paginated room view, add/edit/delete rooms and zones, assign screens to zones
- **Pages** — card grid of all registered pages, add/edit/delete, scan directory for new HTML files
- **Video Params** — when adding/editing a page with `video.html`, a sub-form appears for video URL + border style picker

## Roadmap

### Completed
- MQTT message bus with Mosquitto broker + threaded Python client
- 30 device types with primary/secondary assignment and group targeting
- Heartbeat, state publishing, health monitoring with stale detection
- Automation engine with run/edit/create from config UI
- Self-destruct countdown page with configurable abort
- Page thumbnail generation with Playwright
- PWA manifest for kiosk deployment

### Next: Usability Quick Wins (Phase 4)
Close the pitch-product gap before beta testing:
- Screen naming & human-readable labels
- Scene quick-launch bar (one-tap scene triggering)
- Client auto-reconnect with themed visual feedback
- Enhanced screen health dashboard (FPS, memory, uptime %)

### After: Content Delivery (Phase 5)
Deliver on the pitch's content promises:
- Local/network video playback (MP4/WebM, not just YouTube)
- 2-3 live data pages (weather, clock, news ticker)
- Saved page parameter presets

### Then: ESP32 Proxy (Phase 6)
Python-based virtual hardware simulator — test the full MQTT pipeline
(buttons → automations → screens + lights + audio) without physical
ESP32 boards. See `docs/ESP32_PROXY.md`.

### Then: Choreography & Scheduling (Phase 7)
Timed sequences, chained automations, and cron-like scene scheduling
for multi-device coordinated events.

### Later
- Mobile-optimized config panel + scene preview + undo
- Media manager with remote upload + screen preview thumbnails
- Backup/export/restore + diagnostic page
- Content template library / visual page builder
- Audio zone support, multi-user access control
- Android kiosk app with native MQTT client
- Home Assistant integration via MQTT bridge
- Docker Compose deployment + demo video

## Tech Stack

- **Server:** Python 3.12, FastAPI, uvicorn, aiosqlite, aiomqtt
- **Broker:** Mosquitto (MQTT :1883, WebSocket :9001)
- **Client:** Vanilla JavaScript, HTML5 Canvas, CSS3
- **Fonts:** Tabler Icons (MIT), Aurebesh family (8 styles), Orbitron, Share Tech Mono
- **Data:** SQLite (scenes/configs/device types) + JSON files (pages/rooms/automations)
- **Comms:** MQTT (device bus) + WebSocket (browser screens) + REST API (CRUD)

## Port: 8082

## Easter Egg
"Marchog" is Welsh for "knight."
