# Design: Screen Naming & Labels

**Product Review Item:** #8 — Screen Naming & Labels
**Production Queue:** Phase 4
**Priority:** CRITICAL — Quick win, dramatically improves usability

---

## Problem

Screens are identified by generated IDs like `scr-yoxsnu` or user-provided URL
params like `?id=bar-tv`. These IDs are functional but carry no semantic meaning
in the config UI. With 12+ screens, a list of `scr-` prefixed strings is nearly
unusable. The operator needs to see "Bar Left Monitor" and "Airlock Door Panel,"
not `scr-abc123`.

---

## Current State

### How screen IDs work today

1. **Client connects** via `index.html?id=bar-tv` — the `id` param becomes the screen_id
2. If no `?id=` param, client generates a random `scr-xxxxxx` ID (stored in localStorage)
3. **WebSocket registration** sends `{type: "register", screen_id: "bar-tv"}` to server
4. **Server** stores in `app_state["screens"][screen_id]` (runtime) and `screen_configs` table (DB)
5. **Config UI** displays the raw `screen_id` everywhere — screen cards, dropdowns, zone assignments

### Existing `label` field

The `screen_configs` table already has a `label TEXT DEFAULT ''` column. It's used
in the assign-to-zone flow but is NOT the same as a display name — it's a config
label within a scene/zone context, not a global screen identity.

---

## Design

### New `screen_registry` table

Create a dedicated table for global screen identity, separate from scene-scoped configs:

```sql
CREATE TABLE IF NOT EXISTS screen_registry (
    screen_id TEXT PRIMARY KEY,
    display_name TEXT DEFAULT '',
    description TEXT DEFAULT '',
    icon TEXT DEFAULT 'ti-device-desktop',
    first_seen TEXT DEFAULT (datetime('now')),
    last_seen TEXT DEFAULT (datetime('now'))
)
```

**Why a new table instead of adding to `screen_configs`?**
`screen_configs` is scene-scoped — each row is a screen *within* a scene. A screen's
name should be global: "Bar Left Monitor" is that screen's identity regardless of
which scene is active. The registry is the single source of truth for screen identity.

### Auto-registration on connect

When a screen connects via WebSocket, the server upserts into `screen_registry`:

```python
async def register_screen(screen_id: str):
    """Register or update a screen in the global registry."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO screen_registry (screen_id, last_seen)
            VALUES (?, datetime('now'))
            ON CONFLICT(screen_id) DO UPDATE SET last_seen = datetime('now')
        """, (screen_id,))
        await db.commit()
```

This means every screen that has ever connected gets an entry. Even if it goes
offline, its name persists in the registry for the config UI to display.

### Naming via API

```
PATCH /api/screens/{screen_id}/name
Body: {"display_name": "Bar Left Monitor", "description": "Samsung 24\" behind the bar", "icon": "ti-device-tv"}
```

Server function:
```python
async def update_screen_name(screen_id: str, display_name: str, description: str = "", icon: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE screen_registry SET display_name = ?, description = ?, icon = ?
            WHERE screen_id = ?
        """, (display_name, description, icon, screen_id))
        await db.commit()
```

### Display resolution

Everywhere the UI shows a screen reference, resolve the display name:

```
display = registry.display_name if registry.display_name else screen_id
```

This means unnamed screens still show their technical ID — no data loss, graceful
degradation.

---

## Config UI Changes

### Screen cards (Screens tab)

Current:
```
┌─────────────────────┐
│ scr-yoxsnu          │
│ Page: standby       │
│ [Device Type badge]  │
└─────────────────────┘
```

New:
```
┌─────────────────────────┐
│ Bar Left Monitor    ✏️  │
│ scr-yoxsnu  · online    │
│ Page: standby            │
│ [door-panel badge]       │
└─────────────────────────┘
```

- **Display name** is the primary heading (large, bold)
- **screen_id** shown below in smaller muted text
- **Edit pencil icon** opens inline rename or modal
- Unnamed screens show the screen_id as the heading (current behavior, no regression)

### Rename interaction

Click pencil icon → modal or inline edit:
```
┌─ Rename Screen ─────────────────┐
│ Name: [Bar Left Monitor      ]  │
│ Description: [Samsung 24" ...]  │
│ Icon: [ti-device-tv ▾]         │
│                                  │
│           [Cancel] [Save]        │
└──────────────────────────────────┘
```

### Zone assignment dropdowns

Currently show raw screen_ids. Replace with:
```
[Bar Left Monitor (scr-yoxsnu) ▾]
```

Format: `{display_name} ({screen_id})` or just `{screen_id}` if no name set.

### Health dashboard

Same pattern — show display_name as primary, screen_id as secondary.

---

## Data flow

```
Screen connects via WS
    → server calls register_screen(screen_id)
    → upserts into screen_registry (new screens get empty display_name)
    → server loads display_name from registry into app_state["screen_meta"]

Config UI loads /api/screens
    → response includes display_name, description, icon from registry
    → UI renders display_name prominently

User renames via config UI
    → PATCH /api/screens/{id}/name
    → registry updated
    → next /api/screens call reflects new name
    → WebSocket broadcast optional: notify all config panels of name change
```

---

## Migration

In `_migrate_db()`:
```python
# Create screen_registry table if not exists
await db.execute("""
    CREATE TABLE IF NOT EXISTS screen_registry (
        screen_id TEXT PRIMARY KEY,
        display_name TEXT DEFAULT '',
        description TEXT DEFAULT '',
        icon TEXT DEFAULT 'ti-device-desktop',
        first_seen TEXT DEFAULT (datetime('now')),
        last_seen TEXT DEFAULT (datetime('now'))
    )
""")
await db.commit()
```

No data migration needed — the table starts empty and populates as screens connect.
Existing screen_configs rows are unaffected.

---

## Scope

### In scope
- `screen_registry` table with auto-registration
- `PATCH /api/screens/{id}/name` endpoint
- `GET /api/screens` response includes registry data
- Config UI: display names on screen cards, rename modal, zone dropdowns
- Health dashboard: display names

### Out of scope (future)
- Bulk rename / import screen names from CSV
- QR code scanning to auto-name screens during physical installation
- Screen grouping / tagging beyond device types

---

## Estimated effort
1 session (DB + API + config UI updates)
