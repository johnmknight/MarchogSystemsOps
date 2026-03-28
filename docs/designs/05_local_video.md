# Design: Media Architecture & Kiosk Agent

**Product Review Item:** Gap analysis -- "Keep using all your existing content"
**Production Queue:** Phase 5
**Priority:** HIGH -- Delivers on the core pitch promise
**Architecture Diagram:** See `media_architecture.html` (interactive)

---

## Problem

The pitch promises "those MP4 loops you've already built work as-is" but room
builders' existing content lives on USB drives, NAS shares, and local files --
not YouTube. The current architecture streams all media from the central server,
which creates a network bottleneck with multiple 4K screens.

A beta tester who has 20 MP4 loops on a USB drive needs a path from "files on
disk" to "playing on screen with a themed border" -- without saturating the LAN.

---

## Architecture Overview

Two-tier media delivery with a local agent on each kiosk device:

```
Central Server                    Kiosk Device
+------------------+              +---------------------------+
|                  |   WS/HTTP    |  Kiosk Agent (:9090)      |
|  Media Catalog   |<------------>|    - Local HTTP server     |
|  Asset Registry  |  control +   |    - Media sync manager    |
|  Scene Engine    |  telemetry   |    - Device management     |
|  Config API      |              |    - Telemetry reporter    |
|                  |              +---------------------------+
|  /media/ static  |                        |
|  (fallback)      |              +---------------------------+
+------------------+              |  Browser (kiosk mode)     |
                                  |    - Client shell          |
                                  |    - Media URL rewriter    |
                                  |    - Loads from server     |
                                  |    - Media from agent      |
                                  +---------------------------+
```

**Control plane:** Central server -> WebSocket -> client shell (unchanged).
**Media plane:** Client shell rewrites asset IDs to local agent URLs.
**Fallback:** If no local agent, client streams from central server.

---

## Current State

**Already built:**
- `video.html` detects YouTube vs direct video URLs, plays both
- `<video>` element with autoplay, loop, border overlays
- Page params system: shell sends `{video: "...", border: "..."}` via postMessage
- WebSocket control plane for all screen navigation

**What's missing:**
- Server-side media catalog and static serving
- Kiosk agent for local media delivery and device management
- Client-side media URL rewriting
- UI labels still say "YouTube"

---

## Part 1: Server-Side Media Library

The central server is the single source of truth for all media assets.

### Directory structure

```
MarchogSystemsOps/
+-- media/
|   +-- videos/
|   |   +-- engine-room.mp4
|   |   +-- hyperspace-loop.mp4
|   +-- images/
+-- server/
+-- client/
```

### Static mount

```python
MEDIA_DIR = Path(__file__).parent.parent / "media"
MEDIA_DIR.mkdir(exist_ok=True)
(MEDIA_DIR / "videos").mkdir(exist_ok=True)
app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")
```

### Media catalog API

```
GET /api/media/videos
```
Returns:
```json
[
  {
    "asset_id": "engine-room.mp4",
    "filename": "engine-room.mp4",
    "size": 52428800,
    "url": "/media/videos/engine-room.mp4",
    "content_type": "video/mp4",
    "duration_seconds": null,
    "checksum": "sha256:abc123..."
  }
]
```

The `asset_id` is the filename. The `checksum` enables sync verification --
the agent can confirm it has the correct version without re-downloading.

### Asset references

Throughout the system, media is referenced by `asset_id`, not URL:
- Scene assignments: `{ "page": "video", "params": { "asset": "engine-room.mp4" } }`
- The client shell resolves the asset ID to a playable URL at runtime

---

## Part 2: Kiosk Agent

A lightweight Python daemon running on each kiosk device. Single script,
minimal dependencies, runs as a system service.

### 2.1 Local HTTP Media Server

**Primary function.** Serves media files from a local directory to the
browser running on the same device.

```
GET http://localhost:9090/media/videos/engine-room.mp4
GET http://localhost:9090/status
```

Configuration:
```json
{
  "server_url": "http://YOUR_SERVER_IP:8082",
  "screen_id": "bar-left-monitor",
  "media_dir": "/opt/marchog/media",
  "agent_port": 9090
}
```

The browser client accesses `localhost:9090` -- no CORS issues, no network
latency, no bandwidth contention with other screens.

### 2.2 Media Sync Manager

The agent pulls media from the central server on demand.

**Sync triggers:**
- Server sends `sync_media` command via agent WebSocket
- Agent polls `/api/media/manifest` on a schedule (e.g. every 5 min)
- Manual trigger via agent API

**Sync flow:**
1. Agent fetches manifest from server: list of asset_ids + checksums
2. Compares against local files
3. Downloads missing/changed files from `server/media/videos/{filename}`
4. Deletes local files not in manifest (if `auto_cleanup` enabled)
5. Reports sync result back to server

**Server-initiated operations:**
```
POST agent:9090/api/media/sync         -- trigger full sync
POST agent:9090/api/media/pull         -- pull specific asset
  { "asset_id": "engine-room.mp4" }
DELETE agent:9090/api/media/{asset_id}  -- delete local copy
```

**Agent -> server reporting:**
```
POST server/api/agent/{screen_id}/media-status
{
  "local_assets": ["engine-room.mp4", "hyperspace-loop.mp4"],
  "pending_sync": ["cantina-band.mp4"],
  "last_sync": "2026-02-22T17:00:00Z",
  "sync_errors": []
}
```

### 2.3 Disk Space Reporting

The agent reports storage availability so the server can make informed
decisions about which assets to push to which devices.

```
POST server/api/agent/{screen_id}/telemetry
{
  ...
  "disk_total_gb": 64.0,
  "disk_free_gb": 41.2,
  "disk_media_gb": 18.3,
  "media_dir": "/opt/marchog/media"
}
```

The server's config panel shows per-device storage in the Device Health
section. Admins can see which devices are running low and manage assets
accordingly. The server should warn before pushing media to a device with
insufficient space.

### 2.4 Battery Status

For tablet and laptop kiosks. Report battery level and charging state.

```json
{
  "battery_percent": 72,
  "battery_charging": true,
  "battery_time_remaining_min": null,
  "power_source": "ac"
}
```

**Platform detection:**
- Linux: read `/sys/class/power_supply/BAT0/`
- Windows: `psutil.sensors_battery()`
- macOS: `pmset -g batt` parsed
- Desktop/no battery: omit field (server treats null as "always powered")

Included in the telemetry payload. Server can surface low-battery warnings
in Device Health and optionally trigger power-saving scenes.

### 2.5 Remote Reboot

The server can command a device reboot through the agent.

```
POST agent:9090/api/device/reboot
Authorization: Bearer {agent_token}
```

**Safety:**
- Requires auth token (shared secret set during agent install)
- Agent logs the reboot command and source
- 5-second delay before executing (allows confirmation/cancel)
- Server UI requires explicit confirmation ("Are you sure?")

**Implementation:**
- Linux: `sudo shutdown -r now` (agent runs with reboot permission)
- Windows: `shutdown /r /t 5`

### 2.6 Remote Configuration

Post-install config updates pushed from the server, so admins don't
need physical access to devices after initial setup.

**Configurable settings:**
```json
{
  "server_url": "http://YOUR_SERVER_IP:8082",
  "screen_id": "bar-left-monitor",
  "media_dir": "/opt/marchog/media",
  "agent_port": 9090,
  "sync_interval_min": 5,
  "auto_cleanup": true,
  "telemetry_interval_sec": 60,
  "log_level": "info"
}
```

**Push flow:**
```
POST agent:9090/api/config
Authorization: Bearer {agent_token}
{ "sync_interval_min": 10, "auto_cleanup": false }
```

Agent validates, applies, persists to local config file, and restarts
affected services. Server config panel has a per-device settings editor.

**Pull flow (agent-initiated):**
On startup, agent can optionally fetch config from:
```
GET server/api/agent/{screen_id}/config
```
This enables zero-touch provisioning: plug in a device with only
`server_url` and `screen_id` set, and it pulls everything else.

### 2.7 Telemetry

The agent posts device health telemetry to the central server on a
regular interval (default: 60 seconds).

```
POST server/api/agent/{screen_id}/telemetry
{
  "timestamp": "2026-02-22T17:30:00Z",
  "agent_version": "0.1.0",
  "uptime_seconds": 86400,
  "cpu_percent": 12.5,
  "memory_percent": 45.2,
  "memory_used_mb": 1840,
  "disk_total_gb": 64.0,
  "disk_free_gb": 41.2,
  "disk_media_gb": 18.3,
  "battery_percent": null,
  "battery_charging": null,
  "network": {
    "interface": "eth0",
    "ip": "YOUR_DEVICE_IP",
    "ssid": null,
    "signal_dbm": null
  },
  "temperature_c": 52.0,
  "display": {
    "resolution": "3840x2160",
    "connected": true
  },
  "local_assets_count": 12,
  "last_sync": "2026-02-22T17:00:00Z",
  "errors": []
}
```

**Server-side storage:** Telemetry stored in memory (latest per screen)
and optionally persisted to SQLite for history/graphing.

**Config panel integration:** Device Health section shows agent telemetry
alongside browser client metrics (FPS, heap). Agent data covers the
hardware layer; browser data covers the rendering layer.

---

## Part 3: Client-Side Media Resolution

The client shell resolves asset IDs to playable URLs. This is the bridge
between the server's abstract asset references and actual playback.

### Media resolver

```javascript
// In client shell (index.html)
resolveMediaUrl(assetId) {
  // 1. Check if local agent is available
  if (this.agentUrl) {
    return `${this.agentUrl}/media/videos/${assetId}`;
  }
  // 2. Fallback to central server
  return `/media/videos/${assetId}`;
}
```

### Agent discovery

On startup, the client shell probes for a local agent:

```javascript
async discoverAgent() {
  try {
    const r = await fetch('http://localhost:9090/status', { timeout: 2000 });
    if (r.ok) {
      this.agentUrl = 'http://localhost:9090';
      console.log('Local agent detected');
    }
  } catch {
    this.agentUrl = null;
    console.log('No local agent, using server for media');
  }
}
```

The agent port (9090) can be overridden via screen config from the server.

### Page integration

Pages never deal with resolution. The shell resolves before passing params:

```javascript
// When server sends: { page: "video", params: { asset: "engine-room.mp4" } }
const resolvedParams = {
  ...params,
  video: this.resolveMediaUrl(params.asset)
};
// Page receives: { video: "http://localhost:9090/media/videos/engine-room.mp4" }
```

---

## Part 4: Platform Considerations

The kiosk agent is Python-based. Platform-specific behavior:

| Capability       | Linux (Pi/NUC)          | Windows              | macOS              | Android            |
|------------------|-------------------------|----------------------|--------------------|--------------------|
| Media serving    | Python HTTP server      | Python HTTP server   | Python HTTP server | Future native app  |
| Media sync       | HTTP download           | HTTP download        | HTTP download      | Future native app  |
| Disk reporting   | `shutil.disk_usage()`   | `shutil.disk_usage()`| `shutil.disk_usage()` | N/A            |
| Battery          | `/sys/class/power_supply` | `psutil`           | `pmset`            | Native API         |
| Reboot           | `shutdown -r`           | `shutdown /r`        | `shutdown -r`      | N/A                |
| Temperature      | `vcgencmd` (Pi) / `sensors` | WMI             | `powermetrics`     | N/A                |
| Service install  | systemd unit            | NSSM / Task Scheduler| launchd plist     | N/A                |

### Minimal install

```bash
# On kiosk device:
pip install marchog-agent
marchog-agent --server http://YOUR_SERVER_IP:8082 --screen-id bar-left
```

Or with a config file:
```bash
marchog-agent --config /etc/marchog/agent.json
```

---

## Part 5: Server Config Panel Integration

### Device Health (enhanced)

The existing Device Health section in config.html gains agent telemetry:

```
+--------------------------------------------------+
| Bar Left Monitor  test-screen-1  [ONLINE]        |
|                                                  |
| Page       standby        FPS    60              |
| Uptime     4d 12h         Heap   84 / 87 MB     |
| Last ping  3s ago         Viewport 1920x1080     |
|                                                  |
| -- Agent --                                      |
| CPU        12%            Disk   41.2 / 64 GB    |
| Memory     45%            Media  18.3 GB         |
| Temp       52C            Assets 12 synced       |
| Battery    -- (AC)        Last sync 30m ago      |
|                                                  |
| [SYNC MEDIA] [REBOOT] [CONFIG]                   |
+--------------------------------------------------+
```

### Media Manager (future, Phase 9)

- Upload media through config panel -> server `/media/`
- Push to specific devices or groups
- See per-device sync status
- Storage warnings when devices are low

---

## Security

- Agent API is **localhost-only** by default (binds to 127.0.0.1)
- Remote management endpoints (reboot, config, sync) require auth token
- Auth token is a shared secret set during install, passed as Bearer header
- Server stores per-device agent tokens in the screen registry
- Agent -> server telemetry uses the same screen_id + token for auth
- No sensitive data in telemetry (no passwords, no user data)

---

## Implementation Phases

### Phase 5a: Server media library (1 session)
- `media/` directory + FastAPI static mount
- `GET /api/media/videos` catalog endpoint
- Video page UI: relabel input, add media picker
- Config panel: media picker in page params

### Phase 5b: Kiosk agent MVP (2-3 sessions)
- Single Python script: `marchog_agent.py`
- Local HTTP server for media files
- Agent `/status` endpoint
- Client shell: agent discovery + URL rewriting
- Manual media copy (no sync yet)

### Phase 5c: Media sync + telemetry (2-3 sessions)
- Manifest-based sync from server
- Disk space + basic telemetry reporting
- Server telemetry API + Device Health UI
- Sync trigger from config panel

### Phase 5d: Device management (1-2 sessions)
- Remote reboot
- Remote config push/pull
- Battery reporting (platform-specific)
- Service installer scripts (systemd, NSSM)

---

## Estimated total effort
6-9 sessions across phases 5a-5d
