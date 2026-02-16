# Pages & Rooms JSON Migration — Status

## ✅ COMPLETED: Pages → pages.json

**Commit:** `bf987c5` Pages: migrate from SQLite to JSON file with params support

### What moved
- Page definitions from SQLite `pages` table → `client/pages/pages.json`
- New `server/pages.py` with JSON-backed CRUD (get/create/update/delete/scan)
- Added `params` field (dict) for page-specific config (video URL, border style)
- Shell sends params via postMessage on `pageReady` event
- Config UI has video params sub-form in Add/Edit modals

### What stayed in SQLite
- Scenes, screen_configs, playlists (relational, dynamic)

### Cleanup remaining
- The `pages` table still gets created in `init_db()` — inert, not used. Can remove when convenient.

---

## ✅ COMPLETED: Rooms/Zones → rooms.json

**Commit:** `2db3979` Rooms/Zones: migrate from SQLite to JSON file

### What moved
- Room and zone definitions from SQLite → `server/rooms.json`
- New `server/rooms.py` with JSON-backed CRUD
- Nested structure: rooms contain zones array

### What stayed in SQLite
- Screen assignments within zones (tied to scenes)
- Zone-screen relationships in `screen_configs` table

---

## ✅ COMPLETED: Tabler Icons (emoji replacement)

**Commit:** `d36f747` Replace all emoji with Tabler Icons font

### Changes
- All user-facing emoji replaced with Tabler Icons font-based `<i>` elements
- Icon values stored as class names (`ti-rocket`, `ti-player-play`, etc.) in JSON
- Tabler webfont files hosted locally in `client/fonts/`
- Python defaults updated across database.py, main.py, pages.py, rooms.py

---

## Design Decision Log

### Why JSON over SQLite for pages/rooms?
- Page and room definitions are static config — they rarely change at runtime
- JSON is hand-editable, version-controllable, and instantly extensible (just add a key)
- Adding fields to SQLite requires DB migration + Pydantic model updates + API changes across 4 files
- JSON eliminates seed functions and simplifies the startup path

### Why SQLite for scenes/configs/playlists?
- Scenes reference screens dynamically — screens connect/disconnect at runtime
- Screen configs need relational joins (scene → screen → page)
- Playlists are ordered entries tied to screen configs (foreign key relationships)
- These are genuinely relational data, not static config
