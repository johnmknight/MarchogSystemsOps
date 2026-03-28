# MarchogSystemsOps — Production Queue

## Recently Completed

### MQTT Pub/Sub System (Feb 17, 2026)
- [x] Phase 1: Mosquitto broker + mqtt_bus.py with Windows threading fix
- [x] Phase 2: Device type targeting (30 types, 8 categories, DB + API + Config UI)
- [x] Phase 3: Heartbeat, state publishing, health monitoring + Config UI dashboard
- [x] Architecture diagrams (C4 L1-L3, topic tree, message flow, data model)
- [x] Page thumbnail generation with Playwright
- [x] Tabbed config UI (Screens / Rooms / Pages)
- [x] Screen device type taxonomy (SCREEN_DEVICE_TYPES.md)

### Earlier Work
- [x] Self-destruct countdown page with fixed-width digits
- [x] PWA manifest + service worker for kiosk mode
- [x] Multi-screen WebSocket control system
- [x] Automation engine with run/edit/delete
- [x] Room/zone/screen assignment system
- [x] 7 display pages: hyperspace, viewfinder, standby, logo-3d, video, hangar-scan, selfdestruct

---

## Next Up

### Phase 4: Screen Provisioning & Reliability (Feb 17-22, 2026)
- [x] Screen naming & labels (human-readable names, config UI)
- [x] Scene quick-launch bar (one-tap scene activation from config panel)
- [x] Pages.json migration (file-based page registry)
- [x] Tabbed config UI (Screens / Rooms / Pages)
- [x] Page thumbnails via Playwright
- [x] Connected screen controls (rename, navigate, fullscreen, identify)
- [x] Client auto-reconnect with numbered heartbeat (ping:N/pong:N)
      Silent background reconnect - no on-screen overlay. Kiosk screens keep
      displaying content during disconnects; admins monitor via Device Health.
- [x] MQTT fail-fast startup (try once, go dormant if broker unavailable).
      No retry loop - prevents event loop starvation. POST /api/mqtt/reconnect
      endpoint + clickable MQTT badge in config panel for manual reconnect.
- [x] Screen health dashboard enhancement: FPS, heap memory, viewport/DPR
      metrics with color-coded status (green/yellow/red). Client reports every
      30s, config panel Device Health section displays live values.

### Phase 5: Content Gap — Deliver on the Pitch (Priority: HIGH)
The Brian letter sells "live data on your screens" and "use your existing content."
These features need to exist before any beta tester touches the product.

- [ ] **Local/network video playback** — Video page currently supports YouTube only.
      Add support for direct MP4/WebM URLs, local network file paths, and USB-mounted media.
      This is the #1 promise in the pitch: "keep using all your existing content."
      *Source: Product Review gap analysis — HIGH priority.*
- [ ] **2-3 data integration pages** — Build showcase pages that prove the "live data" pitch:
  - [ ] Weather page — local conditions + forecast in a sci-fi readout
  - [ ] Clock/timezone page — multiple clocks styled as galactic navigation console
  - [ ] News ticker — scrolling headlines styled as incoming transmissions
      *Source: Product Review gap analysis — "stream real-time data" is promised but 0 data pages exist.*
- [ ] **Page parameter presets** — Save named configurations for parameterized pages
      (e.g. Video + specific URL + Imperial border = "Engine Room Feed"). Each preset
      appears as its own assignable page in the config UI.
      *Source: Product Review #12 — video page supports params but no saved presets.*

### Phase 6: ESP32 Proxy (Priority: HIGH)
Build Python-based virtual device simulator for MQTT testing.
No physical hardware needed. See `docs/ESP32_PROXY.md`.
- [ ] `server/esp32_proxy.py` — single script with virtual devices
- [ ] Button panel (keyboard → publish to marchog/action/*)
- [ ] LED strip controller (subscribe → ANSI terminal output)
- [ ] Motion sensor (timer/keyboard → publish presence)
- [ ] Audio controller (subscribe → play/print)
- [ ] End-to-end test: button press → automation → screens navigate

### Phase 7: Choreography (Priority: MEDIUM)
Timed sequences and chained automations. Incorporates scene scheduling.
- [ ] Sequence timeline data model (actions with delay offsets)
- [ ] Sequence executor in server (async task with sleep intervals)
- [ ] Chained triggers: automation A publishes event → triggers automation B
- [ ] **Scene scheduling / automation triggers** — Cron-like time-based scene switching
      (e.g. "Normal Ops" at 9 AM, "Ambient Night" at 11 PM) plus event-driven triggers
      (motion sensor → "Alert Mode"). Visual timeline editor in config.
      *Source: Product Review #2 — completes the automation loop with time-based rules.*
- [ ] Full self-destruct demo: screens + lighting proxy + audio proxy + fog proxy

### Phase 8: Mobile & Config Polish (Priority: MEDIUM)
- [ ] **Mobile-optimized config panel** — Responsive redesign of config.html for phone/tablet.
      Touch-friendly controls, larger tap targets, swipeable room navigation, quick-action
      bar for scene triggering. The pitch says "manage from your phone."
      *Source: Product Review #7.*
- [ ] **Scene preview before activation** — Visual preview showing what each screen will
      display when a scene is triggered, without actually pushing to screens.
      *Source: Product Review #9 — prevents embarrassing accidental scene triggers during events.*
- [ ] **Undo / scene history** — Track last N scene activations with timestamps.
      Quick "revert to previous scene" button.
      *Source: Product Review #10.*
- [ ] Automation editor: device type targeting UI (scope + filter → topics)
- [ ] Video page testing (YouTube embed + border selector)
- [ ] Room pagination (one room at a time + nav) — already built but untested with rooms


### Phase 9: Media Management (Priority: MEDIUM)
- [ ] **Media manager with remote upload** — Built-in file manager for uploading, organizing,
      and previewing media assets through the config panel. Server-side `/media` directory
      with upload API, thumbnail generation, drag-and-drop upload in config UI.
      *Source: Product Review #4 — eliminates the USB stick pain point.*
- [ ] **Screen mirroring / preview thumbnails** — Live thumbnail previews of what each screen
      is currently displaying, visible in config panel. Periodic `canvas.toDataURL()` screenshots
      sent via WebSocket. Config panel renders thumbnails in the Rooms & Zones view.
      *Source: Product Review #5 — significant differentiator from basic signage tools.*

### Phase 10: Reliability & Operations (Priority: MEDIUM)
- [ ] **Backup, export & restore** — One-click export of entire system config (rooms, zones,
      screens, scenes, playlists, pages, media) as portable ZIP archive. One-click restore.
      Enables sharing configs between builders ("here's my Star Destroyer bridge setup").
      `/api/export` and `/api/import` endpoints.
      *Source: Product Review #6.*
- [ ] **Diagnostic / system info page** — Built-in display page showing client hardware info,
      network stats, server connection status, screen resolution. Assignable to any screen
      on demand for remote debugging.
      *Source: Product Review #13.*

---

## Backlog

### Feature Backlog (from Product Review)
- [ ] **Content template library / page builder** — Visual page builder with drag-and-drop
      widgets (clocks, weather, RSS ticker, image slideshow, video player, data readouts).
      Grid-based layout editor in config panel. Theme presets (Imperial, Rebel, Mandalorian,
      Neutral Sci-Fi). This is the biggest growth unlock — transforms the product from
      a developer tool into a room builder tool.
      *Source: Product Review #3 — "the difference between 50 users and 5,000."*
- [ ] **Audio zone support** — Extend Rooms → Zones model to include audio outputs.
      Assign ambient audio tracks or sound effects to zones, synchronized with visual scenes.
      Browser-based audio is zero-hardware-cost.
      *Source: Product Review #14.*
- [ ] **Multi-user access control** — Basic role-based access: admin (full config),
      operator (scene switching only), viewer (read-only dashboard). PIN-based or role-based.
      *Source: Product Review #15 — event/party safety.*
- [ ] **Neutral/customizable theme option** — Config panel theme that isn't Star Wars specific,
      to broaden appeal to steampunk, cyberpunk, fantasy, nautical room builders.
      The underlying tech is theme-agnostic; the UI shouldn't lock it to one franchise.
      *Source: Product Review strategic observation.*

### Technical Backlog
- [ ] **Geo data regionalization** — Re-download Natural Earth 10m GeoJSON datasets
      (states/provinces + lakes) and break them into logical geographic regions for
      on-demand loading. Current monolithic files: states_data.js (42KB), lakes_data.js
      (73KB), land_data.js (21KB). Proposed regions: Northeast, Southeast, Midwest,
      Southwest, West, Great Lakes, Pacific. Each region file loads only when that
      state is active, reducing initial payload. Script should fetch from Natural Earth
      GitHub (martynafford/natural-earth-geojson 10m/physical/ne_10m_lakes.json +
      nvkelso/natural-earth-vector admin_1 states), filter by region bounding boxes,
      simplify coordinates, and output compact JS per region.
- [ ] MQTT WebSocket bridge for direct browser-to-broker (Option B in architecture)
- [ ] MQTT Last Will and Testament for automatic offline detection by broker
- [ ] Multi-broker bridging for multi-building installations
- [ ] Guest interaction tablet app (tour mode)
- [ ] Event logging and replay (subscribe to marchog/#, timestamp everything)
- [ ] Home Assistant integration via MQTT bridge
- [ ] Docker Compose for one-command deployment
- [ ] Proper README with screenshots + 2-minute demo video

### Kiosk App (Priority: LOW — waiting on hardware decisions)
- [ ] Android kiosk app with native MQTT client
- [ ] See `docs/KIOSK_APP_REQUIREMENTS.md`

---

## Priority Rationale

The ordering above follows the Product Review's recommended priority, adjusted for
existing work already completed:

1. **Phases 4-5 first** — Close the pitch-product gap before any beta testing.
   Screen naming, scene quick-launch, auto-reconnect, and content delivery are
   all things a beta tester will hit in their first 10 minutes.
2. **Phase 6 (ESP32 Proxy)** — Proves the MQTT pipeline end-to-end without hardware.
3. **Phase 7 (Choreography)** — Scene scheduling + chained automations complete the
   automation story and deliver the "wow" demo moments.
4. **Phase 8 (Mobile/Config)** — Polish the operator experience.
5. **Phases 9-10 (Media/Operations)** — Production reliability features.
6. **Backlog** — Page builder is the biggest growth unlock but requires the most work.
   Audio, multi-user, and theming are important but can wait for a v2 milestone.

---

## Future Research

### Grafana Dashboard Embedding
- **Concept:** Embed live Grafana dashboards (from `dev1:3000`) as pages in the MarchogSystemsOps page
  rotation, showing real-time SmartLab metrics directly on a kiosk screen.
- **Why it fits:** The existing `.page-frame` iframe architecture already supports this — `pages.json`
  `file` entries accept external URLs. A Grafana page would be a zero-code addition.
- **What's needed on the Grafana side (two `grafana.ini` changes on dev1):**
  ```ini
  [security]
  allow_embedding = true        # disables X-Frame-Options: deny header

  [auth.anonymous]
  enabled = true
  org_name = Main Org
  org_role = Viewer             # read-only, LAN-only exposure
  ```
- **What the pages.json entry would look like:**
  ```json
  {
    "id": "smartlab-metrics",
    "name": "SmartLab Metrics",
    "description": "Live system metrics — all hosts",
    "file": "http://YOUR_SERVER_IP:3000/d/<dashboard-uid>/system-metrics?kiosk=true&refresh=30s",
    "icon": "ti-chart-bar",
    "category": "data",
    "params": {}
  }
  ```
- **Open questions before implementing:**
  - Confirm `index.html` frame loader handles absolute `http://` URLs (vs relative paths) — quick
    code scan needed
  - Decide on `kiosk` vs `kiosk=tv` mode (tv mode hides the top nav bar entirely)
  - Consider a themed wrapper page (`grafana-metrics.html`) that iframe-embeds Grafana with
    MarchogSystems border/overlay treatment rather than raw Grafana chrome
- **Security note:** Anonymous + LAN-only is acceptable for a home lab kiosk. No sensitive data
  in these dashboards (CPU, mem, disk, uptime). Do not expose Grafana port externally.
