# MarchogSystemsOps — Product Review for Themed Room Builders

## What Exists Today

MarchogSystemsOps is a Star Wars–themed, open-source, multi-screen display controller. FastAPI + WebSocket backend, browser-based screen clients, SQLite persistence, MQTT integration for hardware devices. The architecture is solid: Rooms → Zones → Screens hierarchy, Scenes for simultaneous multi-screen switching, Playlists for auto-cycling content, and a config panel for management.

**Current Pages:** Hyperspace, Viewfinder (targeting HUD), Standby, Logo-3D, Video (YouTube + 6 border overlays), Beer Scanner

**Current Capabilities:** Screen provisioning, page assignment, scene switching, playlist cycling, connected screen monitoring, page directory scanning, MQTT bus for automation, WebSocket real-time push

---

## Missing Features — High Value

### 1. Screen Health Dashboard
**What:** Real-time status monitoring showing uptime, last heartbeat, current FPS, memory usage, and network latency per screen.
**Why:** Room builders with 8–20+ embedded screens need to know instantly when something goes wrong. A screen behind a greeblied panel that silently crashes is invisible until someone notices. Heartbeat monitoring with configurable alerts (screen offline > 30s → notification) is table stakes for a production system.
**Implementation:** WebSocket heartbeat ping/pong with timestamps. Client-side `performance.memory` and `requestAnimationFrame` FPS counter reported back. Server tracks last-seen, calculates uptime percentage. Config page shows green/yellow/red per screen.

### 2. Scene Scheduling / Automation Triggers
**What:** Time-based scene switching (e.g., "Normal Ops" at 9 AM, "Ambient Night" at 11 PM) plus event-driven triggers (motion sensor → "Alert Mode", button press → "Self-Destruct sequence").
**Why:** The letter to Brian positions one-button scene switching as the killer feature. But most of the time, rooms need *automatic* behavior — dim at night, wake on entry, party mode on a schedule. Without scheduling, someone has to manually trigger every transition. The MQTT bus is already there for hardware triggers; this is about completing the loop with time-based rules and a visual scheduler in config.
**Implementation:** Cron-like scheduler in the server with a visual timeline in config. MQTT subscription rules that map topics to scene activations. Combines with Phase 5 Choreography from the production queue.

### 3. Content Template Library / Page Builder
**What:** A visual page builder or template system that lets non-coders create new display pages from pre-built components (clocks, weather widgets, text tickers, image frames, video players, data readouts) with drag-and-drop layout and theme selection.
**Why:** Right now, creating a new page means writing HTML/CSS/JS from scratch. That's fine for you, but your target audience is themed room builders — craftspeople who build physical environments but may not code. If someone wants a "Cantina Menu Board" or "Docking Bay Status Display," they shouldn't need to write canvas rendering code. A template system with modular widgets dramatically lowers the barrier to entry.
**Implementation:** Grid-based layout editor in config panel. Widget library (clock, weather, RSS ticker, image slideshow, video player, static text, data binding placeholder). Export as self-contained HTML page. Theme presets (Imperial, Rebel, Mandalorian, Neutral Sci-Fi).

### 4. Media Manager with Remote Upload
**What:** A built-in file manager for uploading, organizing, and previewing media assets (videos, images, audio) directly through the config panel, with the ability to push files to client devices for local playback.
**Why:** The Brian letter specifically calls out the pain of physically pulling USB sticks to update content. The current system streams from URLs or network paths, which is better, but there's no central media library. Room builders need to upload a video once and assign it to any screen without knowing file paths or hosting URLs. The planned "remote media management" feature from the letter is exactly this — it should be prioritized.
**Implementation:** Server-side `/media` directory with upload API. Thumbnail generation for previews. Config panel file browser with drag-and-drop upload. Client-side caching with service worker for offline playback. Storage usage dashboard.

### 5. Screen Mirroring / Preview Thumbnails
**What:** Live thumbnail previews of what each screen is currently displaying, visible in the config panel.
**Why:** When you're managing screens from a phone in another room, you can't physically see what each display is showing. The config page shows "Hyperspace" as text — but is it actually rendering correctly? Is the animation frozen? Is it showing an error? Live thumbnails (even at 1 FPS) give the operator eyes on every screen without walking around. This is standard in professional signage systems and would be a significant differentiator.
**Implementation:** Periodic `canvas.toDataURL()` or `html2canvas` screenshot on each client, compressed and sent via WebSocket. Server stores latest frame per screen. Config panel renders thumbnails in the Rooms & Zones view. Clicking a thumbnail opens a larger live preview.

### 6. Backup, Export & Restore
**What:** One-click export of the entire system configuration (rooms, zones, screens, scenes, playlists, pages, media) as a portable archive, and one-click restore.
**Why:** Room builders invest significant time configuring their setup. A dead SD card on a Pi server shouldn't mean rebuilding everything from scratch. Also enables sharing configurations — "here's my Star Destroyer bridge setup, import it and customize." Critical for the open-source community angle.
**Implementation:** `/api/export` endpoint that bundles SQLite data + rooms.json + pages.json + custom pages + media into a ZIP. `/api/import` that restores from archive. Version stamp for forward compatibility.

---

## Missing Features — Quality of Life

### 7. Mobile-Optimized Config Panel
**What:** Responsive redesign of config.html for phone/tablet use.
**Why:** The pitch says "manage from your phone." The current config page is desktop-oriented. Room builders will be standing in their build holding a phone, not sitting at a desk. Touch-friendly controls, larger tap targets, swipeable room navigation, and a quick-action bar for scene triggering are essential for the phone-in-hand use case.

### 8. Screen Naming & Labels
**What:** Human-readable names for screens (e.g., "Bar Left Monitor," "Airlock Panel") in addition to technical IDs.
**Why:** `scr-yoxsnu` means nothing to anyone. When you have 12 screens, readable names are the difference between usable and unusable. The config panel should show names prominently with IDs as secondary detail.

### 9. Scene Preview Before Activation
**What:** A visual preview showing what each screen will display when a scene is triggered, before actually triggering it.
**Why:** "Self-Destruct" sounds dramatic, but which screens show what? If you've been editing scenes and aren't sure what the current configuration looks like, accidentally triggering the wrong scene in front of guests is embarrassing. Preview mode shows the mapping without pushing to screens.

### 10. Undo / Scene History
**What:** Track the last N scene activations with timestamps, with the ability to revert to the previous state.
**Why:** Accidental scene triggers happen. A quick "undo" or "go back to previous scene" button in the config panel is a huge QOL improvement, especially during events.

### 11. Client Auto-Reconnect with Visual Feedback
**What:** Robust auto-reconnect logic on screen clients with a visible "reconnecting" overlay (not just a blank screen).
**Why:** WiFi drops, servers restart, power blips happen. A screen that loses connection and goes blank is worse than a screen showing a "Reconnecting..." animation in-universe (Aurebesh text, spinning logo, connection status). The client should retry with exponential backoff and automatically resume its assigned content.

### 12. Page Parameter Presets
**What:** Save named parameter configurations for pages (e.g., Video page with specific URL + Imperial border = "Engine Room Feed").
**Why:** The video page already supports URL params (`?video=ID&border=style`), but there's no way to save these as reusable presets in the config panel. Each combination of page + parameters should be saveable as a named "configured page" that can be assigned to screens like any other page.

### 13. Diagnostic / System Info Page
**What:** A built-in page that displays client hardware info, network stats, server connection status, and screen resolution — useful for debugging display issues remotely.
**Why:** When a screen is rendering poorly, you need to know: is it a Pi Zero struggling with Three.js, or a network issue? A diagnostic page that each screen can show on demand helps troubleshoot without physical access.

### 14. Audio Zone Support
**What:** Extend the Rooms → Zones model to include audio outputs, with the ability to assign ambient audio tracks or sound effects to zones and synchronize them with visual scenes.
**Why:** The Brian letter mentions sound as part of the scene vision ("kill the music," "fog machines"). Themed rooms are multi-sensory. Even basic audio routing (play ambient cantina music via browser audio when "Normal Ops" is active, switch to alarm klaxon for "Self-Destruct") would make scenes dramatically more immersive. The MQTT bus can handle hardware audio controllers, but browser-based audio is zero-hardware-cost.

### 15. Multi-User Access Control
**What:** Basic role-based access — admin (full config), operator (scene switching only), viewer (read-only dashboard).
**Why:** At a party or event, you might want a trusted friend to be able to trigger scenes from their phone without being able to accidentally delete rooms or reconfigure screens. Simple PIN-based or role-based access keeps the system safe while enabling shared control.

---

## Gaps in the Current Pitch vs. Product

The letter to Brian promises several features that don't exist yet in code. These should be prioritized to deliver on the pitch:

| Promised in Letter | Current Status | Priority |
|---|---|---|
| "Stream real-time data to screens" (weather, news, ISS, stocks, etc.) | No data integration pages exist yet | **HIGH** — build 2-3 showcase data pages |
| "Keep using all your existing content" (MP4 from network/USB) | Video page does YouTube only; no local file support | **HIGH** — add local/network file playback |
| Home Assistant integration | Planned but not built | MEDIUM |
| "One button press and every screen changes" (Scenes) | Scenes exist in DB but no one-tap trigger UI | **HIGH** — add scene quick-launch bar |
| Remote media management (push files to clients) | Not built | MEDIUM |
| ESP32/hardware integration | MQTT bus exists; ESP32 proxy planned | MEDIUM |

---

## Recommended Priority Order

> **Status:** All items below have been incorporated into PRODUCTION_QUEUE.md
> and relevant issues added to OPEN-ISSUES.md as of Feb 22, 2026.

1. **Screen naming & labels** → Production Queue Phase 4 + OPEN-ISSUES
2. **Scene quick-launch bar** → Production Queue Phase 4 + OPEN-ISSUES
3. **Screen health dashboard** → Production Queue Phase 4 (extends existing Phase 3)
4. **Client auto-reconnect with visual feedback** → Production Queue Phase 4 + OPEN-ISSUES
5. **Local/network video playback** → Production Queue Phase 5 + OPEN-ISSUES
6. **2-3 data integration pages** → Production Queue Phase 5 + OPEN-ISSUES
7. **Mobile-optimized config** → Production Queue Phase 8
8. **Scene scheduling** → Production Queue Phase 7 (merged with Choreography)
9. **Media manager** → Production Queue Phase 9
10. **Screen thumbnails** → Production Queue Phase 9
11. **Backup/restore** → Production Queue Phase 10
12. **Page builder / templates** → Production Queue Backlog (biggest growth unlock)
13. **Audio zones** → Production Queue Backlog
14. **Home Assistant integration** → Production Queue Technical Backlog
15. **Multi-user access** → Production Queue Backlog

---

## Strategic Observations

**The product has a strong architectural foundation.** The WebSocket + MQTT dual-bus approach is genuinely well-designed for this use case. The Rooms/Zones/Screens hierarchy maps naturally to how room builders think about their spaces. Scenes as atomic multi-screen configurations is the right abstraction.

**The biggest risk is the gap between pitch and product.** The Brian letter sells a vision that's about 40% built. The scene system needs a quick-launch UI, the "live data" promise needs at least a few showcase pages, and local video playback is essential before showing this to beta testers. A beta tester who tries to use their existing MP4 content and can't will bounce immediately.

**The second biggest risk is the non-coder barrier.** Every new page requires writing HTML. A template/widget system would transform this from a developer tool into a room builder tool. That's the difference between 50 users and 5,000.

**Theming is a double-edged sword.** The Star Wars aesthetic is gorgeous and perfect for the Star Wars room builder community, but it limits appeal to other themed room builders (steampunk, cyberpunk, fantasy, nautical). Consider: a neutral/customizable theme option for the config panel, and page templates with swappable color/font themes. The underlying technology is theme-agnostic — the UI shouldn't lock it to one franchise.

**The open-source angle is compelling but needs packaging.** Docker Compose for one-command deployment, a proper README with screenshots, and a 2-minute demo video would make the difference between "interesting GitHub repo" and "I'm installing this tonight."
