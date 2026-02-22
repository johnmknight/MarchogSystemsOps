# Design: Screen Health Dashboard Enhancement

**Product Review Item:** #1 — Screen Health Dashboard
**Production Queue:** Phase 4
**Priority:** CRITICAL — Essential for production reliability

---

## Problem

Room builders with 8-20+ embedded screens need instant visibility into screen health.
A screen behind a greeblied panel that silently crashes or degrades is invisible until
someone physically checks. The current health monitoring tracks last-seen timestamps
and publishes stale alerts, but doesn't surface FPS, memory, network quality, or
historical uptime — the data operators need for proactive maintenance.

---

## Current State

**What exists:**
- Server background task `_health_monitor` checks every 30s for screens >90s since last ping
- Publishes `marchog/alert/stale-screen` for stale screens
- `GET /api/health/screens` returns per-screen: status, page, uptime, last_seen, device_type, zone, room
- Config UI has a "Device Health" section with MQTT badge and health card grid (auto-refresh 30s)
- Client sends `ping` over WebSocket, server tracks `last_seen` in `app_state`

**What's missing:**
- Client-side performance metrics (FPS, memory, CPU)
- Network latency measurement (round-trip ping time)
- Uptime percentage calculation (historical)
- Color-coded severity indicators (green/yellow/red)
- Configurable stale threshold (currently hardcoded 90s)

---

## Design

### Client-side metrics reporting

The screen client reports performance data with each ping:

```javascript
// In Shell object, replace simple ping with rich heartbeat
sendHeartbeat() {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;

    const metrics = {
        type: 'heartbeat',
        fps: this.currentFPS,
        memory: this.getMemoryUsage(),
        uptime: Math.floor((Date.now() - this.connectedAt) / 1000),
        page: this.currentPageId,
        resolution: `${window.innerWidth}x${window.innerHeight}`,
        timestamp: Date.now()
    };
    this.ws.send(JSON.stringify(metrics));
},

// FPS counter using requestAnimationFrame
initFPSCounter() {
    let frames = 0;
    let lastTime = performance.now();
    this.currentFPS = 0;

    const countFrame = () => {
        frames++;
        const now = performance.now();
        if (now - lastTime >= 1000) {
            this.currentFPS = frames;
            frames = 0;
            lastTime = now;
        }
        requestAnimationFrame(countFrame);
    };
    requestAnimationFrame(countFrame);
},

getMemoryUsage() {
    // Chrome-only performance.memory API
    if (performance.memory) {
        return {
            used: Math.round(performance.memory.usedJSHeapSize / 1048576),
            total: Math.round(performance.memory.totalJSHeapSize / 1048576)
        };
    }
    return null;
}
```

### Server-side metrics storage

Store latest metrics per screen in `app_state`:

```python
# In app_state, add metrics tracking
app_state = {
    "screens": {},
    "screen_configs": {},
    "screen_meta": {},
    "screen_metrics": {},   # NEW: {screen_id: {fps, memory, latency_ms, ...}}
    "screen_uptime": {},    # NEW: {screen_id: {connected_at, disconnects: int, total_uptime_s}}
}
```

When server receives a heartbeat message:
```python
elif msg_type == "heartbeat":
    now = datetime.now(timezone.utc)
    # Calculate round-trip latency
    client_ts = data.get("timestamp")
    latency_ms = None
    if client_ts:
        latency_ms = int((now.timestamp() * 1000) - client_ts)

    app_state["screen_metrics"][screen_id] = {
        "fps": data.get("fps"),
        "memory": data.get("memory"),
        "resolution": data.get("resolution"),
        "latency_ms": latency_ms,
        "page": data.get("page"),
        "last_heartbeat": now.isoformat(),
    }
    app_state["last_seen"][screen_id] = now
```

### Enhanced health API response

`GET /api/health/screens` now returns richer data:

```json
{
    "screen_id": "bar-tv",
    "display_name": "Bar Left Monitor",
    "status": "healthy",
    "status_color": "green",
    "page": "standby",
    "fps": 58,
    "memory": {"used": 45, "total": 128},
    "latency_ms": 12,
    "resolution": "1920x1080",
    "uptime_pct": 99.7,
    "uptime_seconds": 86400,
    "disconnect_count": 1,
    "last_heartbeat": "2026-02-22T14:00:00Z",
    "device_type": "bar-display",
    "zone": "Main Bar",
    "room": "Cantina"
}
```

### Status classification

```python
def classify_screen_health(metrics, last_seen, now, stale_threshold=90):
    """Returns (status, color) tuple."""
    seconds_since = (now - last_seen).total_seconds()

    if seconds_since > stale_threshold:
        return ("offline", "red")

    fps = metrics.get("fps")
    latency = metrics.get("latency_ms")

    # Degraded: low FPS or high latency
    if fps is not None and fps < 15:
        return ("degraded", "yellow")
    if latency is not None and latency > 500:
        return ("degraded", "yellow")

    return ("healthy", "green")
```

### Config UI health cards

Enhanced health card layout:

```
┌─ Bar Left Monitor ──────────────────────┐
│ 🟢 HEALTHY         bar-tv · door-panel  │
│                                          │
│ FPS: 58    MEM: 45/128 MB    RTT: 12ms  │
│ Page: standby    Res: 1920×1080          │
│ Uptime: 99.7%    Connected: 24h 0m      │
│ Zone: Main Bar · Cantina                 │
└──────────────────────────────────────────┘

┌─ Airlock Panel ─────────────────────────┐
│ 🟡 DEGRADED       scr-xyz · airlock     │
│                                          │
│ FPS: 8     MEM: 110/128 MB   RTT: 340ms │
│ Page: hyperspace   Res: 800×480          │
│ Uptime: 94.2%    Connected: 2h 15m      │
│ Zone: Entrance · Corridor                │
└──────────────────────────────────────────┘
```

Color coding:
- **Green (healthy):** FPS ≥ 15, latency < 500ms, recently seen
- **Yellow (degraded):** Low FPS, high latency, or memory pressure
- **Red (offline):** No heartbeat in > threshold seconds

### Configurable threshold

Add to server config or expose via API:
```
GET /api/health/config → {"stale_threshold_seconds": 90}
PUT /api/health/config → {"stale_threshold_seconds": 120}
```

---

## Scope

### In scope
- Client FPS counter + memory reporting in heartbeat
- Server latency calculation from heartbeat timestamps
- Status classification (healthy/degraded/offline) with color coding
- Enhanced `/api/health/screens` response with metrics
- Config UI health cards with FPS, memory, latency, uptime %
- Configurable stale threshold

### Out of scope
- Historical metrics storage / time-series graphs (future)
- Push notifications on status change (use existing MQTT alert)
- Per-page performance profiling

---

## Estimated effort
1-2 sessions (client metrics + server tracking + config UI cards)
