# Design: Scene Quick-Launch Bar

**Product Review Item:** Gap analysis — "one button press and every screen changes"
**Production Queue:** Phase 4
**Priority:** CRITICAL — Delivers the core product promise

---

## Problem

Scenes exist in the database and can be activated via `POST /api/scenes/{id}/activate`,
but the config UI has no quick-launch mechanism. The pitch promises "one button press
and every screen changes" — currently the operator must navigate into scene management
to trigger a scene change. There's no always-visible, one-tap trigger.

---

## Current State

- Scenes are stored in SQLite with screen→page mappings
- `POST /api/scenes/{id}/activate` sets `is_active=1` and pushes pages to all screens via WebSocket
- Config UI has a Screens tab showing connected screens but no scene switching UI
- No visual indication of which scene is currently active

---

## Design

### Persistent scene bar

A fixed bar at the top of the config page showing all scenes as labeled buttons.
Always visible regardless of which tab is active. One tap activates a scene.

```
┌──────────────────────────────────────────────────────────────┐
│  ⚡ SCENES:  [Normal Ops]  [Red Alert]  [Self-Destruct]  ●  │
│              ^^^active^^^                                     │
└──────────────────────────────────────────────────────────────┘
│  [Screens]  [Rooms]  [Pages]  [Automations]  [Health]        │
│  ... tab content below ...                                    │
```

- **Active scene** is highlighted (solid background, bright border)
- **Inactive scenes** are muted (outline style, dim)
- **● dot** opens a "Manage Scenes" dropdown/panel for create/edit/delete
- The bar is always visible — it doesn't scroll away

### Scene button interaction

**Single tap** → Activate scene immediately. Server pushes to all screens.
The previously active button dims, the new one highlights.

**Long press or right-click** → Opens scene detail: shows screen→page mapping
as a preview (see Phase 8 scene preview design). For now, just activate on tap.

### Confirmation for destructive scenes

Optional: scenes can be flagged as `requires_confirm: true` (e.g. Self-Destruct).
Tapping shows a brief confirmation: "Activate Self-Destruct? [Yes] [Cancel]"
This prevents accidental triggers during events. Non-flagged scenes activate instantly.

### API additions

```
GET /api/scenes          → existing, returns all scenes (add is_active flag)
GET /api/scenes/active   → existing, returns current active scene
POST /api/scenes/{id}/activate  → existing, activates scene
```

No new endpoints needed. The quick-launch bar just calls the existing activate endpoint.

Add to scene schema:
```json
{
  "id": "red-alert",
  "name": "Red Alert",
  "icon": "ti-alert-triangle",
  "color": "#ff3333",
  "requires_confirm": false,
  "sort_order": 1
}
```

New fields:
- `icon` — Tabler icon for the button (default: `ti-stack-2`)
- `color` — accent color for the button when active (default: theme amber)
- `requires_confirm` — show confirmation dialog before activation (default: false)
- `sort_order` — button order in the bar (default: 0)

DB migration adds these columns to the `scenes` table.

### Config UI implementation

```html
<!-- Scene quick-launch bar, inserted above tab navigation -->
<div id="scene-bar" class="scene-bar">
    <span class="scene-bar-label">SCENES</span>
    <div class="scene-buttons" id="sceneButtons">
        <!-- Populated dynamically -->
    </div>
    <button class="scene-manage-btn" title="Manage Scenes">
        <i class="ti ti-settings"></i>
    </button>
</div>
```

CSS:
```css
.scene-bar {
    position: sticky;
    top: 0;
    z-index: 100;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    background: var(--surface-dark);
    border-bottom: 1px solid var(--border);
}

.scene-btn {
    padding: 6px 16px;
    border: 1px solid var(--border);
    border-radius: 4px;
    background: transparent;
    color: var(--text-muted);
    cursor: pointer;
    font-family: 'Share Tech Mono', monospace;
    text-transform: uppercase;
    letter-spacing: 1px;
    transition: all 0.2s;
}

.scene-btn.active {
    background: var(--accent);
    color: var(--bg-dark);
    border-color: var(--accent);
    box-shadow: 0 0 8px var(--accent-glow);
}
```

JavaScript:
```javascript
async function loadSceneBar() {
    const scenes = await fetch('/api/scenes').then(r => r.json());
    const container = document.getElementById('sceneButtons');
    container.innerHTML = '';
    scenes.forEach(scene => {
        const btn = document.createElement('button');
        btn.className = `scene-btn ${scene.is_active ? 'active' : ''}`;
        btn.innerHTML = `<i class="ti ${scene.icon || 'ti-stack-2'}"></i> ${scene.name}`;
        if (scene.color && scene.is_active) {
            btn.style.setProperty('--accent', scene.color);
        }
        btn.onclick = () => activateScene(scene.id, scene.requires_confirm, scene.name);
        container.appendChild(btn);
    });
}

async function activateScene(sceneId, requiresConfirm, sceneName) {
    if (requiresConfirm) {
        if (!confirm(`Activate "${sceneName}"?`)) return;
    }
    await fetch(`/api/scenes/${sceneId}/activate`, { method: 'POST' });
    loadSceneBar();  // Refresh to update active state
}
```

### Auto-refresh

The scene bar refreshes on:
- Page load
- After any scene activation
- On a 10-second polling interval (catches activations from other config panels)
- Future: WebSocket push from server on scene change

---

## Mobile considerations

On narrow screens (< 600px), the scene bar scrolls horizontally:
```css
.scene-buttons {
    display: flex;
    gap: 6px;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}
```

Buttons get slightly larger tap targets on touch devices (min-height: 44px).

---

## Scope

### In scope
- Persistent scene bar in config.html
- One-tap activation with visual feedback
- Active scene highlighting
- Optional confirmation for destructive scenes
- DB migration: icon, color, requires_confirm, sort_order columns on scenes

### Out of scope (future)
- Scene preview on hover/long-press (Phase 8)
- Scene undo / revert to previous (Phase 8)
- Mobile-optimized full-screen scene launcher (Phase 8)
- WebSocket-push scene state sync across config panels

---

## Estimated effort
1 session (DB migration + config UI bar + styling)
