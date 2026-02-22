# Design: Client Auto-Reconnect with Visual Feedback

**Product Review Item:** #11 — Client Auto-Reconnect with Visual Feedback
**Production Queue:** Phase 4
**Priority:** CRITICAL — Essential for 24/7 unattended operation

---

## Problem

When a screen loses its WebSocket connection (WiFi drop, server restart, power blip),
the current behavior is:
- The iframe keeps showing the last-loaded page (frozen, not blank)
- A tiny "DISCONNECTED" status badge appears in the corner
- Exponential backoff reconnect runs silently in the background
- On reconnect, the screen stays on whatever page it was showing — it does NOT
  re-request its assignment from the server

For screens behind panels running 24/7, a frozen page with no visible indication
of disconnection is effectively invisible damage. The operator won't know until
they physically check or notice stale content.

---

## Current State

The client shell (`index.html`) already has:
- `connectWebSocket()` with `onclose` → `scheduleReconnect()`
- Exponential backoff: `Math.min(1000 * 2^(attempts-1), 30000)` (1s→2s→4s→...→30s cap)
- `setConnectionStatus(status)` updating a small corner badge
- `wsReconnectAttempts` counter, reset to 0 on successful connect
- On reconnect `onopen`: calls `reportPage()` but does NOT request current assignment

What's missing:
1. **Full-screen overlay** — the corner badge is invisible on a 7" tablet across the room
2. **Assignment re-sync** — after reconnect, screen should ask "what should I be showing?"
3. **Themed visual** — the overlay should look in-universe, not like an error
4. **Connection attempt counter visible to user** — for debugging

---

## Design

### Reconnection overlay

A full-screen semi-transparent overlay that appears on disconnect and disappears on reconnect.
Themed as an in-universe "SIGNAL LOST" display:

```
┌──────────────────────────────────────────────┐
│                                              │
│          ╔══════════════════════╗            │
│          ║   SIGNAL LOST        ║            │
│          ║                      ║            │
│          ║   ◉ RECONNECTING     ║            │
│          ║   ATTEMPT 3 / 30s    ║            │
│          ║                      ║            │
│          ║   ▓▓▓▓▓░░░░░░░░░░   ║            │
│          ║                      ║            │
│          ║   scr-abc123         ║            │
│          ║   MARCHOG SYSTEMS    ║            │
│          ╚══════════════════════╝            │
│                                              │
│     (frozen last page visible underneath)    │
└──────────────────────────────────────────────┘
```

- Semi-transparent dark overlay (rgba(0,0,0,0.85)) over the iframe
- Aurebesh "SIGNAL LOST" heading with scan line animation
- Pulsing dot next to "RECONNECTING"
- Attempt counter and current backoff delay
- Progress bar showing time until next retry
- Screen ID and Marchog Systems branding at bottom
- Subtle CRT flicker effect on the overlay (CSS animation)

### HTML structure

```html
<!-- Add inside index.html, above the iframe -->
<div id="reconnectOverlay" class="reconnect-overlay hidden">
    <div class="reconnect-content">
        <div class="reconnect-title" data-aurebesh="SIGNAL LOST">SIGNAL LOST</div>
        <div class="reconnect-status">
            <span class="reconnect-dot"></span>
            <span>RECONNECTING</span>
        </div>
        <div class="reconnect-detail">
            ATTEMPT <span id="reconnectAttempt">1</span>
            · RETRY IN <span id="reconnectCountdown">1</span>s
        </div>
        <div class="reconnect-progress">
            <div class="reconnect-progress-bar" id="reconnectProgressBar"></div>
        </div>
        <div class="reconnect-screen-id" id="reconnectScreenId"></div>
    </div>
</div>
```

### CSS

```css
.reconnect-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    z-index: 9999;
    background: rgba(0, 0, 0, 0.85);
    display: flex;
    align-items: center;
    justify-content: center;
    animation: crtFlicker 0.15s infinite alternate;
}

.reconnect-overlay.hidden { display: none; }

.reconnect-content {
    text-align: center;
    font-family: 'Share Tech Mono', monospace;
    color: var(--amber, #f5a623);
    padding: 40px;
    border: 1px solid var(--amber, #f5a623);
    background: rgba(0, 0, 0, 0.6);
}

.reconnect-title {
    font-family: 'Aurebesh', monospace;
    font-size: 2.5rem;
    letter-spacing: 4px;
    margin-bottom: 24px;
    text-shadow: 0 0 10px var(--amber, #f5a623);
}

.reconnect-dot {
    display: inline-block;
    width: 10px; height: 10px;
    border-radius: 50%;
    background: var(--amber, #f5a623);
    animation: pulse 1s ease-in-out infinite;
    margin-right: 8px;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}

@keyframes crtFlicker {
    0% { opacity: 1; }
    100% { opacity: 0.97; }
}
```

### JavaScript changes to Shell object

```javascript
// Enhanced setConnectionStatus
setConnectionStatus(status) {
    const el = document.getElementById('connStatus');
    el.classList.remove('connected', 'disconnected', 'connecting');
    el.classList.add(status);
    document.getElementById('connText').textContent = status.toUpperCase();

    // Overlay control
    const overlay = document.getElementById('reconnectOverlay');
    if (status === 'disconnected' || status === 'connecting') {
        overlay.classList.remove('hidden');
        document.getElementById('reconnectScreenId').textContent = this.screenId;
    } else if (status === 'connected') {
        overlay.classList.add('hidden');
        this.clearReconnectCountdown();
    }
},

// Enhanced scheduleReconnect with countdown
scheduleReconnect() {
    this.wsReconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.wsReconnectAttempts - 1), 30000);

    document.getElementById('reconnectAttempt').textContent = this.wsReconnectAttempts;

    // Countdown timer
    let remaining = delay / 1000;
    document.getElementById('reconnectCountdown').textContent = remaining;
    this.reconnectCountdownInterval = setInterval(() => {
        remaining = Math.max(0, remaining - 1);
        document.getElementById('reconnectCountdown').textContent = remaining;
        // Progress bar
        const pct = (1 - (remaining / (delay / 1000))) * 100;
        document.getElementById('reconnectProgressBar').style.width = pct + '%';
    }, 1000);

    setTimeout(() => this.connectWebSocket(), delay);
},

clearReconnectCountdown() {
    if (this.reconnectCountdownInterval) {
        clearInterval(this.reconnectCountdownInterval);
        this.reconnectCountdownInterval = null;
    }
},
```

### Assignment re-sync on reconnect

The critical missing piece: after reconnecting, the screen must ask the server
what it should be showing. The server may have changed scenes while the screen
was disconnected.

```javascript
// Enhanced onopen handler
this.ws.onopen = () => {
    console.log('WebSocket connected');
    this.wsReconnectAttempts = 0;
    this.setConnectionStatus('connected');
    this.reportPage();

    // Request current assignment from server
    this.ws.send(JSON.stringify({ type: 'request_assignment' }));
};
```

Server-side in `main.py`, handle the `request_assignment` message:
```python
elif msg_type == "request_assignment":
    assignment = await get_screen_assignment(screen_id)
    if assignment:
        page_id = assignment.get("static_page", "standby")
        params = json.loads(assignment.get("params_override") or "null")
        await websocket.send_json({
            "type": "navigate",
            "page_id": page_id,
            "params": params
        })
```

This ensures the screen always lands on the correct page after reconnection,
even if scenes changed while it was offline.

---

## Scope

### In scope
- Full-screen "SIGNAL LOST" reconnect overlay with Aurebesh styling
- Countdown timer showing attempt number and seconds to next retry
- Progress bar for visual countdown
- Assignment re-sync on reconnect (`request_assignment` message)
- Server-side handler to send current assignment on request

### Out of scope
- Sound effects on disconnect/reconnect (Phase 7 audio zones)
- MQTT-direct reconnect (future browser MQTT.js)
- Custom overlay per device type

---

## Estimated effort
1 session (overlay HTML/CSS + JS reconnect enhancements + server handler)
