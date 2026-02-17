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

### Phase 4: ESP32 Proxy (Priority: HIGH)
Build Python-based virtual device simulator for MQTT testing.
No physical hardware needed. See `docs/ESP32_PROXY.md`.
- [ ] `server/esp32_proxy.py` — single script with virtual devices
- [ ] Button panel (keyboard → publish to marchog/action/*)
- [ ] LED strip controller (subscribe → ANSI terminal output)
- [ ] Motion sensor (timer/keyboard → publish presence)
- [ ] Audio controller (subscribe → play/print)
- [ ] End-to-end test: button press → automation → screens navigate

### Phase 5: Choreography (Priority: MEDIUM)
Timed sequences and chained automations.
- [ ] Sequence timeline data model (actions with delay offsets)
- [ ] Sequence executor in server (async task with sleep intervals)
- [ ] Chained triggers: automation A publishes event → triggers automation B
- [ ] Full self-destruct demo: screens + lighting proxy + audio proxy + fog proxy

### Config UI Polish (Priority: MEDIUM)
- [ ] Automation editor: device type targeting UI (scope + filter → topics)
- [ ] Video page testing (YouTube embed + border selector)
- [ ] Room pagination (one room at a time + nav) — already built but untested with rooms

### Kiosk App (Priority: LOW — waiting on hardware decisions)
- [ ] Android kiosk app with native MQTT client
- [ ] See `docs/KIOSK_APP_REQUIREMENTS.md`

---

## Backlog
- [ ] MQTT WebSocket bridge for direct browser-to-broker (Option B in architecture)
- [ ] MQTT Last Will and Testament for automatic offline detection by broker
- [ ] Multi-broker bridging for multi-building installations
- [ ] Guest interaction tablet app (tour mode)
- [ ] Event logging and replay (subscribe to marchog/#, timestamp everything)
- [ ] Home Assistant integration via MQTT bridge
