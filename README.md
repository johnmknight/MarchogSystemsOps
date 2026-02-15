# MarchogSystemsOps

Star Wars inspired multi-screen display controller. Built on the same architecture as ArtemisOps with new **scenes** and **playlists** systems.

## Architecture

```
client/
  index.html          # Shell - manages iframes, WebSocket, playlists
  pages/              # Individual page files (loaded as iframes)
    hyperspace.html    # Hyperspace jump effect
server/
  main.py             # FastAPI server with WebSocket screen management
  database.py         # SQLite: pages, scenes, screen_configs, playlists
```

## Key Concepts

### Pages
Individual full-screen experiences loaded as iframes. Each page is a self-contained HTML file in `client/pages/`.

### Scenes
Named configurations that define what each screen displays. A scene maps screen IDs to either a static page or a playlist.

### Playlists
Ordered lists of pages with durations and transitions. Screens in playlist mode auto-cycle through their assigned pages.

### Screen Management
- Each browser window connects as a named screen via `?id=screen-name`
- Screens connect via WebSocket for real-time control
- Scenes push assignments to connected screens
- Playlists run client-side with progress reporting

## API

| Endpoint | Description |
|---|---|
| `GET /api/pages` | List available pages |
| `GET /api/scenes` | List all scenes |
| `GET /api/scenes/active` | Get active scene |
| `POST /api/scenes/{id}/activate` | Activate a scene |
| `PUT /api/scenes/{sid}/screens/{scr}` | Set screen config |
| `GET /api/screens` | List connected screens |
| `POST /api/screens/{id}/navigate` | Navigate a screen |
| `WS /ws/screen/{id}` | Screen WebSocket |

## Quick Start

```bash
start-marchogsystemsops.bat
# Open http://localhost:8082
# Add ?id=bridge-main for named screens
# Config panel at http://localhost:8082/config
```

### Manual Start

If the batch file doesn't work, run directly via the venv Python:

```bash
cd server
venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8082 --reload
```

> **Note:** Do not rely on `activate` + bare `uvicorn` — uvicorn may not be on PATH. Always invoke via `venv\Scripts\python.exe -m uvicorn`.

## Pages

| Page | Description |
|---|---|
| `hyperspace` | Star Wars hyperspace jump animation (canvas) |
| `viewfinder` | Targeting computer / camera viewfinder HUD overlay |

## Port: 8082

## Easter Egg
"Marchog" is Welsh for "knight."
