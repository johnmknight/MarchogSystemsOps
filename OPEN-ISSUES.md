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

### 3. ~~Weather modal save does not persist params~~ FIXED
**Severity:** Medium (user-facing)
**Root cause:** `get_zone()` from `rooms.py` is a sync function but was called
with `await` in two places in `main.py` (lines 336 and 787). Python raises
`TypeError: object dict can't be used in 'await' expression`, causing the
POST `/api/zones/{zone_id}/screens` handler to return a 500 error.
The save *appeared* to fail because the assignment POST crashed after the DB
write but before the response, so the config panel saw a network error.
**Fix:** Removed `await` from both `get_zone()` call sites in `main.py`.
The third call site (line 302, GET `/api/zones/{zone_id}`) was already correct.

### 4. Parameter changes didn't reach live screens (FIX APPLIED — NEEDS VERIFICATION)
**Severity:** Medium (user-facing)
**Symptom:** Editing a screen's video URL / weather location / countdown in
the config panel persisted to the DB, but the live monitor did not update.
**Root cause:** `build_navigate_message` in `server/main.py` emitted per-page
WS message types (`videoConfig`, `configure`) that the Shell's
`handleWSMessage` switch had no cases for — so the messages were silently
dropped. The video/weather/selfdestruct pages all listen for a uniform
`{ type: 'configure', ...fields }` postMessage on the top level, so unifying
the WS transport on a single `{ type: "navigate", page, params }` shape
(which the Shell's existing `navigate` case forwards as `configure`) fixes
every page at once.
**Fix:** `build_navigate_message` now always emits `{type: "navigate", page,
params}`. All call sites (api_navigate_screen, push_assignment_to_screen,
push_scene_to_screens, the WS reconnect handler) inherit the fix.
**Status:** Open until John verifies live. A follow-up report ("still buggy.
Error changing from any screen to video screen in Connected Screens view")
strongly suggests the kiosk was running stale cached Shell code that
predated the fix — motivating the version-stamping work below.

### 5. Video screen transition errors — NEEDS TESTING
**Severity:** Medium (user-facing)
**Symptom:** "Error changing from any screen to video screen in Connected
Screens view" after the Bug #4 fix. Not yet reproduced on a fresh Shell.
**Likely cause:** Stale cached Shell code (service worker + browser cache)
from before the `build_navigate_message` unification. Old Shell code
expected the `videoConfig` WS message type that the server no longer sends.
**Plan:** Force a hard reload on every kiosk (now possible via the new
RELOAD ALL button in the config panel). Then reproduce and, if the error
persists, capture the JS console from the kiosk.
**Status:** OPEN — needs verification after deploy + reload-all.

---

## Needs Further Testing

### Version drift detection & cache-busting (fresh work, today)
**What was added:**
- Server `BUILD_VERSION` (git short hash + `-dirty` flag, mtime fallback)
- `/api/version` endpoint + `version` field on every WS `registered`/
  `navigate` message
- `/` and `/sw.js` template routes that substitute `{{BUILD_VERSION}}`
  into `client/index.html` (`<meta name="mso-build">`) and the SW cache
  name
- Kiosk Shell reports its embedded build on WS connect (`build:<version>`),
  server tracks it per-screen and exposes it in `/api/screens` as
  `shell_version`
- `flashIdentify()` now shows screen ID + Shell build + Server build,
  tinted red with a DRIFT tag when they disagree
- WS `{type: "reload"}` handler in Shell: unregisters SW, wipes caches,
  hard-reloads with a 30s one-shot loop guard
- New endpoints: `POST /api/screens/{id}/reload`, `POST /api/screens/reload-all`,
  `POST /api/screens/{id}/identify`
- Config panel: per-row build badge (green match / red drift), per-row
  RELOAD button, RELOAD ALL button in the Connected Screens header
- sw.js cache name is now `marchog-<BUILD_VERSION>`; `activate` evicts
  stale `marchog-*` caches
- Page iframe `src` gets `?v=<shellVersion>` cache-buster

**Nothing is visible on the kiosk during normal operation** (per John's
explicit preference). Build info only surfaces through the Identify
overlay or in the admin config panel.

**Needs testing after next server restart:**
- [ ] `/api/version` returns real git hash, not `mtime-*` or `unknown`
- [ ] Loading `/` shows `<meta name="mso-build" content="<hash>">` in view-source
- [ ] Kiosk Shell logs `[version] Shell build: <hash>` on load
- [ ] Kiosk reports `build:<hash>` on connect; config panel badges show green
- [ ] Hitting Identify on any screen shows three-row overlay with matching builds
- [ ] Intentionally edit a file, redeploy without reloading kiosks → config
  panel shows drift badges red → click RELOAD on one row → kiosk comes
  back on fresh build → badge goes green
- [ ] RELOAD ALL broadcasts to every connected screen simultaneously
- [ ] Service worker cache name actually becomes `marchog-<hash>` and old
  caches are evicted on activate (check DevTools → Application → Cache)
- [ ] Page iframes no longer load stale cached HTML after reload (e.g. try
  an edit to `pages/video.html` without a server restart — reload all —
  confirm change is live without manually clearing cache)

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
**Severity:** High (pitch-product gap) — PARTIALLY ADDRESSED
The pitch lists 11 types of live data (weather, news, ISS, stocks, etc.) but
only weather and clock pages have been built so far.
- Weather page: ✅ Complete with theme support
- Clock page: ✅ World clock with calendar feed integration
  - iCal proxy API at `/api/ical-proxy` (urllib, 10min cache)
  - Supports local `.ics` files and external feeds (space launches, etc.)
  - **Known issue:** Clock digits wiggle — need fixed-width character cells
    (each digit in its own `<span>` with `display:inline-block; text-align:center; width:Xch`)
  - **Needs testing:** External feed rendering with multiple feeds + feed tags
- News ticker: Not started
**Fix:** Build 1-2 more showcase data pages (news ticker, ISS tracker).
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
