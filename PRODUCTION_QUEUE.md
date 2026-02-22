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

### Phase 4: Quick Wins — Usability (Priority: CRITICAL)
Close the gap between what the pitch promises and what the product delivers.
These are fast to implement and dramatically improve the user experience.

- [ ] **Screen naming & labels** — Human-readable names for screens (e.g. "Bar Left Monitor")
      in addition to technical IDs. Display names prominently in config UI with IDs as secondary.
      *Source: Product Review #8 — "scr-yoxsnu means nothing to anyone."*
- [ ] **Scene quick-launch bar** — One-tap scene triggering from config panel and mobile.
      Persistent bar at top/bottom of config UI with scene buttons. This is the core promise
      of the pitch: "one button press and every screen changes."
      *Source: Product Review gap analysis — scenes exist in DB but no one-tap trigger UI.*
- [ ] **Client auto-reconnect with visual feedback** — Robust reconnect logic with a visible
      "Reconnecting..." overlay in Aurebesh/themed style (not blank screen). Exponential backoff,
      auto-resume assigned content on reconnect.
      *Source: Product Review #11 — essential for 24/7 unattended operation.*
- [ ] **Screen health dashboard enhancement** — Expand existing health monitoring to show
      per-screen uptime percentage, FPS, memory usage, network latency. Color-coded
      green/yellow/red status. Configurable stale threshold.
      *Source: Product Review #1 — builds on existing Phase 3 heartbeat system.*

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
