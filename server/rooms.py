"""
MarchogSystemsOps Rooms — JSON-backed room and zone registry
Replaces SQLite rooms/zones tables with a simple rooms.json file
"""
import json
from pathlib import Path

ROOMS_JSON = Path(__file__).parent / "rooms.json"


def _read_rooms() -> list[dict]:
    """Read and parse rooms.json."""
    if not ROOMS_JSON.exists():
        return []
    with open(ROOMS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_rooms(rooms: list[dict]):
    """Write rooms list back to rooms.json."""
    with open(ROOMS_JSON, "w", encoding="utf-8") as f:
        json.dump(rooms, f, indent=2, ensure_ascii=False)
        f.write("\n")


# ── Room Operations ──────────────────────────────────────────

def get_all_rooms() -> list[dict]:
    """Get all rooms with their zones."""
    return _read_rooms()


def get_room(room_id: str) -> dict | None:
    """Get a single room with its zones."""
    for r in _read_rooms():
        if r["id"] == room_id:
            return r
    return None


def create_room(room_id: str, name: str, description: str = "", icon: str = "🚀"):
    """Create a new room."""
    rooms = _read_rooms()
    if any(r["id"] == room_id for r in rooms):
        return False
    max_order = max((r.get("sort_order", 0) for r in rooms), default=0)
    rooms.append({
        "id": room_id,
        "name": name,
        "description": description,
        "icon": icon,
        "sort_order": max_order + 1,
        "zones": []
    })
    _write_rooms(rooms)
    return True


def update_room(room_id: str, name: str = None, description: str = None, icon: str = None):
    """Update a room's fields."""
    rooms = _read_rooms()
    for r in rooms:
        if r["id"] == room_id:
            if name is not None:
                r["name"] = name
            if description is not None:
                r["description"] = description
            if icon is not None:
                r["icon"] = icon
            _write_rooms(rooms)
            return True
    return False


def delete_room(room_id: str):
    """Delete a room and all its zones."""
    rooms = _read_rooms()
    filtered = [r for r in rooms if r["id"] != room_id]
    if len(filtered) == len(rooms):
        return False
    _write_rooms(filtered)
    return True


# ── Zone Operations ──────────────────────────────────────────

def get_zone(zone_id: str) -> dict | None:
    """Get a zone (searches all rooms)."""
    for r in _read_rooms():
        for z in r.get("zones", []):
            if z["id"] == zone_id:
                result = dict(z)
                result["room_id"] = r["id"]
                return result
    return None


def create_zone(zone_id: str, room_id: str, name: str, description: str = "", icon: str = "📍"):
    """Create a zone within a room."""
    rooms = _read_rooms()
    for r in rooms:
        if r["id"] == room_id:
            zones = r.get("zones", [])
            if any(z["id"] == zone_id for z in zones):
                return False
            max_order = max((z.get("sort_order", 0) for z in zones), default=0)
            zones.append({
                "id": zone_id,
                "name": name,
                "description": description,
                "icon": icon,
                "sort_order": max_order + 1
            })
            r["zones"] = zones
            _write_rooms(rooms)
            return True
    return False


def update_zone(zone_id: str, name: str = None, description: str = None, icon: str = None):
    """Update a zone's fields."""
    rooms = _read_rooms()
    for r in rooms:
        for z in r.get("zones", []):
            if z["id"] == zone_id:
                if name is not None:
                    z["name"] = name
                if description is not None:
                    z["description"] = description
                if icon is not None:
                    z["icon"] = icon
                _write_rooms(rooms)
                return True
    return False


def delete_zone(zone_id: str):
    """Delete a zone from its room."""
    rooms = _read_rooms()
    for r in rooms:
        zones = r.get("zones", [])
        filtered = [z for z in zones if z["id"] != zone_id]
        if len(filtered) < len(zones):
            r["zones"] = filtered
            _write_rooms(rooms)
            return True
    return False
