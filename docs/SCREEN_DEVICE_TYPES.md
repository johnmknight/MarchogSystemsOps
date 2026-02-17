# Screen Device Types — Deep Review

## Purpose

Define a taxonomy of screen device types for themed room installations.
This enables automations to target screens by **function** rather than
individual ID — e.g. "send lockdown to all door panels" or
"show diagnostic readout on all engineering screens."

---

## The Problem

Currently, automations target specific screen IDs (`scr-abc123`). These IDs
are ephemeral (change on reconnect) and don't carry any semantic meaning.
A "lockdown" automation shouldn't need to know which specific screens are
door panels — it should target the *category* "door-panel" and hit all of them.

---

## Thinking Through Themed Room Installations

A themed room build isn't just one type of space. Different builders create
different environments, and within each environment there are distinct
functional zones. We need device types that cover:

1. **In-universe functional screens** — panels that serve a narrative purpose
   (door controls, navigation, engineering readouts)
2. **Collectible/display screens** — showcasing items, memorabilia, artwork
3. **Ambient/atmospheric screens** — viewport simulations, background effects
4. **Utility screens** — clocks, weather, real-world information
5. **Entertainment screens** — video playback, media content

---

## Room-by-Room Walkthrough

### 1. CORRIDOR / HALLWAY
The transition space. Every themed build has passages between rooms.

| Location | Device Type | Purpose | Example Content |
|----------|------------|---------|-----------------|
| Beside each door | `door-panel` | Door status, access control display | Lock status, authorized personnel, countdown |
| Airlock-style doors | `airlock-panel` | Pressure/cycle status for airlock doors | Pressure readout, cycle animation, warning |
| Wall-mounted | `corridor-display` | Directional signage, deck status | Deck map, section alerts, wayfinding |
| Ceiling/soffit | `alert-beacon` | Emergency status indicator | Normal/alert/lockdown color state |

### 2. COCKPIT / BRIDGE / COMMAND CENTER
The hero room. Maximum screen density.

| Location | Device Type | Purpose | Example Content |
|----------|------------|---------|-----------------|
| Forward console | `navigation-panel` | Flight/navigation instruments | Star map, hyperspace, heading readout |
| Forward viewport area | `viewport` | Simulated window to space | Starfield, planet approach, hyperspace tunnel |
| Side console | `tactical-panel` | Weapons/shields/sensors | Targeting display, shield status, sensor sweep |
| Overhead panel | `systems-panel` | Ship systems overview | Power distribution, life support, reactor |
| Comm station | `comms-panel` | Communications interface | Incoming transmission, frequency scan |
| Center console/table | `holotable` | Tactical/strategic display | 3D map, mission briefing, fleet positions |
| Captain's chair armrest | `command-panel` | Captain's status display | Ship status summary, alert controls |

### 3. ENGINEERING / MECHANICAL ROOM
Where the ship's guts are visible.

| Location | Device Type | Purpose | Example Content |
|----------|------------|---------|-----------------|
| Main console | `engineering-panel` | Engine/reactor controls | Power output, fuel levels, temperature |
| Wall-mounted readout | `diagnostic-panel` | System diagnostics | Component health, error logs, warnings |
| Near machinery/props | `gauge-display` | Single-metric readout | Temperature, pressure, RPM, flow rate |
| Environmental | `life-support-panel` | Atmosphere/environment | O2 levels, CO2, humidity, temperature |

### 4. CANTINA / BAR AREA
Social space with ambient screens.

| Location | Device Type | Purpose | Example Content |
|----------|------------|---------|-----------------|
| Behind bar | `bar-display` | Menu, ambient visuals | Drink menu, species guide, bounty board |
| Wall-mounted | `entertainment-display` | Media playback, ambient | Podracing, music visualizer, holonet news |
| Table-embedded | `table-display` | Interactive tabletop | Dejarik board, ordering interface |
| Above bar/shelf | `collectible-display` | Showcase items | Rotating 3D model, item info card, lore |

### 5. QUARTERS / CABIN / BUNK
Private living space.

| Location | Device Type | Purpose | Example Content |
|----------|------------|---------|-----------------|
| Bedside/wall | `personal-panel` | Personal interface | Clock, messages, personal log |
| Viewport | `viewport` | Simulated window | Starfield, planet view, passing nebula |
| Desk | `workstation-display` | Work/research interface | Data files, schematics, research |

### 6. CARGO BAY / HANGAR
Large open space with industrial feel.

| Location | Device Type | Purpose | Example Content |
|----------|------------|---------|-----------------|
| Bay door area | `hangar-panel` | Bay door/loading controls | Bay status, docking, cargo manifest |
| Inventory wall | `cargo-display` | Cargo/inventory tracking | Manifest list, container status |
| Near vehicles/ships | `vehicle-display` | Vehicle status/info | Ship specs, fuel, maintenance log |

### 7. MEDBAY / MEDICAL
Clinical environment.

| Location | Device Type | Purpose | Example Content |
|----------|------------|---------|-----------------|
| Beside bed/station | `medical-panel` | Patient monitoring | Vital signs, heart rate, scan results |
| Wall-mounted | `medical-display` | Reference/diagnostic | Anatomy display, species database |

### 8. TROPHY / COLLECTION ROOM
Dedicated display space for memorabilia.

| Location | Device Type | Purpose | Example Content |
|----------|------------|---------|-----------------|
| Beside/behind items | `collectible-display` | Item showcase | 3D model rotation, lore card, provenance |
| Shelf-integrated | `label-display` | Item identification | Name, origin, date acquired, description |
| Feature wall | `gallery-display` | Rotating gallery | Slideshow, artwork, concept art |

### 9. GENERAL / ANY ROOM

| Location | Device Type | Purpose | Example Content |
|----------|------------|---------|-----------------|
| Any wall | `info-display` | General information | Clock, weather, news, system status |
| Near entrance | `door-panel` | Door/access control | Access status, room name, occupancy |
| Ceiling/hidden | `ambient-display` | Atmospheric effect | Color wash, subtle animation, mood |
| Any surface | `utility-display` | Real-world utility | Smart home data, network status, calendar |

---

## Proposed Device Type Categories

Based on the walkthrough, here are the consolidated categories:

### Access & Security
- `door-panel` — Standard door control/status display
- `airlock-panel` — Airlock-specific (pressure, cycle, warning)
- `alert-beacon` — Emergency/status indicator

### Navigation & Command
- `navigation-panel` — Flight/nav instruments
- `tactical-panel` — Weapons/shields/sensors
- `command-panel` — Captain/command summary
- `comms-panel` — Communications interface
- `holotable` — Tactical/strategic holographic display

### Engineering & Systems
- `engineering-panel` — Engine/reactor controls
- `diagnostic-panel` — System health/diagnostics
- `gauge-display` — Single-metric readout
- `life-support-panel` — Environmental/atmosphere
- `systems-panel` — General ship systems overview

### Viewport & Atmospheric
- `viewport` — Simulated window/porthole
- `ambient-display` — Atmospheric/mood screen
- `corridor-display` — Hallway signage/wayfinding

### Entertainment & Media
- `entertainment-display` — Video/media playback
- `bar-display` — Bar area specific content
- `table-display` — Embedded tabletop display

### Display & Collection
- `collectible-display` — Item showcase with 3D/info
- `label-display` — Small item identification label
- `gallery-display` — Rotating image/art gallery

### Utility & Personal
- `info-display` — General information (clock, weather)
- `utility-display` — Real-world data (smart home, network)
- `personal-panel` — Private/personal interface
- `workstation-display` — Desk/work interface
- `medical-panel` — Medical monitoring
- `medical-display` — Medical reference

### Specialized
- `hangar-panel` — Bay door/loading controls
- `cargo-display` — Inventory/manifest
- `vehicle-display` — Vehicle status/specs

---

## Automation Targeting Examples

With device types, automations become powerful and declarative:

| Automation | Target | Action |
|-----------|--------|--------|
| Full Lockdown | `door-panel`, `airlock-panel` | Navigate → lockdown page |
| External Lockdown | `airlock-panel` only | Navigate → airlock-sealed page |
| Red Alert | ALL device types | Navigate → red-alert page |
| Battle Stations | `tactical-panel`, `navigation-panel`, `command-panel` | Navigate → combat readout |
| All Clear | `door-panel`, `airlock-panel`, `alert-beacon` | Navigate → standby |
| Movie Night | `entertainment-display`, `viewport` | Navigate → video page |
| Showcase Mode | `collectible-display`, `gallery-display` | Navigate → slideshow |
| Engineering Emergency | `engineering-panel`, `diagnostic-panel`, `gauge-display` | Navigate → warning page |
| Night Mode | ALL | Navigate → standby (dim) |

---

## Implementation Plan

### Phase 1: Add device_type to screen_configs
- New column: `device_type TEXT DEFAULT 'info-display'`
- Dropdown in config UI when adding/editing screens in zones
- Categories grouped in the dropdown for easy selection
- Multiple device types per screen? Probably not — one primary type is cleaner

### Phase 2: Update automations to target by device type
- Actions get a new `target_type` field: `"screens"` (specific IDs) or `"device_types"` (categories)
- `target_device_types: ["door-panel", "airlock-panel"]`
- Run endpoint resolves device types → matching screen IDs at execution time
- UI: toggle between "Select Screens" and "Select Device Types" in automation editor

### Phase 3: Smart targeting
- Combine: "all door-panels IN room Bridge"
- Exclude: "all screens EXCEPT viewports"
- Priority: device type targeting > room targeting > individual screen targeting

---

## Open Questions

1. Should we support multiple device types per screen? (e.g. a door panel that's
   also a general info display) — Recommend: No, keep it single-type for clarity.
   Use the most specific type.

2. Should device types be user-editable or fixed? — Recommend: Ship with a
   pre-built list, allow custom types later. The pre-built list covers 95% of cases.

3. Should the device type affect what pages are suggested/allowed? — Nice to have:
   a door-panel probably shouldn't show a drink menu. Could be soft guidance rather
   than hard restriction.

4. Icon mapping — each device type should have a Tabler icon for the UI.
