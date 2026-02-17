# Marchog Kiosk App — Future Requirements & Architecture

## Overview

A purpose-built Android kiosk application that turns any Android tablet into a
managed Marchog Systems display. The app replaces the need for Chrome, handles
boot automation, fullscreen display, and introduces a hybrid content delivery
model where assets can be served remotely from the central server or locally
from the tablet's own storage.

---

## Problem Statement

Current deployment requires:
1. Manually opening Chrome on each tablet after reboot
2. Navigating to the server URL
3. Tapping a fullscreen overlay (browser security prevents auto-fullscreen)
4. Network-dependent playback — all content streams from the server in real time

This is fragile for unattended installations and bandwidth-constrained environments.

---

## Proposed Architecture

```
┌─ Central Server (MarchogSystemsOps) ──────────────────────┐
│  FastAPI backend                                           │
│  ├─ Content management (pages, videos, 3D assets)         │
│  ├─ WebSocket control plane (navigate, automations)        │
│  ├─ Content sync API (manifest, delta updates)             │
│  ├─ Client registry (device info, sync status)             │
│  └─ Kiosk APK hosting (/app/marchog.apk)                  │
└────────────────────────────────────────────────────────────┘
            │  WebSocket (control)        │  HTTP (content sync)
            ▼                             ▼
┌─ Android Tablet (Marchog Kiosk App) ──────────────────────┐
│                                                            │
│  Kotlin App Shell                                          │
│  ├─ WebView (Chromium engine)                              │
│  │   └─ Renders pages, video, WebGL/Three.js, CSS          │
│  ├─ Boot Receiver (BOOT_COMPLETED)                         │
│  │   └─ Auto-launches app on device startup                │
│  ├─ Fullscreen Manager                                     │
│  │   └─ Immediate fullscreen, no user gesture needed       │
│  ├─ WebSocket Client                                       │
│  │   └─ Persistent connection to server control plane      │
│  ├─ Content Sync Service                                   │
│  │   └─ Pulls content from server to local storage         │
│  ├─ Local Media Server (Python or NanoHTTPD)               │
│  │   └─ Serves synced content at localhost:PORT            │
│  └─ Keep-Alive / Watchdog                                  │
│      └─ Restarts WebView on crash, reconnects on failure   │
│                                                            │
│  WebView loads from either:                                │
│   • http://server:8080/pages/...    (remote mode)          │
│   • http://localhost:PORT/media/... (local mode)           │
│   • Hybrid: control from server, assets from local         │
└────────────────────────────────────────────────────────────┘
```

---

## Content Delivery Modes

### Remote (current behavior)
- WebView points directly at server URL
- All content streams over the network
- Always up to date, zero local storage needed
- Best for: LAN installations with reliable network

### Local Sync
- Server pushes content manifest to tablet
- Tablet downloads assets to local storage on sync
- Embedded micro-server serves content at localhost
- Instant loads, zero network traffic during playback
- Works fully offline after initial sync
- Best for: trade shows, remote installations, bad WiFi

### Hybrid (recommended default)
- Control plane (navigation, automations, WebSocket commands) from server
- Heavy assets (video, 3D models, images) served from local storage
- Light assets (HTML pages, CSS, JS) can go either way
- Server decides per-asset: `"delivery": "local"` or `"delivery": "remote"`
- Best of both worlds: responsive + always controllable

---

## Content Sync Protocol

### Manifest
Server maintains a content manifest per client:
```json
{
  "version": "2026-02-17T02:00:00Z",
  "assets": [
    {
      "path": "pages/selfdestruct.html",
      "hash": "sha256:abc123...",
      "size": 45200,
      "delivery": "local",
      "priority": "required"
    },
    {
      "path": "media/videos/intro.mp4",
      "hash": "sha256:def456...",
      "size": 52428800,
      "delivery": "local",
      "priority": "prefetch"
    },
    {
      "path": "pages/hyperspace.html",
      "hash": "sha256:ghi789...",
      "delivery": "remote",
      "priority": "optional"
    }
  ]
}
```

### Sync Flow
1. Tablet checks in: `GET /api/sync/manifest?device_id=XXX`
2. Compares local manifest hashes to server manifest
3. Downloads changed/new assets: `GET /api/sync/asset?path=...`
4. Delta sync — only downloads what changed
5. Reports sync status: `POST /api/sync/status`

### Sync Triggers
- On boot (after network available)
- Periodic interval (configurable, e.g. every 6 hours)
- On-demand from server via WebSocket command
- Manual from config UI

---

## Kiosk App Features

### Core (MVP)
- [x] WebView with hardware-accelerated rendering
- [ ] BOOT_COMPLETED receiver — auto-launch on startup
- [ ] Immediate fullscreen (no user gesture)
- [ ] FLAG_KEEP_SCREEN_ON — prevent sleep
- [ ] Server URL configuration (first-run setup or QR scan)
- [ ] WebSocket keep-alive with auto-reconnect
- [ ] Device registration with server (screen ID, device name, resolution)

### Content Delivery
- [ ] Local media server (NanoHTTPD or embedded Python)
- [ ] Content sync service with manifest-based delta updates
- [ ] Storage management (max cache size, cleanup old assets)
- [ ] Offline mode — serve from local cache when server unreachable

### Reliability
- [ ] Watchdog — restart WebView on crash or white screen
- [ ] Network recovery — reconnect and re-sync after connectivity loss
- [ ] Crash reporting to server
- [ ] Auto-update — check server for new APK version

### Management
- [ ] QR code setup — scan to configure server URL
- [ ] Remote screenshot — server can request a screenshot for debugging
- [ ] Device info reporting (battery, storage, network, screen res)
- [ ] Kiosk lock — prevent users from exiting the app

---

## Technology Decision: Local Media Server

### Option A: NanoHTTPD (Java/Kotlin, recommended for MVP)
- ~30 lines of code, embedded in the Kotlin app
- Zero dependencies, tiny footprint
- Serves static files from local storage
- No Python complexity on Android
- Sufficient for static asset serving

### Option B: Embedded Python (Flask/FastAPI via Chaquopy)
- More capable — can do dynamic content, transcoding, playlist logic
- Adds ~15-20MB to APK size
- More complex build pipeline
- Better if local server needs application logic beyond static files

### Recommendation
Start with NanoHTTPD for MVP. Migrate to embedded Python if/when
local server needs dynamic capabilities.

---

## Distribution

### Sideloading (primary method)
- Cost: $0
- Generate signed APK in Android Studio
- Host on MarchogSystemsOps server: `http://server:8080/app/marchog.apk`
- User visits URL on tablet → downloads → installs
- Settings → Allow Unknown Sources (one-time)
- Auto-update: app checks `/api/app/version`, downloads new APK if available

### Google Play Store (optional, future)
- $25 one-time developer fee
- Wider reach, automatic updates
- Review process may be slow; kiosk apps sometimes flagged
- Only pursue if distributing beyond personal/known installations

---

## WebView Capabilities Confirmed

The Android WebView is Chromium under the hood and supports everything
currently used by MarchogSystemsOps:

- ✅ HTML5 video (with `setMediaPlaybackRequiresUserGesture(false)`)
- ✅ WebGL / Three.js (3D models, ISS visualization)
- ✅ WebSockets (real-time control from server)
- ✅ CSS animations and transitions (selfdestruct effects)
- ✅ YouTube embeds (via iframe)
- ✅ Custom fonts (Aurebesh, Orbitron, Tabler Icons)
- ✅ Responsive layout (clamp, vw units)

Requires: `setLayerType(LAYER_TYPE_HARDWARE)` for GPU acceleration.

---

## Implementation Phases

### Phase 1: Kiosk Shell (MVP)
Kotlin app with WebView, boot receiver, fullscreen, keep-alive.
Points at remote server only. Solves the reboot problem immediately.
**Estimate: 1-2 sessions**

### Phase 2: Device Registration
App registers with server on first connect. Persistent device ID
replaces random `scr-xxxxx` IDs. Server knows device capabilities.
**Estimate: 1 session**

### Phase 3: Local Media Server
NanoHTTPD serves static assets from tablet storage.
Manual content push via USB or download from server.
**Estimate: 1-2 sessions**

### Phase 4: Content Sync
Manifest-based sync protocol. Server pushes content updates.
Delta sync, priority levels, storage management.
**Estimate: 2-3 sessions**

### Phase 5: Hybrid Delivery
Server decides per-asset delivery mode. WebView URL rewriting
to swap remote URLs for localhost equivalents transparently.
**Estimate: 1-2 sessions**

---

## Related Documents
- [PITCH_BRIAN.md](./PITCH_BRIAN.md) — Business pitch for the platform
- [README.md](../README.md) — Project overview
