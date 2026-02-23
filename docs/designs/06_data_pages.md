# Design: Data Integration Pages

**Product Review Item:** Gap analysis — "Stream real-time data to your screens"
**Production Queue:** Phase 5
**Priority:** HIGH — Proves the live data pitch with 3 showcase pages

---

## Problem

The pitch lists 11 types of live data (weather, news, ISS, stocks, etc.) but
zero data integration pages exist. Every current page is either ambient animation
(hyperspace, logo-3d), an HUD (viewfinder), a utility (standby, selfdestruct),
or a video player. The "stream real-time data" promise is entirely undelivered.

Building 2-3 showcase data pages proves the concept and gives beta testers
something tangible to show visitors.

---

## Selected Pages

### 1. Weather Station (`weather.html`)
**Data source:** Open-Meteo API (free, no API key needed)
**Refresh:** Every 15 minutes
**Layout:**

```
┌──────────────────────────────────────────────────────┐
│  ENVIRONMENTAL MONITORING SYSTEM                     │
│  ═══════════════════════════════════════════════      │
│                                                      │
│  ┌─ CURRENT ──────────┐  ┌─ ATMOSPHERIC ─────────┐  │
│  │                     │  │                       │  │
│  │   72°F              │  │  Humidity:    45%     │  │
│  │   CLEAR SKIES       │  │  Pressure: 1013 hPa  │  │
│  │                     │  │  Wind:     8 mph NW   │  │
│  │   ☀ Feels: 70°F    │  │  UV Index: 6          │  │
│  └─────────────────────┘  └───────────────────────┘  │
│                                                      │
│  ┌─ FORECAST ────────────────────────────────────┐   │
│  │  TODAY    TUE    WED    THU    FRI    SAT     │   │
│  │  72/58   68/52  75/60  71/55  69/50  73/58   │   │
│  │   ☀       ⛅     ☀      🌧     ⛅     ☀      │   │
│  └───────────────────────────────────────────────┘   │
│                                                      │
│  ┌─ ALERTS ──────────────────────────────────────┐   │
│  │  ▶ NO ACTIVE WEATHER ALERTS                   │   │
│  └───────────────────────────────────────────────┘   │
│                                                      │
│  TERRA · 27.9506°N 82.5248°W · UPDATED 14:30 UTC    │
└──────────────────────────────────────────────────────┘
```

**Styling:** Amber/green monochrome readout. Aurebesh section headers.
Animated scan lines. Temperature as large digits. Weather codes mapped
to in-universe descriptions ("CLEAR SKIES" not "sunny").

**Configurable params:**
```json
{
    "latitude": 27.9506,
    "longitude": -82.5248,
    "units": "imperial",
    "location_name": "TERRA",
    "refresh_minutes": 15
}
```

**API call:**
```
https://api.open-meteo.com/v1/forecast?latitude=27.95&longitude=-82.52
    &current=temperature_2m,relative_humidity_2m,wind_speed_10m,
             wind_direction_10m,surface_pressure,uv_index,weather_code
    &daily=temperature_2m_max,temperature_2m_min,weather_code
    &temperature_unit=fahrenheit&wind_speed_unit=mph
    &timezone=America/New_York&forecast_days=7
```

### 2. Galactic Chronometer (`chrono.html`)
**Data source:** JavaScript `Date` object (no API needed)
**Refresh:** Every second
**Layout:**

```
┌──────────────────────────────────────────────────────┐
│  GALACTIC CHRONOMETER                                │
│  ═══════════════════════════════════════════════      │
│                                                      │
│  ┌─ LOCAL TIME ──────────────────────────────────┐   │
│  │                                               │   │
│  │         14 : 30 : 45                          │   │
│  │         EASTERN STANDARD                      │   │
│  │         SUNDAY · 22 FEBRUARY 2026             │   │
│  │                                               │   │
│  └───────────────────────────────────────────────┘   │
│                                                      │
│  ┌─ SECTOR CLOCKS ───────────────────────────────┐   │
│  │                                               │   │
│  │  CORUSCANT (UTC)     19:30    ██████████░░    │   │
│  │  TATOOINE (PST)      11:30    ████████░░░░    │   │
│  │  NABOO (JST)         04:30+1  ██░░░░░░░░░░    │   │
│  │  MANDALORE (GMT)     19:30    ██████████░░    │   │
│  │  KASHYYYK (IST)      01:00+1  ░░░░░░░░░░░░    │   │
│  │                                               │   │
│  └───────────────────────────────────────────────┘   │
│                                                      │
│  STARDATE 2026.053                                   │
└──────────────────────────────────────────────────────┘
```

**Styling:** Large fixed-width digits for local time (same style as ArtemisOps
countdown). Sector clocks show progress bars for day/night cycle. Aurebesh labels.
In-universe timezone aliases configurable.

**Configurable params:**
```json
{
    "local_timezone": "America/New_York",
    "local_alias": "BASE",
    "zones": [
        {"tz": "UTC", "alias": "CORUSCANT"},
        {"tz": "America/Los_Angeles", "alias": "TATOOINE"},
        {"tz": "Asia/Tokyo", "alias": "NABOO"},
        {"tz": "Europe/London", "alias": "MANDALORE"},
        {"tz": "Asia/Kolkata", "alias": "KASHYYYK"}
    ],
    "show_stardate": true
}
```

### 3. Comms Feed / News Ticker (`comms.html`)
**Data source:** RSS feeds via server-side proxy (CORS bypass)
**Refresh:** Every 10 minutes
**Layout:**

```
┌──────────────────────────────────────────────────────┐
│  ◉ INCOMING TRANSMISSIONS                            │
│  ═══════════════════════════════════════════════      │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │  ▶ PRIORITY ALPHA                              │  │
│  │  NASA confirms Artemis III launch window       │  │
│  │  for September 2026 remains on track           │  │
│  │  SOURCE: REUTERS · 14:22 UTC                   │  │
│  ├────────────────────────────────────────────────┤  │
│  │  ▶ STANDARD                                    │  │
│  │  SpaceX Starship completes 10th orbital        │  │
│  │  flight test with full reuse demonstration     │  │
│  │  SOURCE: SPACENEWS · 13:45 UTC                 │  │
│  ├────────────────────────────────────────────────┤  │
│  │  ▶ STANDARD                                    │  │
│  │  New archaeological discovery reveals ancient  │  │
│  │  Roman fort beneath London construction site   │  │
│  │  SOURCE: BBC · 12:30 UTC                       │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  3 TRANSMISSIONS · NEXT SCAN IN 8:42                 │
└──────────────────────────────────────────────────────┘
```

**Styling:** Cards auto-scroll vertically with a slow fade transition.
"INCOMING TRANSMISSION" flash animation when new items arrive.
Priority classification based on keywords. Aurebesh decorative elements.

**Server-side RSS proxy:**
```python
@app.get("/api/feeds")
async def get_feeds():
    """Fetch and parse RSS feeds, return as JSON."""
    import feedparser
    feeds = [
        {"url": "https://www.nasa.gov/feed/", "source": "NASA"},
        {"url": "https://feeds.bbci.co.uk/news/rss.xml", "source": "BBC"},
    ]
    items = []
    for feed_conf in feeds:
        feed = feedparser.parse(feed_conf["url"])
        for entry in feed.entries[:5]:
            items.append({
                "title": entry.get("title", ""),
                "summary": entry.get("summary", "")[:200],
                "source": feed_conf["source"],
                "published": entry.get("published", ""),
                "link": entry.get("link", "")
            })
    # Sort by date, newest first
    items.sort(key=lambda x: x.get("published", ""), reverse=True)
    return items[:15]
```

**Configurable params:**
```json
{
    "feeds": [
        {"url": "https://www.nasa.gov/feed/", "source": "COMMAND", "priority": "alpha"},
        {"url": "https://feeds.bbci.co.uk/news/rss.xml", "source": "BBC", "priority": "standard"}
    ],
    "max_items": 10,
    "refresh_minutes": 10,
    "scroll_speed": "slow"
}
```

**Dependency:** `feedparser` added to `requirements.txt`

---

## Page Registration

Each page gets added to `client/pages/pages.json`:

```json
[
    {
        "id": "weather",
        "name": "Weather Station",
        "file": "weather.html",
        "icon": "ti-cloud",
        "category": "data",
        "params": {
            "latitude": 27.9506,
            "longitude": -82.5248,
            "units": "imperial",
            "location_name": "TERRA"
        }
    },
    {
        "id": "chrono",
        "name": "Galactic Chronometer",
        "file": "chrono.html",
        "icon": "ti-clock",
        "category": "data",
        "params": {}
    },
    {
        "id": "comms",
        "name": "Comms Feed",
        "file": "comms.html",
        "icon": "ti-antenna",
        "category": "data",
        "params": {}
    }
]
```

New category: `"data"` — distinguishes data pages from ambient/hud/general.

---

## Scope

### In scope
- `weather.html` — Open-Meteo API, no key required, configurable location
- `chrono.html` — Pure JS clocks, configurable timezones with in-universe aliases
- `comms.html` — RSS via server proxy, configurable feed URLs
- Server-side `/api/feeds` RSS proxy endpoint
- Pages registered in pages.json with params
- Thumbnails generated for all three

### Out of scope
- ISS tracker page (already have this in ArtemisOps — could port later)
- Stock/crypto ticker
- Home network status
- Social media feeds
- Custom data binding / widget system (Phase backlog: page builder)

---

## Estimated effort
2-3 sessions (1 per page + server proxy + thumbnails)


---

## Weather Page — Geographic Data & Visual Design Notes

### Data Sources

| File | Source | License | Size | Contents |
|------|--------|---------|------|----------|
| `states_data.js` | Natural Earth 10m admin-1 | CC0 Public Domain | 42 KB | US state boundaries, high-fidelity GIS shorelines |
| `lakes_data.js` | Natural Earth 10m lakes | CC0 Public Domain | 19 KB | 12 major US lakes (rank 0-2), reduced resolution |
| `land_data.js` | Natural Earth coastlines | CC0 Public Domain | 21 KB | Global continent outlines for Three.js globe |

All sourced from [martynafford/natural-earth-geojson](https://github.com/martynafford/natural-earth-geojson)
and [nvkelso/natural-earth-vector](https://github.com/nvkelso/natural-earth-vector).

### Lake Data — 75% Point Reduction (Intentional)

The Natural Earth 10m lakes dataset provides high-fidelity shoreline polygons
(5,185 total coordinate points across 12 major US lakes). We deliberately reduced
these to **~25% of original resolution** (1,233 points) by sampling every 4th vertex.

**Why:** The full-resolution lake outlines produced smooth, organic curves that
visually clashed with the tactical HUD aesthetic. The state boundary data — while
also high-fidelity — renders as angular wireframe segments due to vertex node
rendering and the glow/double-stroke treatment. At full resolution, lakes looked
like they belonged to a different visual system: too smooth, too "GIS", not enough
"sensor scan". The reduced resolution produces geometric, angular lake outlines
that match the state borders and reinforce the "Planetary Surface Monitor" concept
of digitized terrain data being reconstructed from limited sensor readings.

**Before/after comparison:**
- Lake Okeechobee: 66 pts → 18 pts (27%) — still clearly recognizable at FL zoom
- Lake Superior: 897 pts → 213 pts (24%) — angular but reads correctly at MI zoom
- All lakes maintain shape recognition while gaining visual consistency

**Rendering:** Lakes use identical border treatment as active state boundaries:
outer glow (shadowBlur 12), double stroke (1.6px + 1.1px inner), vertex nodes
(1.8px radius), and dark water fill (rgba 0,8,24 @ 0.7 opacity).

### Future: Regional Data Loading

Currently all geographic data loads monolithically. A backlog item exists in
PRODUCTION_QUEUE.md to re-download both datasets and split by geographic region
(Northeast, Southeast, Midwest, Southwest, West, Great Lakes, Pacific) for
on-demand loading per active state, reducing initial page payload.
