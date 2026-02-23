#!/usr/bin/env python3
"""
MarchogSystemsOps Kiosk Agent
Lightweight daemon running on each kiosk device.

MVP scope:
  - Local HTTP server for media files (:9090)
  - /status endpoint for agent discovery
  - /api/media/videos listing endpoint
  - CORS headers for browser access
  - Config file support

Usage:
  python marchog_agent.py
  python marchog_agent.py --config agent.json
  python marchog_agent.py --port 9090 --media-dir ./media
"""

import argparse
import json
import mimetypes
import os
import platform
import shutil
import socket
import sys
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote

__version__ = "0.1.0"

# ── Defaults ──

DEFAULT_PORT = 9090
DEFAULT_MEDIA_DIR = None  # resolved at startup
DEFAULT_SERVER_URL = "http://localhost:8082"
DEFAULT_SCREEN_ID = None  # auto-detected or set in config


# ── Configuration ──

class AgentConfig:
    """Agent configuration loaded from file or CLI args."""

    def __init__(self):
        self.port = DEFAULT_PORT
        self.media_dir = DEFAULT_MEDIA_DIR
        self.server_url = DEFAULT_SERVER_URL
        self.screen_id = DEFAULT_SCREEN_ID
        self.bind_address = "127.0.0.1"  # localhost only for security

    def load_file(self, path):
        """Load config from JSON file."""
        with open(path) as f:
            data = json.load(f)
        if "port" in data:
            self.port = int(data["port"])
        if "media_dir" in data:
            self.media_dir = data["media_dir"]
        if "server_url" in data:
            self.server_url = data["server_url"]
        if "screen_id" in data:
            self.screen_id = data["screen_id"]
        if "bind_address" in data:
            self.bind_address = data["bind_address"]

    def apply_args(self, args):
        """Override config with CLI arguments."""
        if args.port:
            self.port = args.port
        if args.media_dir:
            self.media_dir = args.media_dir
        if args.server_url:
            self.server_url = args.server_url
        if args.screen_id:
            self.screen_id = args.screen_id

    def resolve_media_dir(self):
        """Set default media_dir if not configured."""
        if not self.media_dir:
            # Default: media/ alongside the agent script
            self.media_dir = str(Path(__file__).parent / "media")
        self.media_dir = str(Path(self.media_dir).resolve())
        # Ensure directories exist
        Path(self.media_dir).mkdir(parents=True, exist_ok=True)
        (Path(self.media_dir) / "videos").mkdir(exist_ok=True)
        (Path(self.media_dir) / "images").mkdir(exist_ok=True)

    def to_dict(self):
        return {
            "port": self.port,
            "media_dir": self.media_dir,
            "server_url": self.server_url,
            "screen_id": self.screen_id,
            "bind_address": self.bind_address,
        }


config = AgentConfig()


# ── Media helpers ──

VIDEO_EXTENSIONS = {".mp4", ".webm", ".ogg", ".mov", ".m3u8"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}

def list_videos():
    """List video files in the media directory."""
    video_dir = Path(config.media_dir) / "videos"
    videos = []
    if not video_dir.exists():
        return videos
    for f in video_dir.iterdir():
        if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS:
            stat = f.stat()
            videos.append({
                "asset_id": f.name,
                "filename": f.name,
                "size": stat.st_size,
                "url": f"/media/videos/{f.name}",
            })
    return sorted(videos, key=lambda v: v["filename"])

def get_disk_usage():
    """Get disk usage for the media directory."""
    try:
        usage = shutil.disk_usage(config.media_dir)
        media_size = sum(
            f.stat().st_size
            for f in Path(config.media_dir).rglob("*")
            if f.is_file()
        )
        return {
            "disk_total_gb": round(usage.total / (1024**3), 1),
            "disk_free_gb": round(usage.free / (1024**3), 1),
            "disk_media_gb": round(media_size / (1024**3), 2),
        }
    except Exception:
        return {}


# ── HTTP Request Handler ──

class AgentHandler(SimpleHTTPRequestHandler):
    """HTTP handler for the kiosk agent."""

    def log_message(self, format, *args):
        """Override to use our format."""
        print(f"[agent] {self.address_string()} {format % args}")

    def send_cors_headers(self):
        """Add CORS headers for browser access."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def send_json(self, data, status=200):
        """Send JSON response."""
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_cors_headers()
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        """Route GET requests."""
        path = unquote(self.path).split("?")[0]

        # ── API routes ──

        if path == "/status":
            self.send_json({
                "agent": "marchog-kiosk-agent",
                "version": __version__,
                "status": "ok",
                "screen_id": config.screen_id,
                "media_dir": config.media_dir,
                "uptime_seconds": int(time.time() - _start_time),
                "platform": platform.system(),
                "hostname": socket.gethostname(),
                "disk": get_disk_usage(),
            })
            return

        if path == "/api/media/videos":
            self.send_json(list_videos())
            return

        if path == "/api/config":
            self.send_json(config.to_dict())
            return

        # ── Static media files ──
        # Serve files from media_dir at /media/...
        if path.startswith("/media/"):
            rel = path[len("/media/"):]
            file_path = Path(config.media_dir) / rel
            file_path = file_path.resolve()

            # Security: ensure resolved path is inside media_dir
            media_root = Path(config.media_dir).resolve()
            if not str(file_path).startswith(str(media_root)):
                self.send_error(403, "Forbidden")
                return

            if not file_path.is_file():
                self.send_error(404, "File not found")
                return

            # Serve the file with proper content type
            content_type, _ = mimetypes.guess_type(str(file_path))
            if not content_type:
                content_type = "application/octet-stream"

            try:
                file_size = file_path.stat().st_size
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_cors_headers()
                self.send_header("Content-Length", file_size)
                # Enable range requests for video seeking
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()

                # Stream in chunks to handle large files
                with open(file_path, "rb") as f:
                    while True:
                        chunk = f.read(65536)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass  # Client disconnected
            return

        # ── Fallback: 404 ──
        self.send_error(404, "Not found. Try /status or /media/videos/...")



# ── Main ──

_start_time = time.time()

def main():
    global _start_time

    parser = argparse.ArgumentParser(
        description="MarchogSystemsOps Kiosk Agent"
    )
    parser.add_argument("--config", help="Path to config JSON file")
    parser.add_argument("--port", type=int, help="HTTP port (default: 9090)")
    parser.add_argument("--media-dir", help="Media directory path")
    parser.add_argument("--server-url", help="Central server URL")
    parser.add_argument("--screen-id", help="Screen ID for this device")
    args = parser.parse_args()

    # Load config
    if args.config:
        config.load_file(args.config)
    config.apply_args(args)
    config.resolve_media_dir()

    _start_time = time.time()

    print(f"")
    print(f"  MarchogSystemsOps Kiosk Agent v{__version__}")
    print(f"  -----------------------------------")
    print(f"  Port:       {config.port}")
    print(f"  Media dir:  {config.media_dir}")
    print(f"  Server:     {config.server_url}")
    print(f"  Screen ID:  {config.screen_id or '(not set)'}")
    print(f"  Bind:       {config.bind_address}")
    print(f"")

    # Count existing media
    videos = list_videos()
    disk = get_disk_usage()
    print(f"  Videos:     {len(videos)} files")
    if disk:
        print(f"  Disk:       {disk.get('disk_free_gb', '?')} GB free")
    print(f"")

    server = HTTPServer(
        (config.bind_address, config.port),
        AgentHandler
    )
    print(f"  Agent running on http://{config.bind_address}:{config.port}")
    print(f"  Status:     http://localhost:{config.port}/status")
    print(f"  Media:      http://localhost:{config.port}/media/videos/")
    print(f"")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Agent stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
