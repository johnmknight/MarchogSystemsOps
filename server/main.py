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
import asyncio
import json

from database import (
    init_db,
    get_all_scenes, get_scene, get_active_scene,
    create_scene, delete_scene, activate_scene,
    set_screen_config, remove_screen_config, get_screen_assignment,
    get_zone_screens, assign_screen_to_zone, unassign_screen_from_zone,
    get_rooms_with_screens,
)
from pages import (
    get_all_pages, get_page, create_page, update_page, delete_page,
    scan_pages_directory,
)
from rooms import (
    get_all_rooms, get_room, create_room, update_room, delete_room,
    get_zone, create_zone, update_zone, delete_zone,
)
import mqtt_bus

# Paths
BASE_DIR = Path(__file__).parent
CLIENT_DIR = BASE_DIR.parent / "client"

# ── Device Type Taxonomy ─────────────────────────────────────

DEVICE_TYPES = {
    "Access & Security": [
        {"id": "door-panel", "label": "Door Panel"},
        {"id": "airlock-panel", "label": "Airlock Panel"},
        {"id": "alert-beacon", "label": "Alert Beacon"},
    ],
    "Navigation & Command": [
        {"id": "navigation-panel", "label": "Navigation Panel"},
        {"id": "tactical-panel", "label": "Tactical Panel"},
        {"id": "command-panel", "label": "Command Panel"},
        {"id": "comms-panel", "label": "Comms Panel"},
        {"id": "holotable", "label": "Holotable"},
    ],
    "Engineering & Systems": [
        {"id": "engineering-panel", "label": "Engineering Panel"},
        {"id": "diagnostic-panel", "label": "Diagnostic Panel"},
        {"id": "gauge-display", "label": "Gauge Display"},
        {"id": "life-support-panel", "label": "Life Support Panel"},
        {"id": "systems-panel", "label": "Systems Panel"},
    ],
    "Viewport & Atmospheric": [
        {"id": "viewport", "label": "Viewport"},
        {"id": "ambient-display", "label": "Ambient Display"},
        {"id": "corridor-display", "label": "Corridor Display"},
    ],
    "Entertainment & Media": [
        {"id": "entertainment-display", "label": "Entertainment Display"},
        {"id": "bar-display", "label": "Bar Display"},
        {"id": "table-display", "label": "Table Display"},
    ],
    "Display & Collection": [
        {"id": "collectible-display", "label": "Collectible Display"},
        {"id": "label-display", "label": "Label Display"},
        {"id": "gallery-display", "label": "Gallery Display"},
    ],
    "Utility & Personal": [
        {"id": "info-display", "label": "Info Display"},
        {"id": "utility-display", "label": "Utility Display"},
        {"id": "personal-panel", "label": "Personal Panel"},
        {"id": "workstation-display", "label": "Workstation Display"},
        {"id": "medical-panel", "label": "Medical Panel"},
        {"id": "medical-display", "label": "Medical Display"},
    ],
    "Specialized": [
        {"id": "hangar-panel", "label": "Hangar Panel"},
        {"id": "cargo-display", "label": "Cargo Display"},
        {"id": "vehicle-display", "label": "Vehicle Display"},
    ],
}

# ── App State ────────────────────────────────────────────────

app_state = {
    "screens": {},         # {screen_id: {"ws": websocket, "page": str, "connected_at": str}}
    "screen_configs": {},  # Pre-provisioned: {screen_id: {"page": str, "label": str}}
    "screen_meta": {},     # {screen_id: {"device_type": str, "room_id": str, "zone_id": str, ...}}
}

# ── Lifespan ─────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[*] MarchogSystemsOps Server starting...")
    await init_db()
    print("[+] Database initialized")
    # Auto-discover new pages in client/pages/
    pages_dir = CLIENT_DIR / "pages"
    discovered = scan_pages_directory(pages_dir)
    if discovered:
        print(f"[+] Auto-registered {len(discovered)} new page(s): {', '.join(discovered)}")
    else:
        print("[+] All pages up to date")
    # Start MQTT message bus
    await mqtt_bus.start(app_state)
    # Start health monitor
    health_task = asyncio.create_task(_health_monitor())
    yield
    # Shutdown
    health_task.cancel()
    try:
        await health_task
    except asyncio.CancelledError:
        pass
    await mqtt_bus.stop()
    print("MarchogSystemsOps Server shutting down...")


HEALTH_CHECK_INTERVAL = 30  # seconds
STALE_THRESHOLD = 90  # seconds before a screen is considered stale


async def _health_monitor():
    """Background task: check screen health every HEALTH_CHECK_INTERVAL seconds."""
    while True:
        try:
            await asyncio.sleep(HEALTH_CHECK_INTERVAL)
            now = datetime.now(timezone.utc)
            stale_screens = []
            for screen_id, screen_data in list(app_state["screens"].items()):
                last_seen = screen_data.get("last_seen")
                if last_seen:
                    last_dt = datetime.fromisoformat(last_seen)
                    delta = (now - last_dt).total_seconds()
                    if delta > STALE_THRESHOLD:
                        stale_screens.append(screen_id)

            if stale_screens and mqtt_bus.is_connected():
                for sid in stale_screens:
                    await mqtt_bus.publish(f"marchog/alert/stale-screen", {
                        "type": "alert",
                        "alert_type": "stale-screen",
                        "device_id": sid,
                        "message": f"Screen {sid} has not responded in {STALE_THRESHOLD}s",
                    })
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[!] Health monitor error: {e}")


# ── App ──────────────────────────────────────────────────────

app = FastAPI(title="MarchogSystemsOps", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic Models ──────────────────────────────────────────

class RoomCreate(BaseModel):
    id: str
    name: str
    description: str = ""
    icon: str = "ti-rocket"

class RoomUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None

class ZoneCreate(BaseModel):
    id: str
    room_id: str
    name: str
    description: str = ""
    icon: str = "ti-map-pin"

class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None

class ZoneScreenAssign(BaseModel):
    screen_id: str
    page_id: str
    label: str = ""
    params_override: dict = None
    device_type: str = "info-display"
    device_type_secondary: Optional[str] = None

class NavigateCommand(BaseModel):
    page: str
    params: dict = None

class PageCreate(BaseModel):
    id: str
    name: str
    file: str
    description: str = ""
    icon: str = ""
    category: str = "general"
    params: Optional[dict] = None

class PageUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    category: Optional[str] = None
    params: Optional[dict] = None


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


# ── API: Rooms (JSON-backed) ─────────────────────────────────

@app.get("/api/rooms")
async def api_rooms(include_screens: bool = True):
    """List all rooms with their zones and screen assignments."""
    if include_screens:
        return await get_rooms_with_screens()
    return get_all_rooms()

@app.post("/api/rooms")
async def api_create_room(room: RoomCreate):
    """Create a new room."""
    create_room(room.id, room.name, room.description, room.icon)
    return {"status": "created", "id": room.id}

@app.get("/api/rooms/{room_id}")
async def api_room(room_id: str):
    """Get a room with zones."""
    room = get_room(room_id)
    if not room:
        raise HTTPException(404, "Room not found")
    return room

@app.put("/api/rooms/{room_id}")
async def api_update_room(room_id: str, data: RoomUpdate):
    """Update a room."""
    update_room(room_id, data.name, data.description, data.icon)
    return {"status": "updated"}

@app.delete("/api/rooms/{room_id}")
async def api_delete_room(room_id: str):
    """Delete a room and its zones."""
    delete_room(room_id)
    return {"status": "deleted"}


# ── API: Zones (JSON-backed) ─────────────────────────────────

@app.post("/api/zones")
async def api_create_zone(zone: ZoneCreate):
    """Create a zone within a room."""
    create_zone(zone.id, zone.room_id, zone.name, zone.description, zone.icon)
    return {"status": "created", "id": zone.id}

@app.get("/api/zones/{zone_id}")
async def api_zone(zone_id: str):
    """Get a zone."""
    zone = get_zone(zone_id)
    if not zone:
        raise HTTPException(404, "Zone not found")
    return zone

@app.put("/api/zones/{zone_id}")
async def api_update_zone(zone_id: str, data: ZoneUpdate):
    """Update a zone."""
    update_zone(zone_id, data.name, data.description, data.icon)
    return {"status": "updated"}

@app.delete("/api/zones/{zone_id}")
async def api_delete_zone(zone_id: str):
    """Delete a zone."""
    delete_zone(zone_id)
    return {"status": "deleted"}


# ── API: Zone Screen Assignments ───────────────────────────

@app.get("/api/zones/{zone_id}/screens")
async def api_zone_screens(zone_id: str):
    """Get screens assigned to a zone in the active scene."""
    return await get_zone_screens(zone_id)

@app.post("/api/zones/{zone_id}/screens")
async def api_assign_screen_to_zone(zone_id: str, data: ZoneScreenAssign):
    """Assign a screen to a zone in the active scene."""
    active = await get_active_scene()
    if not active:
        raise HTTPException(400, "No active scene")
    await assign_screen_to_zone(active["id"], data.screen_id, zone_id, data.page_id, data.label, data.params_override, data.device_type, data.device_type_secondary)
    # Update screen_meta for MQTT targeting
    zone = await get_zone(zone_id)
    room_id = zone.get("room_id") if zone else None
    app_state["screen_meta"][data.screen_id] = {
        "device_type": data.device_type,
        "device_type_secondary": data.device_type_secondary,
        "zone_id": zone_id,
        "room_id": room_id,
    }
    # Push assignment to screen if connected
    await push_assignment_to_screen(data.screen_id)
    return {"status": "assigned", "screen_id": data.screen_id, "zone_id": zone_id}

@app.delete("/api/zones/{zone_id}/screens/{screen_id}")
async def api_unassign_screen_from_zone(zone_id: str, screen_id: str):
    """Remove a screen from a zone in the active scene."""
    active = await get_active_scene()
    if not active:
        raise HTTPException(400, "No active scene")
    await unassign_screen_from_zone(active["id"], screen_id)
    return {"status": "unassigned", "screen_id": screen_id}


class DeviceTypeUpdate(BaseModel):
    device_type: str = "info-display"
    device_type_secondary: Optional[str] = None

@app.patch("/api/screens/{screen_id}/device-type")
async def api_update_device_type(screen_id: str, data: DeviceTypeUpdate):
    """Update device type(s) for a screen in the active scene."""
    active = await get_active_scene()
    if not active:
        raise HTTPException(400, "No active scene")
    from database import update_screen_device_type
    await update_screen_device_type(active["id"], screen_id, data.device_type, data.device_type_secondary)
    # Update runtime meta
    if screen_id in app_state["screen_meta"]:
        app_state["screen_meta"][screen_id]["device_type"] = data.device_type
        app_state["screen_meta"][screen_id]["device_type_secondary"] = data.device_type_secondary
    return {"status": "updated", "screen_id": screen_id, "device_type": data.device_type, "device_type_secondary": data.device_type_secondary}

@app.get("/api/device-types")
async def api_get_device_types():
    """Return the full device type taxonomy."""
    return DEVICE_TYPES


# ── API: Pages (JSON-backed) ─────────────────────────────────

@app.get("/api/pages")
async def api_pages():
    """List all available pages."""
    return get_all_pages()

@app.post("/api/pages")
async def api_create_page(page: PageCreate):
    """Register a new page."""
    create_page(page.id, page.name, page.file, page.description, page.icon, page.category, page.params)
    return {"status": "created", "id": page.id}

@app.post("/api/pages/scan")
async def api_scan_pages():
    """Re-scan pages directory for new HTML files."""
    pages_dir = CLIENT_DIR / "pages"
    discovered = scan_pages_directory(pages_dir)
    return {"status": "scanned", "discovered": discovered}

@app.get("/api/pages/{page_id}")
async def api_page(page_id: str):
    """Get a single page."""
    page = get_page(page_id)
    if not page:
        raise HTTPException(404, "Page not found")
    return page

@app.put("/api/pages/{page_id}")
async def api_update_page(page_id: str, data: PageUpdate):
    """Update a page's metadata."""
    update_page(page_id, data.name, data.description, data.icon, data.category, data.params)
    return {"status": "updated"}

@app.delete("/api/pages/{page_id}")
async def api_delete_page(page_id: str):
    """Delete a page registration."""
    delete_page(page_id)
    return {"status": "deleted"}


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
async def api_navigate_screen(screen_id: str, cmd: NavigateCommand):
    """Send a navigation command to a specific screen."""
    if screen_id in app_state["screens"]:
        ws = app_state["screens"][screen_id]["ws"]
        try:
            msg = {
                "type": "navigate",
                "page": cmd.page
            }
            if cmd.params:
                msg["params"] = cmd.params
            await ws.send_json(msg)
            return {"status": "sent", "page": cmd.page}
        except Exception as e:
            raise HTTPException(500, f"Failed to send: {e}")
    raise HTTPException(404, "Screen not connected")


# ── API: Automations (JSON-backed) ───────────────────────────

AUTOMATIONS_JSON = Path(__file__).parent / "automations.json"

def _read_automations() -> list[dict]:
    if not AUTOMATIONS_JSON.exists():
        return []
    with open(AUTOMATIONS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

def _write_automations(autos: list[dict]):
    with open(AUTOMATIONS_JSON, "w", encoding="utf-8") as f:
        json.dump(autos, f, indent=2, ensure_ascii=False)
        f.write("\n")

class AutomationCreate(BaseModel):
    id: str
    name: str
    description: str = ""
    icon: str = "ti-bolt"
    enabled: bool = True
    actions: list = []

class AutomationUpdate(BaseModel):
    name: str = None
    description: str = None
    icon: str = None
    enabled: bool = None
    actions: list = None

@app.get("/api/automations")
async def api_get_automations():
    return _read_automations()

@app.post("/api/automations")
async def api_create_automation(data: AutomationCreate):
    autos = _read_automations()
    if any(a["id"] == data.id for a in autos):
        raise HTTPException(409, "Automation ID already exists")
    autos.append(data.dict())
    _write_automations(autos)
    return {"status": "created", "id": data.id}

@app.put("/api/automations/{auto_id}")
async def api_update_automation(auto_id: str, data: AutomationUpdate):
    autos = _read_automations()
    for a in autos:
        if a["id"] == auto_id:
            if data.name is not None: a["name"] = data.name
            if data.description is not None: a["description"] = data.description
            if data.icon is not None: a["icon"] = data.icon
            if data.enabled is not None: a["enabled"] = data.enabled
            if data.actions is not None: a["actions"] = data.actions
            _write_automations(autos)
            return {"status": "updated", "id": auto_id}
    raise HTTPException(404, "Automation not found")

@app.delete("/api/automations/{auto_id}")
async def api_delete_automation(auto_id: str):
    autos = _read_automations()
    filtered = [a for a in autos if a["id"] != auto_id]
    if len(filtered) == len(autos):
        raise HTTPException(404, "Automation not found")
    _write_automations(filtered)
    return {"status": "deleted", "id": auto_id}

@app.post("/api/automations/{auto_id}/run")
async def api_run_automation(auto_id: str):
    """Execute an automation: send navigate commands to all target screens."""
    autos = _read_automations()
    auto = next((a for a in autos if a["id"] == auto_id), None)
    if not auto:
        raise HTTPException(404, "Automation not found")
    if not auto.get("enabled", True):
        raise HTTPException(400, "Automation is disabled")

    results = []
    for action in auto.get("actions", []):
        if action.get("type") == "navigate":
            page_id = action.get("page_id")
            params = action.get("params", {})

            # ── MQTT pub/sub targets ──
            publish_to = action.get("publish_to", [])
            if publish_to and mqtt_bus.is_connected():
                await mqtt_bus.publish_navigate(
                    publish_to, page_id, params,
                    source=f"automation:{auto_id}"
                )
                results.append({
                    "targets": publish_to,
                    "status": "published",
                    "via": "mqtt"
                })

            # ── Legacy direct WebSocket targets ──
            targets = action.get("targets", [])
            for screen_id in targets:
                if screen_id in app_state["screens"]:
                    ws = app_state["screens"][screen_id]["ws"]
                    try:
                        msg = {"type": "navigate", "page": page_id}
                        if params:
                            msg["params"] = params
                        await ws.send_json(msg)
                        results.append({"screen": screen_id, "status": "sent", "via": "ws"})
                    except Exception as e:
                        results.append({"screen": screen_id, "status": "error", "error": str(e)})
                else:
                    results.append({"screen": screen_id, "status": "not_connected"})
    return {"status": "executed", "automation": auto_id, "results": results}


# ── API: MQTT Status ─────────────────────────────────────────

@app.get("/api/mqtt/status")
async def api_mqtt_status():
    """Check MQTT broker connection status."""
    return {
        "connected": mqtt_bus.is_connected(),
        "host": mqtt_bus.MQTT_HOST,
        "port": mqtt_bus.MQTT_PORT,
        "topic_prefix": mqtt_bus.TOPIC_PREFIX
    }

@app.post("/api/mqtt/publish")
async def api_mqtt_publish(body: dict):
    """Publish a message to an MQTT topic (for testing)."""
    topic = body.get("topic", "")
    payload = body.get("payload", {})
    retain = body.get("retain", False)
    if not topic:
        raise HTTPException(400, "topic required")
    ok = await mqtt_bus.publish(topic, payload, retain=retain)
    return {"status": "published" if ok else "failed", "topic": topic}


# ── API: Device Health ───────────────────────────────────────

@app.get("/api/health/screens")
async def api_screen_health():
    """Get health status of all connected screens."""
    now = datetime.now(timezone.utc)
    results = []
    for screen_id, screen_data in app_state["screens"].items():
        connected_at = screen_data.get("connected_at")
        last_seen = screen_data.get("last_seen")
        uptime = None
        if connected_at:
            uptime = int((now - datetime.fromisoformat(connected_at)).total_seconds())

        last_seen_ago = None
        status = "online"
        if last_seen:
            last_seen_ago = int((now - datetime.fromisoformat(last_seen)).total_seconds())
            if last_seen_ago > STALE_THRESHOLD:
                status = "stale"
        else:
            # No ping received yet, just connected
            status = "online"

        meta = app_state["screen_meta"].get(screen_id, {})
        results.append({
            "screen_id": screen_id,
            "status": status,
            "page": screen_data.get("page"),
            "connected_at": connected_at,
            "uptime_seconds": uptime,
            "last_seen": last_seen,
            "last_seen_ago_seconds": last_seen_ago,
            "device_type": meta.get("device_type"),
            "device_type_secondary": meta.get("device_type_secondary"),
            "zone_id": meta.get("zone_id"),
            "room_id": meta.get("room_id"),
        })
    return {
        "total_connected": len(app_state["screens"]),
        "mqtt_connected": mqtt_bus.is_connected(),
        "screens": results,
    }


# ── WebSocket: Screen Connection ─────────────────────────────

@app.websocket("/ws/screen/{screen_id}")
async def ws_screen(websocket: WebSocket, screen_id: str):
    await websocket.accept()
    print(f"[*] Screen '{screen_id}' connected")

    # Register screen
    app_state["screens"][screen_id] = {
        "ws": websocket,
        "page": None,
        "connected_at": datetime.now(timezone.utc).isoformat()
    }

    # Publish connection event to MQTT
    if mqtt_bus.is_connected():
        await mqtt_bus.publish_heartbeat(screen_id, "screen")

    # Populate screen_meta for MQTT topic matching
    assignment = await get_screen_assignment(screen_id)
    if assignment:
        zone_id = assignment.get("zone_id")
        # Look up room_id from zone
        room_id = None
        if zone_id:
            zone = await get_zone(zone_id)
            if zone:
                room_id = zone.get("room_id")
        app_state["screen_meta"][screen_id] = {
            "device_type": assignment.get("device_type", "info-display"),
            "device_type_secondary": assignment.get("device_type_secondary"),
            "zone_id": zone_id,
            "room_id": room_id,
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
                app_state["screens"][screen_id]["last_seen"] = datetime.now(timezone.utc).isoformat()
                # Publish state to MQTT (retained)
                if mqtt_bus.is_connected():
                    await mqtt_bus.publish(f"marchog/state/{screen_id}", {
                        "type": "state",
                        "device_id": screen_id,
                        "status": "online",
                        "page": page,
                    }, retain=True)

            elif data == "ping":
                await websocket.send_json({"type": "pong"})
                app_state["screens"][screen_id]["last_seen"] = datetime.now(timezone.utc).isoformat()
                # Periodic heartbeat to MQTT
                if mqtt_bus.is_connected():
                    await mqtt_bus.publish_heartbeat(screen_id, "screen")

            elif data.startswith("playlist_index:"):
                # Screen reporting playlist position
                idx = data.split(":", 1)[1]
                app_state["screens"][screen_id]["playlist_index"] = int(idx)

    except WebSocketDisconnect:
        print(f"[~] Screen '{screen_id}' disconnected")
    except Exception as e:
        print(f"[!] Screen '{screen_id}' error: {e}")
    finally:
        app_state["screens"].pop(screen_id, None)
        app_state["screen_meta"].pop(screen_id, None)
        # Publish offline status to MQTT
        if mqtt_bus.is_connected():
            await mqtt_bus.publish(f"marchog/heartbeat/{screen_id}", {
                "type": "heartbeat",
                "device_id": screen_id,
                "device_type": "screen",
                "status": "offline",
            }, retain=True)
            await mqtt_bus.publish(f"marchog/state/{screen_id}", {
                "type": "state",
                "device_id": screen_id,
                "status": "offline",
                "page": None,
            }, retain=True)


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


# ── Explicit page routes ─────────────────────────────────────

@app.get("/config")
async def config_page():
    return FileResponse(str(CLIENT_DIR / "config.html"))


# ── Thumbnails ───────────────────────────────────────────────

@app.post("/api/thumbnails/generate")
async def generate_thumbnails():
    """Generate page thumbnails using Playwright"""
    from thumbnails import generate_thumbnails as gen_thumbs
    results = await gen_thumbs()
    return {"status": "complete", "results": results}


# ── Static Files ─────────────────────────────────────────────

# Serve client files
app.mount("/", StaticFiles(directory=str(CLIENT_DIR), html=True), name="client")
