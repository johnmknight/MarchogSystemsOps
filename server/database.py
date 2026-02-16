"""
MarchogSystemsOps Database - Scenes & Screen Management
SQLite-backed storage for scenes, screen configs, and playlists
"""
import aiosqlite
import json
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).parent / "marchogsystemsops.db"


async def init_db():
    """Initialize the database with all tables."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Rooms - physical/themed spaces
        await db.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                icon TEXT DEFAULT '🚀',
                sort_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # Zones - areas within a room (Bar, Lounge, Cockpit, etc.)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS zones (
                id TEXT PRIMARY KEY,
                room_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                icon TEXT DEFAULT '📍',
                sort_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
            )
        """)

        # Pages registry - tracks available pages
        await db.execute("""
            CREATE TABLE IF NOT EXISTS pages (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                file TEXT NOT NULL,
                icon TEXT DEFAULT '',
                category TEXT DEFAULT 'general',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # Scenes - named configurations of screen assignments
        await db.execute("""
            CREATE TABLE IF NOT EXISTS scenes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                is_active INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # Screen configs within a scene
        # mode: 'static' (single page) or 'playlist' (rotating pages)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS screen_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scene_id TEXT NOT NULL,
                screen_id TEXT NOT NULL,
                label TEXT DEFAULT '',
                mode TEXT DEFAULT 'static',
                static_page TEXT DEFAULT NULL,
                playlist_loop INTEGER DEFAULT 1,
                zone_id TEXT DEFAULT NULL,
                FOREIGN KEY (scene_id) REFERENCES scenes(id) ON DELETE CASCADE,
                FOREIGN KEY (zone_id) REFERENCES zones(id) ON DELETE SET NULL,
                UNIQUE(scene_id, screen_id)
            )
        """)

        # Playlist entries for screens in playlist mode
        await db.execute("""
            CREATE TABLE IF NOT EXISTS playlist_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                screen_config_id INTEGER NOT NULL,
                page_id TEXT NOT NULL,
                duration INTEGER DEFAULT 30,
                sort_order INTEGER DEFAULT 0,
                transition TEXT DEFAULT 'fade',
                FOREIGN KEY (screen_config_id) REFERENCES screen_configs(id) ON DELETE CASCADE
            )
        """)

        await db.commit()

        # Migrations for existing databases
        await _migrate_db(db)

        # Seed default pages
        # Seed a default scene
        await seed_default_scene(db)


async def _migrate_db(db):
    """Run migrations for existing databases."""
    # Add zone_id to screen_configs if missing
    try:
        cursor = await db.execute("PRAGMA table_info(screen_configs)")
        cols = [row[1] for row in await cursor.fetchall()]
        if 'zone_id' not in cols:
            await db.execute("ALTER TABLE screen_configs ADD COLUMN zone_id TEXT DEFAULT NULL")
            await db.commit()
    except Exception:
        pass


async def seed_default_scene(db):
    """Create a default scene if none exists."""
    cursor = await db.execute("SELECT COUNT(*) FROM scenes")
    count = (await cursor.fetchone())[0]
    if count == 0:
        await db.execute("""
            INSERT INTO scenes (id, name, description, is_active)
            VALUES ('default', 'Default Scene', 'Initial screen configuration', 1)
        """)
        await db.commit()


# ── Scene Operations ─────────────────────────────────────────

async def get_all_scenes():
    """Get all scenes with their screen configs."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM scenes ORDER BY name")
        scenes = [dict(row) for row in await cursor.fetchall()]

        for scene in scenes:
            scene["screens"] = await _get_scene_screens(db, scene["id"])

        return scenes


async def get_scene(scene_id: str):
    """Get a single scene with full screen configs and playlists."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM scenes WHERE id = ?", (scene_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        scene = dict(row)
        scene["screens"] = await _get_scene_screens(db, scene_id)
        return scene


async def get_active_scene():
    """Get the currently active scene."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM scenes WHERE is_active = 1 LIMIT 1")
        row = await cursor.fetchone()
        if not row:
            return None
        scene = dict(row)
        scene["screens"] = await _get_scene_screens(db, scene["id"])
        return scene


async def activate_scene(scene_id: str):
    """Set a scene as active (deactivates all others)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE scenes SET is_active = 0")
        await db.execute("UPDATE scenes SET is_active = 1 WHERE id = ?", (scene_id,))
        await db.commit()


async def create_scene(scene_id: str, name: str, description: str = ""):
    """Create a new scene."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO scenes (id, name, description)
            VALUES (?, ?, ?)
        """, (scene_id, name, description))
        await db.commit()


async def delete_scene(scene_id: str):
    """Delete a scene and its configs (cascade)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM scenes WHERE id = ?", (scene_id,))
        await db.commit()


# ── Screen Config Operations ────────────────────────────────

async def set_screen_config(scene_id: str, screen_id: str, config: dict):
    """
    Set or update a screen's configuration within a scene.
    config: {
        "label": "Bridge Main",
        "mode": "static" | "playlist",
        "static_page": "hyperspace",  # if mode=static
        "playlist_loop": true,
        "playlist": [                 # if mode=playlist
            {"page_id": "hyperspace", "duration": 30, "transition": "fade"},
            ...
        ]
    }
    """
    async with aiosqlite.connect(DB_PATH) as db:
        # Upsert screen config
        await db.execute("""
            INSERT INTO screen_configs (scene_id, screen_id, label, mode, static_page, playlist_loop)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(scene_id, screen_id) DO UPDATE SET
                label = excluded.label,
                mode = excluded.mode,
                static_page = excluded.static_page,
                playlist_loop = excluded.playlist_loop
        """, (
            scene_id, screen_id,
            config.get("label", ""),
            config.get("mode", "static"),
            config.get("static_page"),
            1 if config.get("playlist_loop", True) else 0
        ))

        # Get the screen_config id
        cursor = await db.execute(
            "SELECT id FROM screen_configs WHERE scene_id = ? AND screen_id = ?",
            (scene_id, screen_id)
        )
        row = await cursor.fetchone()
        config_id = row[0]

        # Replace playlist entries if mode is playlist
        if config.get("mode") == "playlist" and config.get("playlist"):
            await db.execute("DELETE FROM playlist_entries WHERE screen_config_id = ?", (config_id,))
            for i, entry in enumerate(config["playlist"]):
                await db.execute("""
                    INSERT INTO playlist_entries (screen_config_id, page_id, duration, sort_order, transition)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    config_id,
                    entry["page_id"],
                    entry.get("duration", 30),
                    i,
                    entry.get("transition", "fade")
                ))

        await db.commit()


async def remove_screen_config(scene_id: str, screen_id: str):
    """Remove a screen from a scene."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM screen_configs WHERE scene_id = ? AND screen_id = ?",
            (scene_id, screen_id)
        )
        await db.commit()


async def get_screen_assignment(screen_id: str):
    """Get what the active scene says this screen should show."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # Find active scene's config for this screen
        cursor = await db.execute("""
            SELECT sc.*, s.id as scene_id, s.name as scene_name
            FROM screen_configs sc
            JOIN scenes s ON s.id = sc.scene_id
            WHERE s.is_active = 1 AND sc.screen_id = ?
        """, (screen_id,))
        row = await cursor.fetchone()
        if not row:
            return None

        config = dict(row)
        # Load playlist if applicable
        if config["mode"] == "playlist":
            cursor = await db.execute("""
                SELECT page_id, duration, sort_order, transition
                FROM playlist_entries
                WHERE screen_config_id = ?
                ORDER BY sort_order
            """, (config["id"],))
            config["playlist"] = [dict(r) for r in await cursor.fetchall()]

        return config


# ── Zone-Screen Assignment ───────────────────────────────────

async def get_zone_screens(zone_id: str, scene_id: str = None):
    """Get screen configs assigned to a zone within a scene (or the active scene)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if scene_id:
            cursor = await db.execute(
                "SELECT * FROM screen_configs WHERE zone_id = ? AND scene_id = ? ORDER BY screen_id",
                (zone_id, scene_id)
            )
        else:
            cursor = await db.execute("""
                SELECT sc.* FROM screen_configs sc
                JOIN scenes s ON s.id = sc.scene_id
                WHERE sc.zone_id = ? AND s.is_active = 1
                ORDER BY sc.screen_id
            """, (zone_id,))
        return [dict(row) for row in await cursor.fetchall()]


async def assign_screen_to_zone(scene_id: str, screen_id: str, zone_id: str, page_id: str, label: str = ""):
    """Assign a screen to a zone with a static page in the given scene."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO screen_configs (scene_id, screen_id, zone_id, label, mode, static_page)
            VALUES (?, ?, ?, ?, 'static', ?)
            ON CONFLICT(scene_id, screen_id) DO UPDATE SET
                zone_id = excluded.zone_id,
                label = excluded.label,
                mode = excluded.mode,
                static_page = excluded.static_page
        """, (scene_id, screen_id, zone_id, label, page_id))
        await db.commit()


async def unassign_screen_from_zone(scene_id: str, screen_id: str):
    """Remove a screen assignment from a scene."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM screen_configs WHERE scene_id = ? AND screen_id = ?",
            (scene_id, screen_id)
        )
        await db.commit()


async def get_rooms_with_screens():
    """Get all rooms with zones and their screen assignments from the active scene."""
    import rooms as rooms_module
    room_list = rooms_module.get_all_rooms()
    # Deep copy so we don't mutate the source
    import copy
    rooms = copy.deepcopy(room_list)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Get active scene id
        cursor = await db.execute("SELECT id FROM scenes WHERE is_active = 1 LIMIT 1")
        active_row = await cursor.fetchone()
        active_scene_id = active_row["id"] if active_row else None

        for room in rooms:
            for zone in room.get("zones", []):
                if active_scene_id:
                    cursor = await db.execute(
                        "SELECT * FROM screen_configs WHERE zone_id = ? AND scene_id = ? ORDER BY screen_id",
                        (zone["id"], active_scene_id)
                    )
                    zone["screens"] = [dict(row) for row in await cursor.fetchall()]
                else:
                    zone["screens"] = []

        return rooms


# ── Internal helpers ─────────────────────────────────────────

async def _get_scene_screens(db, scene_id: str):
    """Get all screen configs for a scene, including playlists."""
    cursor = await db.execute(
        "SELECT * FROM screen_configs WHERE scene_id = ? ORDER BY screen_id",
        (scene_id,)
    )
    screens = [dict(row) for row in await cursor.fetchall()]

    for screen in screens:
        if screen["mode"] == "playlist":
            cursor = await db.execute("""
                SELECT page_id, duration, sort_order, transition
                FROM playlist_entries
                WHERE screen_config_id = ?
                ORDER BY sort_order
            """, (screen["id"],))
            screen["playlist"] = [dict(r) for r in await cursor.fetchall()]
        else:
            screen["playlist"] = []

    return screens
