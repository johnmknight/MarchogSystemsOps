# Pages JSON Migration — Design Notes

## Decision
Move page definitions from SQLite `pages` table to a `pages.json` file.
Rooms/Zones will follow as a second migration.

## Why
- Adding fields (like `params`) requires DB migration, Pydantic model updates, API changes across 4 files
- Page definitions are static config — rarely change, benefit from hand-editing and version control
- JSON is instantly extensible — just add a key

## Current State (SQLite)
- **DB table**: `pages` (id, name, description, file, icon, category, created_at)
- **DB functions** in `database.py`: get_all_pages, get_page, create_page, update_page, delete_page, scan_pages_directory, seed_default_pages
- **API endpoints** in `main.py`: GET/POST /api/pages, GET/PUT/DELETE /api/pages/{id}, POST /api/pages/scan
- **Pydantic models**: PageCreate(id, name, file, description, icon, category), PageUpdate(name, description, icon, category)
- **Shell** (`index.html`): fetches GET /api/pages, calls ensureFrame(p.id, p.file) setting iframe.src = `pages/${file}`
- **Config UI** (`config.html`): renders page cards, Add/Edit/Delete modals, SCAN DIR button, PREVIEW links

## Target State (JSON)

### File: `client/pages/pages.json`
```json
[
  {
    "id": "hyperspace",
    "name": "Hyperspace",
    "description": "Star Wars hyperspace jump effect",
    "file": "hyperspace.html",
    "icon": "⟐",
    "category": "ambient",
    "params": {}
  },
  {
    "id": "cantina-tv",
    "name": "Cantina TV",
    "description": "Red throne room video loop",
    "file": "video.html",
    "icon": "▶",
    "category": "ambient",
    "params": {
      "video": "https://www.blindltd.com/media/lastjedi/vids/red_05.mp4",
      "border": "imperial"
    }
  }
]
```

### New field: `params` (object)
- Generic key-value config passed to the page iframe via postMessage
- For video.html: `{ "video": "url", "border": "style" }`
- For future parameterized pages: any keys the page understands
- Pages with no params: `{}` or omitted

### Server changes — new `server/pages.py`
- Replace all page DB functions with JSON file read/write
- `get_all_pages()` → read & parse pages.json
- `get_page(id)` → filter from list
- `create_page(...)` → append to list, write file
- `update_page(id, ...)` → find & update in list, write file
- `delete_page(id)` → remove from list, write file
- `scan_pages_directory(dir)` → glob *.html, add any not in JSON
- No more seed_default_pages (defaults baked into initial pages.json)
- File locking: simple write-after-read, no concurrent writers expected

### API changes (`main.py`)
- Same endpoints, same surface
- PageCreate model adds: `params: Optional[dict] = None`
- PageUpdate model adds: `params: Optional[dict] = None`
- Import new pages module instead of DB functions
- Remove pages table from init_db (or leave inert)
- Remove seed_default_pages call
- Startup auto-scan still works (reads JSON + globs dir)

### Shell changes (`index.html`)
- `handleMessage` for `pageReady`: look up page params, send via postMessage
```js
} else if (type === 'pageReady') {
  const page = this.pages.find(p => p.id === event.data.page);
  if (page && page.params && Object.keys(page.params).length > 0) {
    const frame = this.loadedFrames[page.id];
    if (frame && frame.contentWindow) {
      frame.contentWindow.postMessage({ type: 'configure', ...page.params }, '*');
    }
  }
}
```

### Config UI changes (`config.html`)
- Add Page modal: add `oninput="onFileFieldChange()"` on file field
- When file = video.html, show VIDEO PARAMS sub-form (video URL + border picker)
- Edit Page modal: same — detect video.html, show params fields pre-filled
- `submitPage()` / `submitEditPage()`: collect params, include in API call
- Page cards: show params summary for video pages (e.g. "imperial · red_05.mp4")

### video.html
- Already has postMessage listener for `{ type: 'videoConfig', video, border }`
- Need to also accept `{ type: 'configure', video, border }` (the generic name)
- OR: shell sends type: 'videoConfig' specifically — either works

## Migration Path
1. On first startup: if pages.json doesn't exist, export current DB pages → JSON
2. Remove pages table creation from init_db (leave it for now, just stop using it)
3. All page API calls go through new JSON-backed functions

## Execution Order
1. Create `pages.json` with current page definitions + params field
2. Create `server/pages.py` with JSON-backed CRUD functions
3. Update `main.py` imports and models (add params)
4. Update shell `index.html` (postMessage params on pageReady)
5. Update config UI `config.html` (video params in Add/Edit modals)
6. Update `video.html` to accept `configure` message type
7. Test: create a video page with params, verify it loads correctly
8. Clean up: remove page DB functions from database.py, remove seed

## Future: Rooms/Zones → `rooms.json`
Same pattern. Nested structure:
```json
[
  {
    "id": "smugglers-room",
    "name": "Smuggler's Room",
    "icon": "🚀",
    "description": "Main Area",
    "zones": [
      {
        "id": "bar",
        "name": "Bar",
        "icon": "📍",
        "screens": [
          { "screen_id": "Beer Menu", "label": "Over Bar", "static_page": "video" }
        ]
      }
    ]
  }
]
```
Scenes stay in DB for now (more relational, references screens dynamically).
