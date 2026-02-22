# Design: Scene Scheduling & Automation Triggers

**Product Review Item:** #2 — Scene Scheduling / Automation Triggers
**Production Queue:** Phase 7 (merged with Choreography)
**Priority:** MEDIUM

---

## Problem

The pitch positions one-button scene switching as the killer feature. But most of
the time, rooms need automatic behavior — dim at night, wake on entry, party mode
on a schedule. Without scheduling, someone must manually trigger every transition.

---

## Design

### Time-based scheduling

Add a `schedules` array to automations.json:

```json
{
    "id": "night-mode",
    "name": "Night Mode",
    "trigger": {
        "type": "schedule",
        "cron": "0 23 * * *",
        "timezone": "America/New_York"
    },
    "actions": [
        {"type": "activate_scene", "scene_id": "ambient-night"}
    ]
}
```

Server-side: use `APScheduler` (lightweight async scheduler) to evaluate cron
expressions. On startup, load all schedule-type automations and register jobs.

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler()

async def load_schedules():
    automations = load_automations()
    for auto in automations:
        trigger = auto.get("trigger", {})
        if trigger.get("type") == "schedule":
            scheduler.add_job(
                run_automation, CronTrigger.from_crontab(trigger["cron"]),
                args=[auto["id"]], id=auto["id"], replace_existing=True
            )
    scheduler.start()
```

### Event-driven triggers

MQTT-based triggers (already partially designed in PUBSUB_ARCHITECTURE.md):

```json
{
    "trigger": {
        "type": "mqtt",
        "topic": "marchog/sensor/corridor-a-motion/motion",
        "condition": {"status": "detected"}
    },
    "actions": [
        {"type": "activate_scene", "scene_id": "welcome-mode"}
    ]
}
```

Server subscribes to `marchog/action/#` and `marchog/sensor/#` already —
add trigger matching when messages arrive.

### Config UI: Visual scheduler

A timeline view in the Automations tab:

```
┌─ SCHEDULE ──────────────────────────────────────────┐
│                                                      │
│  00:00    06:00    12:00    18:00    24:00           │
│  ├────────┼────────┼────────┼────────┤              │
│  │ Night  │ Morning│  Day   │Evening │ Night        │
│  │ Mode   │ Ops    │  Ops   │ Ambient│ Mode         │
│  └────────┴────────┴────────┴────────┘              │
│                                                      │
│  [+ Add Schedule]                                    │
└──────────────────────────────────────────────────────┘
```

### Dependencies
- `apscheduler` added to requirements.txt

---

## Estimated effort
2 sessions (scheduler engine + MQTT trigger matching + config UI timeline)
