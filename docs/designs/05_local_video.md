# Design: Local/Network Video Playback

**Product Review Item:** Gap analysis — "Keep using all your existing content"
**Production Queue:** Phase 5
**Priority:** HIGH — Delivers on the core pitch promise

---

## Problem

The pitch promises "those MP4 loops you've already built work as-is" but room
builders' existing content lives on USB drives, NAS shares, and local files —
not YouTube. While the video page *does* already support direct HTTP video URLs
via a native `<video>` element, there's no way to serve local files through the
server, and the UI still labels the input as "YouTube URL or ID."

A beta tester who has 20 MP4 loops on a USB drive needs a path from "files on
disk" to "playing on screen with a themed border."

---

## Current State

**Already built:**
- `video.html` has `getSourceType(input)` that detects YouTube IDs/URLs vs direct video URLs
- `isDirectVideoUrl()` checks for `.mp4|.webm|.ogg|.m3u8|.mov` extensions
- Direct URLs create a native `<video>` element with autoplay, loop, and controls
- Border overlays work on both YouTube iframe and native video (canvas z-layered above)
- Page params system: shell sends `{video: "...", border: "..."}` via postMessage

**What's missing:**
- Server-side media directory to serve local video files
- Static file mount in FastAPI for `/media/` path
- UI labels say "YouTube" — should say "Video URL" or similar
- No file browser / media library in config panel (that's Phase 9 — Media Manager)
- No guidance in UI about how to use local files

---

## Design

### Server-side media directory

Create a `/media` directory alongside `/client` that FastAPI serves as static files:

```
MarchogSystemsOps/
├── client/
├── media/                    ← NEW
│   ├── videos/               ← User puts MP4s here
│   │   ├── engine-room.mp4
│   │   ├── hyperspace-loop.mp4
│   │   └── cantina-band.mp4
│   └── images/               ← Future use
├── server/
└── ...
```

FastAPI mount:
```python
# In main.py, add static file mount
from fastapi.staticfiles import StaticFiles
import os

MEDIA_DIR = Path(__file__).parent.parent / "media"
MEDIA_DIR.mkdir(exist_ok=True)
(MEDIA_DIR / "videos").mkdir(exist_ok=True)

app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")
```

Now any file in `media/videos/` is accessible at:
```
http://server:8082/media/videos/engine-room.mp4
```

### Media listing API

```
GET /api/media/videos → [
    {"filename": "engine-room.mp4", "size": 52428800, "url": "/media/videos/engine-room.mp4"},
    {"filename": "hyperspace-loop.mp4", "size": 12345678, "url": "/media/videos/hyperspace-loop.mp4"}
]
```

```python
@app.get("/api/media/videos")
async def list_media_videos():
    video_dir = MEDIA_DIR / "videos"
    videos = []
    for f in video_dir.iterdir():
        if f.suffix.lower() in ('.mp4', '.webm', '.ogg', '.mov', '.m3u8'):
            videos.append({
                "filename": f.name,
                "size": f.stat().st_size,
                "url": f"/media/videos/{f.name}"
            })
    return sorted(videos, key=lambda v: v["filename"])
```

### Video page UI updates

1. **Change input label** from "YouTube URL or ID" to "Video URL (YouTube, MP4, or network path)"
2. **Add media picker** — a dropdown/modal showing files from `/api/media/videos`:

```html
<div class="setting-group">
    <label>VIDEO SOURCE</label>
    <input id="videoUrl" type="text" placeholder="YouTube URL, MP4 URL, or pick from library">
    <button id="mediaPicker" title="Browse media library">📂</button>
</div>

<!-- Media picker modal -->
<div id="mediaModal" class="modal hidden">
    <h3>MEDIA LIBRARY</h3>
    <div id="mediaList" class="media-list">
        <!-- Populated from /api/media/videos -->
    </div>
</div>
```

3. **Media picker JS:**
```javascript
async function openMediaPicker() {
    const videos = await fetch('/api/media/videos').then(r => r.json());
    const list = document.getElementById('mediaList');
    list.innerHTML = '';
    if (videos.length === 0) {
        list.innerHTML = '<p class="muted">No videos in media/videos/ folder.<br>Drop MP4 files there and refresh.</p>';
        return;
    }
    videos.forEach(v => {
        const item = document.createElement('div');
        item.className = 'media-item';
        item.innerHTML = `<span>${v.filename}</span><span class="muted">${formatBytes(v.size)}</span>`;
        item.onclick = () => {
            document.getElementById('videoUrl').value = v.url;
            loadVideo(v.url);
            closeMediaPicker();
        };
        list.appendChild(item);
    });
    document.getElementById('mediaModal').classList.remove('hidden');
}
```

### Config panel integration

When creating a video page preset in the config panel, the video URL field should
also show the media picker. The saved `params.video` value can be a relative URL
like `/media/videos/engine-room.mp4` — the client will resolve it against the
server's origin automatically.

### Network path support

For files on a NAS or network share, users have two options:

1. **Symlink** — Symlink the NAS share into `media/videos/`:
   ```bash
   ln -s /mnt/nas/video-loops media/videos/nas
   # or on Windows: mklink /D media\videos\nas \\NAS\video-loops
   ```

2. **Direct URL** — If the NAS has an HTTP server, paste the URL directly:
   ```
   http://192.168.1.50/videos/engine-room.mp4
   ```

Both work with the existing `<video>` element — no code changes needed for playback.

---

## Scope

### In scope
- `media/` directory with static file serving via FastAPI
- `GET /api/media/videos` listing endpoint
- Video page: relabel input, add media picker button/modal
- Config panel: media picker in video page params form
- README update documenting the `media/videos/` folder

### Out of scope (Phase 9: Media Manager)
- Drag-and-drop upload via config panel
- Thumbnail generation for video previews
- Storage usage tracking
- Client-side caching / service worker for offline playback
- Remote push of media files to client devices

---

## Estimated effort
1 session (FastAPI mount + API endpoint + video page picker + config UI)
