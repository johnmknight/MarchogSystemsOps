#!/usr/bin/env python3
"""
MarchogSystemsOps Kiosk Agent v0.2.0
Lightweight daemon running on each kiosk device.

Features:
  - Local HTTP server for media files (:9090)
  - /status endpoint for agent discovery
  - /api/media/videos listing endpoint
  - Media sync from central server (manifest-based)
  - Telemetry reporting (CPU, memory, disk, network)
  - CORS headers for browser access
  - Config file support

Usage:
  python marchog_agent.py
  python marchog_agent.py --config agent.json
  python marchog_agent.py --port 9090 --media-dir ./media --server-url http://server:8082 --screen-id bar-left
"""

import argparse
import hashlib
import json
import mimetypes
import os
import platform
import shutil
import socket
import sys
import threading
import time
import traceback
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from datetime import datetime, timezone

__version__ = "0.2.0"

# ── Defaults ──

DEFAULT_PORT = 9090
DEFAULT_MEDIA_DIR = None  # resolved at startup
DEFAULT_SERVER_URL = "http://localhost:8082"
DEFAULT_SCREEN_ID = None
DEFAULT_SYNC_INTERVAL = 300  # 5 minutes
DEFAULT_TELEMETRY_INTERVAL = 60  # 1 minute


# ── Configuration ──

class AgentConfig:
    """Agent configuration loaded from file or CLI args."""

    def __init__(self):
        self.port = DEFAULT_PORT
        self.media_dir = DEFAULT_MEDIA_DIR
        self.server_url = DEFAULT_SERVER_URL
        self.screen_id = DEFAULT_SCREEN_ID
        self.bind_address = "127.0.0.1"
        self.sync_interval = DEFAULT_SYNC_INTERVAL
        self.telemetry_interval = DEFAULT_TELEMETRY_INTERVAL
        self.auto_cleanup = False  # delete local files not in server manifest

    def load_file(self, path):
        with open(path) as f:
            data = json.load(f)
        for key in ("port", "media_dir", "server_url", "screen_id",
                     "bind_address", "sync_interval", "telemetry_interval",
                     "auto_cleanup"):
            if key in data:
                setattr(self, key, data[key])

    def apply_args(self, args):
        if args.port: self.port = args.port
        if args.media_dir: self.media_dir = args.media_dir
        if args.server_url: self.server_url = args.server_url
        if args.screen_id: self.screen_id = args.screen_id

    def resolve_media_dir(self):
        if not self.media_dir:
            self.media_dir = str(Path(__file__).parent / "media")
        self.media_dir = str(Path(self.media_dir).resolve())
        Path(self.media_dir).mkdir(parents=True, exist_ok=True)
        (Path(self.media_dir) / "videos").mkdir(exist_ok=True)
        (Path(self.media_dir) / "images").mkdir(exist_ok=True)

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items()}


config = AgentConfig()


# ── Media helpers ──

VIDEO_EXTENSIONS = {".mp4", ".webm", ".ogg", ".mov", ".m3u8"}

def list_videos():
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

def file_checksum(filepath):
    """SHA-256 checksum of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"

def get_disk_usage():
    try:
        usage = shutil.disk_usage(config.media_dir)
        media_size = sum(
            f.stat().st_size for f in Path(config.media_dir).rglob("*") if f.is_file()
        )
        return {
            "disk_total_gb": round(usage.total / (1024**3), 1),
            "disk_free_gb": round(usage.free / (1024**3), 1),
            "disk_media_gb": round(media_size / (1024**3), 2),
        }
    except Exception:
        return {}


# ── Media Sync Engine ──

class SyncState:
    """Tracks sync status."""
    def __init__(self):
        self.last_sync = None
        self.last_result = None
        self.syncing = False
        self.errors = []

sync_state = SyncState()

def _http_get_json(url):
    """GET JSON from a URL. Returns parsed dict or None on error."""
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"[sync] HTTP GET {url} failed: {e}")
        return None

def _http_post_json(url, data):
    """POST JSON to a URL. Returns True on success."""
    try:
        body = json.dumps(data).encode()
        req = Request(url, data=body, headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        with urlopen(req, timeout=15) as resp:
            return resp.status < 400
    except Exception as e:
        print(f"[sync] HTTP POST {url} failed: {e}")
        return False

def do_sync():
    """Sync media from central server.
    1. Fetch manifest from server
    2. Compare checksums with local files
    3. Download missing/changed files
    4. Optionally delete files not in manifest
    5. Report status back to server
    """
    if sync_state.syncing:
        print("[sync] Already syncing, skipping")
        return {"status": "already_syncing"}
    if not config.server_url or not config.screen_id:
        print("[sync] No server_url or screen_id configured, skipping sync")
        return {"status": "not_configured"}

    sync_state.syncing = True
    sync_state.errors = []
    result = {"downloaded": [], "deleted": [], "unchanged": [], "errors": []}

    try:
        # 1. Fetch manifest
        manifest_url = f"{config.server_url}/api/media/manifest"
        print(f"[sync] Fetching manifest from {manifest_url}")
        manifest = _http_get_json(manifest_url)
        if not manifest or "assets" not in manifest:
            err = "Failed to fetch manifest"
            sync_state.errors.append(err)
            result["errors"].append(err)
            return result

        server_assets = {a["asset_id"]: a for a in manifest["assets"]}
        video_dir = Path(config.media_dir) / "videos"

        # 2. Check local files
        local_files = {}
        for f in video_dir.iterdir():
            if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS:
                local_files[f.name] = f

        # 3. Download missing or changed files
        for asset_id, asset in server_assets.items():
            try:
                local_path = video_dir / asset_id
                need_download = False
                if asset_id not in local_files:
                    need_download = True
                    print(f"[sync] {asset_id}: not local, will download")
                else:
                    local_checksum = file_checksum(local_path)
                    if local_checksum != asset["checksum"]:
                        need_download = True
                        print(f"[sync] {asset_id}: checksum mismatch, will re-download")
                    else:
                        result["unchanged"].append(asset_id)

                if need_download:
                    download_url = f"{config.server_url}{asset['url']}"
                    print(f"[sync] Downloading {asset_id} from {download_url}")
                    tmp_path = video_dir / f".{asset_id}.tmp"
                    try:
                        with urlopen(download_url, timeout=300) as resp:
                            with open(tmp_path, "wb") as out:
                                total = 0
                                while True:
                                    chunk = resp.read(65536)
                                    if not chunk:
                                        break
                                    out.write(chunk)
                                    total += len(chunk)
                        # Verify checksum
                        dl_checksum = file_checksum(tmp_path)
                        if dl_checksum != asset["checksum"]:
                            tmp_path.unlink(missing_ok=True)
                            err = f"{asset_id}: checksum mismatch after download"
                            print(f"[sync] ERROR: {err}")
                            result["errors"].append(err)
                            continue
                        # Move into place atomically
                        tmp_path.replace(local_path)
                        size_mb = round(total / (1024*1024), 1)
                        print(f"[sync] {asset_id}: downloaded ({size_mb} MB)")
                        result["downloaded"].append(asset_id)
                    except Exception as e:
                        tmp_path.unlink(missing_ok=True)
                        err = f"{asset_id}: download failed: {e}"
                        print(f"[sync] ERROR: {err}")
                        result["errors"].append(err)
            except Exception as e:
                err = f"{asset_id}: {e}"
                result["errors"].append(err)

        # 4. Delete local files not in manifest (if enabled)
        if config.auto_cleanup:
            for local_name, local_path in local_files.items():
                if local_name not in server_assets:
                    try:
                        local_path.unlink()
                        print(f"[sync] {local_name}: deleted (not in manifest)")
                        result["deleted"].append(local_name)
                    except Exception as e:
                        err = f"{local_name}: delete failed: {e}"
                        result["errors"].append(err)

        sync_state.last_sync = datetime.now(timezone.utc).isoformat()
        sync_state.last_result = result
        sync_state.errors = result["errors"]

        # 5. Report to server
        _report_media_status()

        dl = len(result["downloaded"])
        un = len(result["unchanged"])
        de = len(result["deleted"])
        er = len(result["errors"])
        print(f"[sync] Complete: {dl} downloaded, {un} unchanged, {de} deleted, {er} errors")
        return result

    except Exception as e:
        traceback.print_exc()
        sync_state.errors.append(str(e))
        return {"error": str(e)}
    finally:
        sync_state.syncing = False

def _report_media_status():
    """Report media sync status to the central server."""
    if not config.server_url or not config.screen_id:
        return
    videos = list_videos()
    data = {
        "local_assets": [v["asset_id"] for v in videos],
        "local_asset_count": len(videos),
        "last_sync": sync_state.last_sync,
        "syncing": sync_state.syncing,
        "sync_errors": sync_state.errors,
        "last_result": sync_state.last_result,
    }
    url = f"{config.server_url}/api/agent/{config.screen_id}/media-status"
    _http_post_json(url, data)


# ── Telemetry ──

def collect_telemetry():
    """Collect device telemetry."""
    import psutil
    disk = get_disk_usage()
    videos = list_videos()

    # Network info
    net = {"interface": None, "ip": None, "ssid": None}
    try:
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        for iface, iface_stats in stats.items():
            if iface_stats.isup and iface != "lo" and not iface.startswith("vEthernet"):
                for addr in addrs.get(iface, []):
                    if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                        net["interface"] = iface
                        net["ip"] = addr.address
                        break
                if net["ip"]:
                    break
    except Exception:
        pass

    # Battery (optional)
    battery = {"battery_percent": None, "battery_charging": None}
    try:
        bat = psutil.sensors_battery()
        if bat:
            battery["battery_percent"] = round(bat.percent)
            battery["battery_charging"] = bat.power_plugged
    except Exception:
        pass

    # Temperature (optional)
    temp_c = None
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            for name, entries in temps.items():
                if entries:
                    temp_c = round(entries[0].current, 1)
                    break
    except Exception:
        pass

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_version": __version__,
        "uptime_seconds": int(time.time() - _start_time),
        "platform": platform.system(),
        "hostname": socket.gethostname(),
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "memory_percent": round(psutil.virtual_memory().percent, 1),
        "memory_used_mb": round(psutil.virtual_memory().used / (1024**2)),
        **disk,
        **battery,
        "temperature_c": temp_c,
        "network": net,
        "local_assets_count": len(videos),
        "last_sync": sync_state.last_sync,
        "errors": sync_state.errors[-5:] if sync_state.errors else [],
    }


def send_telemetry():
    """Collect and POST telemetry to central server."""
    if not config.server_url or not config.screen_id:
        return
    try:
        data = collect_telemetry()
        url = f"{config.server_url}/api/agent/{config.screen_id}/telemetry"
        _http_post_json(url, data)
    except Exception as e:
        print(f"[telemetry] Error: {e}")


# ── Background Worker ──

def background_worker():
    """Background thread for periodic sync and telemetry."""
    # Wait for HTTP server to start
    time.sleep(3)
    print("[worker] Background worker started")

    # Initial sync on startup
    if config.server_url and config.screen_id:
        print("[worker] Running initial sync...")
        do_sync()
        send_telemetry()

    last_sync = time.time()
    last_telemetry = time.time()

    while True:
        try:
            now = time.time()

            # Periodic telemetry
            if now - last_telemetry >= config.telemetry_interval:
                send_telemetry()
                last_telemetry = now

            # Periodic sync
            if now - last_sync >= config.sync_interval:
                do_sync()
                last_sync = now

            time.sleep(5)  # check every 5 seconds
        except Exception as e:
            print(f"[worker] Error: {e}")
            time.sleep(10)


# ── HTTP Request Handler ──

class AgentHandler(SimpleHTTPRequestHandler):

    def log_message(self, format, *args):
        print(f"[http] {self.address_string()} {format % args}")

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def send_json(self, data, status=200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_cors_headers()
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length:
            return json.loads(self.rfile.read(length).decode())
        return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        path = unquote(self.path).split("?")[0]

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
                "syncing": sync_state.syncing,
                "last_sync": sync_state.last_sync,
            })
            return

        if path == "/api/media/videos":
            self.send_json(list_videos())
            return

        if path == "/api/config":
            self.send_json(config.to_dict())
            return

        if path == "/api/sync/status":
            self.send_json({
                "syncing": sync_state.syncing,
                "last_sync": sync_state.last_sync,
                "last_result": sync_state.last_result,
                "errors": sync_state.errors,
            })
            return

        # ── Static media files ──
        if path.startswith("/media/"):
            rel = path[len("/media/"):]
            file_path = Path(config.media_dir) / rel
            file_path = file_path.resolve()

            media_root = Path(config.media_dir).resolve()
            if not str(file_path).startswith(str(media_root)):
                self.send_error(403, "Forbidden")
                return
            if not file_path.is_file():
                self.send_error(404, "File not found")
                return

            content_type, _ = mimetypes.guess_type(str(file_path))
            if not content_type:
                content_type = "application/octet-stream"

            try:
                file_size = file_path.stat().st_size
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_cors_headers()
                self.send_header("Content-Length", file_size)
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()
                with open(file_path, "rb") as f:
                    while True:
                        chunk = f.read(65536)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return

        self.send_error(404, "Not found. Try /status or /media/videos/...")

    def do_POST(self):
        path = unquote(self.path).split("?")[0]

        if path == "/api/media/sync":
            # Trigger a full sync in background
            if sync_state.syncing:
                self.send_json({"status": "already_syncing"})
                return
            threading.Thread(target=do_sync, daemon=True).start()
            self.send_json({"status": "sync_started"})
            return

        if path == "/api/media/pull":
            # Pull a specific asset
            body = self.read_body()
            asset_id = body.get("asset_id")
            if not asset_id:
                self.send_json({"error": "asset_id required"}, 400)
                return
            def _pull():
                url = f"{config.server_url}/media/videos/{asset_id}"
                dest = Path(config.media_dir) / "videos" / asset_id
                print(f"[sync] Pulling {asset_id} from {url}")
                try:
                    with urlopen(url, timeout=300) as resp:
                        with open(dest, "wb") as out:
                            while True:
                                chunk = resp.read(65536)
                                if not chunk:
                                    break
                                out.write(chunk)
                    print(f"[sync] {asset_id}: pulled successfully")
                except Exception as e:
                    print(f"[sync] {asset_id}: pull failed: {e}")
            threading.Thread(target=_pull, daemon=True).start()
            self.send_json({"status": "pull_started", "asset_id": asset_id})
            return

        self.send_error(404, "Not found")

    def do_DELETE(self):
        path = unquote(self.path).split("?")[0]

        # DELETE /api/media/{asset_id}
        if path.startswith("/api/media/"):
            asset_id = path.split("/api/media/")[1]
            if not asset_id:
                self.send_json({"error": "asset_id required"}, 400)
                return
            file_path = (Path(config.media_dir) / "videos" / asset_id).resolve()
            media_root = Path(config.media_dir).resolve()
            if not str(file_path).startswith(str(media_root)):
                self.send_error(403, "Forbidden")
                return
            if not file_path.is_file():
                self.send_json({"error": "not found"}, 404)
                return
            file_path.unlink()
            print(f"[media] Deleted {asset_id}")
            self.send_json({"status": "deleted", "asset_id": asset_id})
            return

        self.send_error(404, "Not found")


# ── Main ──

_start_time = time.time()

def main():
    global _start_time

    parser = argparse.ArgumentParser(description="MarchogSystemsOps Kiosk Agent")
    parser.add_argument("--config", help="Path to config JSON file")
    parser.add_argument("--port", type=int, help="HTTP port (default: 9090)")
    parser.add_argument("--media-dir", help="Media directory path")
    parser.add_argument("--server-url", help="Central server URL")
    parser.add_argument("--screen-id", help="Screen ID for this device")
    args = parser.parse_args()

    if args.config:
        config.load_file(args.config)
    config.apply_args(args)
    config.resolve_media_dir()

    _start_time = time.time()

    print()
    print(f"  MarchogSystemsOps Kiosk Agent v{__version__}")
    print(f"  -----------------------------------")
    print(f"  Port:        {config.port}")
    print(f"  Media dir:   {config.media_dir}")
    print(f"  Server:      {config.server_url}")
    print(f"  Screen ID:   {config.screen_id or '(not set)'}")
    print(f"  Bind:        {config.bind_address}")
    print(f"  Sync every:  {config.sync_interval}s")
    print(f"  Telemetry:   {config.telemetry_interval}s")
    print(f"  Cleanup:     {config.auto_cleanup}")
    print()
    videos = list_videos()
    disk = get_disk_usage()
    print(f"  Videos:      {len(videos)} files")
    if disk:
        print(f"  Disk:        {disk.get('disk_free_gb', '?')} GB free")
    print()

    # Check if psutil is available
    try:
        import psutil
        print(f"  psutil:      {psutil.__version__} (telemetry enabled)")
    except ImportError:
        print(f"  psutil:      NOT INSTALLED (telemetry disabled)")
        print(f"               pip install psutil")
        config.telemetry_interval = 0  # disable telemetry

    # Start background worker for sync + telemetry
    if config.server_url and config.screen_id:
        worker = threading.Thread(target=background_worker, daemon=True)
        worker.start()
        print(f"  Worker:      started (sync + telemetry)")
    else:
        print(f"  Worker:      disabled (no server_url or screen_id)")
    print()

    server = HTTPServer((config.bind_address, config.port), AgentHandler)
    print(f"  Agent running on http://{config.bind_address}:{config.port}")
    print(f"  Status:      http://localhost:{config.port}/status")
    print(f"  Media:       http://localhost:{config.port}/media/videos/")
    print(f"  Sync:        POST http://localhost:{config.port}/api/media/sync")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Agent stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
