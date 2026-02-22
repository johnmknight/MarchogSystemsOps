# Design: Page Parameter Presets

**Product Review Item:** #12 — Page Parameter Presets
**Production Queue:** Phase 5
**Priority:** HIGH — Makes parameterized pages usable as first-class entries

---

## Problem

The video page supports params (`?video=ID&border=style`) and the shell sends
params via postMessage on `pageReady`. But there's no way to save a specific
combination of page + params as a reusable, named entry. Each time you want
"Engine Room Feed" (video page + specific MP4 + Imperial border), you have to
know the params and configure them manually.

Presets let you save `{page: "video", params: {video: "...", border: "imperial"}}`
as a named entry called "Engine Room Feed" that appears in the page list just
like any built-in page.

---

## Current State

- `pages.json` stores page definitions with a `params` object
- The shell sends `configure` message to iframes with params from pages.json
- Config panel has a video params sub-form when editing a video-type page
- `screen_configs` has a `params_override` column for per-screen param overrides
- Creating a new "page" in the config UI creates a new entry in pages.json

**The mechanism already exists** — creating a new page entry in pages.json with
`file: "video.html"` and custom params effectively creates a preset. What's
missing is the UX: the config UI doesn't make this workflow obvious or easy.

---

## Design

### Preset = page entry with a shared file

A preset is simply a pages.json entry where `file` points to an existing page:

```json
{
    "id": "engine-room-feed",
    "name": "Engine Room Feed",
    "file": "video.html",
    "icon": "ti-engine",
    "category": "video-preset",
    "params": {
        "video": "/media/videos/engine-diagnostics.mp4",
        "border": "imperial"
    }
}
```

Multiple presets can share the same `file`. Each appears as a separate,
assignable page in the config UI.

### "Create Preset" flow in config UI

On the Pages tab, when viewing a parameterized page card (e.g. Video), add a
"Create Preset" button:

```
┌─ Video ─────────────────────────────────┐
│ 🎬 General video player                 │
│ video.html                              │
│ [Edit] [Delete] [+ Create Preset]       │
└──────────────────────────────────────────┘
```

Clicking "Create Preset" opens the page form pre-filled with the base page's
file and an empty params form:

```
┌─ Create Preset ──────────────────────────────┐
│ Name:   [Engine Room Feed               ]    │
│ Icon:   [ti-engine ▾]                        │
│ Base:   video.html (locked)                  │
│                                              │
│ ── VIDEO PARAMS ──                           │
│ Video URL: [/media/videos/engine-diag.mp4 ]  │
│            [📂 Browse Media]                  │
│ Border:   [Imperial ▾]                       │
│                                              │
│              [Cancel] [Save Preset]          │
└──────────────────────────────────────────────┘
```

The saved preset appears as its own card in the Pages grid:

```
┌─ Engine Room Feed ──────────────────────┐
│ ⚙ Video preset                          │
│ video.html · imperial border             │
│ [Edit] [Delete]                          │
└──────────────────────────────────────────┘
```

### Visual distinction

Presets get a subtle badge or different card border to distinguish them from
base pages:

- **Base pages:** Solid border, standard card
- **Presets:** Dashed border, "PRESET" badge, shows base page name

### Param form registry

Each base page can define what params it accepts. Store this in pages.json
or a companion schema:

```json
{
    "id": "video",
    "name": "Video",
    "file": "video.html",
    "param_schema": [
        {"key": "video", "label": "Video URL", "type": "text", "media_picker": true},
        {"key": "border", "label": "Border Style", "type": "select",
         "options": ["none", "hud", "imperial", "hologram", "targeting", "data-feed"]}
    ]
}
```

The config UI reads `param_schema` to dynamically build the preset form.
Pages without `param_schema` don't show the "Create Preset" button.

Future data pages (weather, chrono, comms) would define their own schemas:
```json
{
    "id": "weather",
    "param_schema": [
        {"key": "latitude", "label": "Latitude", "type": "number"},
        {"key": "longitude", "label": "Longitude", "type": "number"},
        {"key": "units", "label": "Units", "type": "select", "options": ["imperial", "metric"]},
        {"key": "location_name", "label": "Location Name", "type": "text"}
    ]
}
```

---

## API

No new endpoints needed. Presets use the existing page CRUD:
- `POST /api/pages` — create preset (just a page with shared file + params)
- `PUT /api/pages/{id}` — edit preset params
- `DELETE /api/pages/{id}` — delete preset

---

## Scope

### In scope
- "Create Preset" button on parameterized page cards
- Preset creation form with dynamic param fields
- `param_schema` field in pages.json for form generation
- Visual distinction between base pages and presets
- Video page param_schema (video URL + border)

### Out of scope
- Param schemas for future pages (added when those pages are built)
- Preset import/export
- Preset templates / sharing between installations

---

## Estimated effort
1 session (config UI preset form + param_schema support + visual styling)
