"""
MarchogSystemsOps Server - Star Wars Inspired Multi-Screen Controller
FastAPI backend with WebSocket screen management and scenes system
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Optional
import json

from database import (
    init_db, get_all_pages, get_page,
    get_all_scenes, get_scene, get_active_scene,
    create_scene, delete_scene, activate_scene,
    set_screen_config, remove_screen_config, get_screen_assignment
)

# Paths
BASE_DIR = Path(__file__).parent
CLIENT_DIR = BASE_DIR.parent / "client"

# ── App State ────────────────────────────────────────────────

app_state = {
    "screens": {},         # {screen_id: {"ws": websocket, "page": str, "connected_at": str}}
    "screen_configs": {},  # Pre-provisioned: {screen_id: {"page": str, "label": str}}
}

# ── Lifespan ─────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("⚡ MarchogSystemsOps Server starting...")
    await init_db()
    print("✅ Database initialized")
    yield
    print("MarchogSystemsOps Server shutting down...")

# ── App ──────────────────────────────────────────────────────

app = FastAPI(title="MarchogSystemsOps", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic Models ──────────────────────────────────────────

class SceneCreate(BaseModel):
    id: str
    name: str
    description: str = ""

class ScreenConfigUpdate(BaseModel):
    label: str = ""
    mode: str = "static"
    static_page: Optional[str] = None
    playlist_loop: bool = True
    playlist: Optional[list] = None


# ── API: Pages ───────────────────────────────────────────────

@app.get("/api/pages")
async def api_pages():
    """List all available pages."""
    return await get_all_pages()

@app.get("/api/pages/{page_id}")
async def api_page(page_id: str):
    """Get a single page."""
    page = await get_page(page_id)
    if not page:
        raise HTTPException(404, "Page not found")
    return page


# ── API: Scenes ──────────────────────────────────────────────

@app.get("/api/scenes")
async def api_scenes():
    """List all scenes."""
    return await get_all_scenes()

@app.get("/api/scenes/active")
async def api_active_scene():
    """Get the currently active scene."""
    scene = await get_active_scene()
    if not scene:
        raise HTTPException(404, "No active scene")
    return scene

@app.post("/api/scenes")
async def api_create_scene(scene: SceneCreate):
    """Create a new scene."""
    await create_scene(scene.id, scene.name, scene.description)
    return {"status": "created", "id": scene.id}

@app.get("/api/scenes/{scene_id}")
async def api_scene(scene_id: str):
    """Get a scene with all screen configs."""
    scene = await get_scene(scene_id)
    if not scene:
        raise HTTPException(404, "Scene not found")
    return scene

@app.post("/api/scenes/{scene_id}/activate")
async def api_activate_scene(scene_id: str):
    """Activate a scene and push configs to all connected screens."""
    await activate_scene(scene_id)
    # Push new assignments to all connected screens
    await push_scene_to_screens(scene_id)
    return {"status": "activated", "scene_id": scene_id}

@app.delete("/api/scenes/{scene_id}")
async def api_delete_scene(scene_id: str):
    """Delete a scene."""
    await delete_scene(scene_id)
    return {"status": "deleted"}


# ── API: Screen Configs ──────────────────────────────────────

@app.put("/api/scenes/{scene_id}/screens/{screen_id}")
async def api_set_screen(scene_id: str, screen_id: str, config: ScreenConfigUpdate):
    """Set a screen's config within a scene."""
    await set_screen_config(scene_id, screen_id, config.model_dump())
    # If this is the active scene and screen is connected, push update
    active = await get_active_scene()
    if active and active["id"] == scene_id:
        await push_assignment_to_screen(screen_id)
    return {"status": "updated"}

@app.delete("/api/scenes/{scene_id}/screens/{screen_id}")
async def api_remove_screen(scene_id: str, screen_id: str):
    """Remove a screen from a scene."""
    await remove_screen_config(scene_id, screen_id)
    return {"status": "removed"}


# ── API: Connected Screens ───────────────────────────────────

@app.get("/api/screens")
async def api_screens():
    """List all connected screens and their current state."""
    screens = []
    for sid, info in app_state["screens"].items():
        screens.append({
            "screen_id": sid,
            "page": info.get("page"),
            "connected_at": info.get("connected_at"),
        })
    return screens

@app.post("/api/screens/{screen_id}/navigate")
async def api_navigate_screen(screen_id: str, page: str):
    """Send a navigation command to a specific screen."""
    if screen_id in app_state["screens"]:
        ws = app_state["screens"][screen_id]["ws"]
        try:
            await ws.send_json({
                "type": "navigate",
                "page": page
            })
            return {"status": "sent", "page": page}
        except Exception as e:
            raise HTTPException(500, f"Failed to send: {e}")
    raise HTTPException(404, "Screen not connected")


# ── WebSocket: Screen Connection ─────────────────────────────

@app.websocket("/ws/screen/{screen_id}")
async def ws_screen(websocket: WebSocket, screen_id: str):
    await websocket.accept()
    print(f"⚡ Screen '{screen_id}' connected")

    # Register screen
    app_state["screens"][screen_id] = {
        "ws": websocket,
        "page": None,
        "connected_at": datetime.now(timezone.utc).isoformat()
    }

    try:
        # Send registration confirmation
        await websocket.send_json({
            "type": "registered",
            "screen_id": screen_id
        })

        # Send current scene assignment if any
        assignment = await get_screen_assignment(screen_id)
        if assignment:
            await websocket.send_json({
                "type": "assignment",
                "config": assignment
            })

        # Message loop
        while True:
            data = await websocket.receive_text()

            if data.startswith("page:"):
                # Screen reporting its current page
                page = data.split(":", 1)[1]
                app_state["screens"][screen_id]["page"] = page

            elif data == "ping":
                await websocket.send_json({"type": "pong"})

            elif data.startswith("playlist_index:"):
                # Screen reporting playlist position
                idx = data.split(":", 1)[1]
                app_state["screens"][screen_id]["playlist_index"] = int(idx)

    except WebSocketDisconnect:
        print(f"📡 Screen '{screen_id}' disconnected")
    except Exception as e:
        print(f"❌ Screen '{screen_id}' error: {e}")
    finally:
        app_state["screens"].pop(screen_id, None)


# ── Scene Push Helpers ───────────────────────────────────────

async def push_scene_to_screens(scene_id: str):
    """Push a scene's configs to all connected screens."""
    scene = await get_scene(scene_id)
    if not scene:
        return

    for screen_config in scene.get("screens", []):
        sid = screen_config["screen_id"]
        if sid in app_state["screens"]:
            try:
                await app_state["screens"][sid]["ws"].send_json({
                    "type": "assignment",
                    "config": screen_config
                })
            except Exception as e:
                print(f"Failed to push to {sid}: {e}")


async def push_assignment_to_screen(screen_id: str):
    """Push the active scene's assignment to a specific screen."""
    if screen_id not in app_state["screens"]:
        return

    assignment = await get_screen_assignment(screen_id)
    if assignment:
        try:
            await app_state["screens"][screen_id]["ws"].send_json({
                "type": "assignment",
                "config": assignment
            })
        except Exception as e:
            print(f"Failed to push assignment to {screen_id}: {e}")


# ── Static Files ─────────────────────────────────────────────

# Serve client files
app.mount("/", StaticFiles(directory=str(CLIENT_DIR), html=True), name="client")
