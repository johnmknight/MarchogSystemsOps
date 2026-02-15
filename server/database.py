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
                FOREIGN KEY (scene_id) REFERENCES scenes(id) ON DELETE CASCADE,
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

        # Seed default pages
        await seed_default_pages(db)
        # Seed a default scene
        await seed_default_scene(db)


async def seed_default_pages(db):
    """Register the built-in pages."""
    pages = [
        ("hyperspace", "Hyperspace", "Star Wars hyperspace jump effect", "hyperspace.html", "⟐", "ambient"),
    ]
    for page in pages:
        await db.execute("""
            INSERT OR IGNORE INTO pages (id, name, description, file, icon, category)
            VALUES (?, ?, ?, ?, ?, ?)
        """, page)
    await db.commit()


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


# ── Page Operations ──────────────────────────────────────────

async def get_all_pages():
    """Get all registered pages."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM pages ORDER BY category, name")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_page(page_id: str):
    """Get a single page by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM pages WHERE id = ?", (page_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


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
