# MarchogSystemsOps — Open Issues

## Bugs

### 1. Stale port bindings on Windows
**Severity:** Low (dev environment only)
After killing the uvicorn process, port 8080 sometimes stays bound
by zombie PIDs that don't respond to `taskkill`. Requires waiting
or using a different port. Windows TCP TIME_WAIT behavior.
**Workaround:** Use `--port 8082` or restart terminal.

### 2. MQTT reconnect spam in logs
**Severity:** Low (cosmetic)
When Mosquitto isn't running, `mqtt_bus.py` retries every 1s and
fills the console. The exponential backoff caps at 30s but the
initial burst is noisy.
**Fix:** Add a flag to suppress repeated log messages after first warning.

---

## Known Limitations

### MQTT + Windows ProactorEventLoop
`aiomqtt` (paho-mqtt underneath) requires `SelectorEventLoop` which
Windows uvicorn doesn't use. Solved by running MQTT in a dedicated
thread. This works but means cross-thread communication for every
publish (via queue) and every WS bridge (via `run_coroutine_threadsafe`).
**Impact:** Minimal latency added (~1ms). No functional issues observed.

### screen_meta not persisted across server restarts
`app_state["screen_meta"]` is populated when screens connect via WebSocket.
If the server restarts, meta is empty until screens reconnect. Screens
that are assigned in the DB but not currently connected won't have meta.
**Impact:** MQTT topic matching won't work for screens that haven't
reconnected after a server restart. They'll reconnect within seconds
typically (browser auto-reconnect).

### Heartbeat is server-bridged, not true device heartbeat
Browser screens send "ping" over WebSocket, server publishes heartbeat
to MQTT on their behalf. This means the heartbeat reflects "screen ↔ server"
health, not "screen ↔ broker" health. True MQTT heartbeat requires
browser MQTT.js client (Phase future) or native kiosk app.

### Client auto-reconnect shows blank screen on disconnect
**Severity:** Medium (user-facing)
When a screen loses WebSocket connection (WiFi drop, server restart),
the screen goes blank or freezes on the last frame. There is no visible
reconnection indicator. For screens embedded behind panels running 24/7,
a silent blank screen is invisible until someone notices.
**Fix:** Add themed "Reconnecting..." overlay with Aurebesh text, spinning
logo, and connection status. Exponential backoff retry. Auto-resume assigned
content on successful reconnect. See Production Queue Phase 4.
*Source: Product Review #11.*

### Screen IDs are not human-readable
**Severity:** Medium (usability)
Screens are identified by generated IDs like `scr-yoxsnu` which carry no
semantic meaning. With 12+ screens, this makes the config UI nearly unusable.
**Fix:** Add human-readable `display_name` field to screen_configs. Show names
prominently in config UI with technical IDs as secondary/tooltip.
See Production Queue Phase 4.
*Source: Product Review #8.*

### No one-tap scene triggering
**Severity:** High (core feature gap)
Scenes exist in the database and can be activated via API, but the config UI
has no quick-launch mechanism. The pitch promises "one button press and every
screen changes" but the current workflow requires navigating to scene management.
**Fix:** Persistent scene quick-launch bar in config UI. See Production Queue Phase 4.
*Source: Product Review gap analysis.*

### Video page only supports YouTube — no local/network files
**Severity:** High (pitch-product gap)
The pitch letter promises "keep using all your existing content" (MP4 loops from
network/USB), but the video page only embeds YouTube iframes. A beta tester who
tries to use their existing MP4 content will bounce immediately.
**Fix:** Extend video page to support direct MP4/WebM URLs, local network paths,
and USB-mounted media. See Production Queue Phase 5.
*Source: Product Review gap analysis.*

### No live data integration pages exist
**Severity:** High (pitch-product gap)
The pitch lists 11 types of live data (weather, news, ISS, stocks, etc.) but
zero data integration pages have been built. The "stream real-time data" promise
is entirely undelivered.
**Fix:** Build 2-3 showcase data pages (weather, clock, news ticker).
See Production Queue Phase 5.
*Source: Product Review gap analysis.*

---

## Deferred Decisions

### Automation targeting: `publish_to` vs `target_device_types`
Current automations have `targets: [screen_ids]` (legacy direct WS)
and the automation run code checks for `publish_to: [topics]`.
The config UI doesn't yet expose device-type-based targeting in the
automation editor — it still uses individual screen selection.
**Decision needed:** How should the automation editor UI present
scope + filter → topic resolution? Build in Phase 7.

### Mosquitto as service vs manual start
Currently Mosquitto must be started manually before the server.
Options: Windows service, batch file, or have the server spawn it.
**Decision needed:** For dev, manual is fine. For kiosk deployment,
should be a service or started by the launcher script.

### Theming: Star Wars only vs. multi-theme support
The Star Wars aesthetic is perfect for the SW room builder community but
limits appeal to other themed room builders (steampunk, cyberpunk, fantasy).
The underlying technology is theme-agnostic.
**Decision needed:** Should the config panel offer a neutral/customizable theme?
Should page templates support swappable color/font themes?
Deferred to backlog. *Source: Product Review strategic observation.*

### Open-source packaging & distribution
The product needs Docker Compose for one-command deployment, a proper README
with screenshots, and a 2-minute demo video to convert GitHub visitors into
installers. Currently "interesting repo" not "I'm installing this tonight."
**Decision needed:** When to invest in packaging vs. feature development.
*Source: Product Review strategic observation.*
