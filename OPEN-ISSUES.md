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

---

## Deferred Decisions

### Automation targeting: `publish_to` vs `target_device_types`
Current automations have `targets: [screen_ids]` (legacy direct WS)
and the automation run code checks for `publish_to: [topics]`.
The config UI doesn't yet expose device-type-based targeting in the
automation editor — it still uses individual screen selection.
**Decision needed:** How should the automation editor UI present
scope + filter → topic resolution? Build in Phase 5.

### Mosquitto as service vs manual start
Currently Mosquitto must be started manually before the server.
Options: Windows service, batch file, or have the server spawn it.
**Decision needed:** For dev, manual is fine. For kiosk deployment,
should be a service or started by the launcher script.
