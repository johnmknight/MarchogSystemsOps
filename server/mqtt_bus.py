"""
MarchogSystemsOps MQTT Integration
Connects to Mosquitto broker and bridges MQTT <-> WebSocket.

On Windows, paho-mqtt requires SelectorEventLoop but uvicorn uses
ProactorEventLoop. We solve this by running the MQTT client in a
dedicated thread with its own SelectorEventLoop.
"""
import asyncio
import sys
import json
import logging
import threading
from datetime import datetime, timezone
from typing import Optional

import aiomqtt

logger = logging.getLogger("marchog.mqtt")

BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC_PREFIX = "marchog"

# Aliases for main.py compatibility
MQTT_HOST = BROKER_HOST
MQTT_PORT = BROKER_PORT


class MQTTBus:
    """MQTT message bus with Windows-compatible threading.

    Runs the MQTT client in a dedicated thread with SelectorEventLoop
    to avoid ProactorEventLoop incompatibility on Windows.
    """

    def __init__(self, app_state: dict):
        self.app_state = app_state
        self._connected = False
        self._thread: Optional[threading.Thread] = None
        self._mqtt_loop: Optional[asyncio.AbstractEventLoop] = None
        self._client: Optional[aiomqtt.Client] = None
        self._stopping = False
        self._handlers: dict[str, list] = {}
        # Queue for cross-thread publish requests
        self._publish_queue: asyncio.Queue = asyncio.Queue()
        # Reference to the main event loop (uvicorn's)
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None

    # ── Lifecycle ─────────────────────────────────────

    async def start(self):
        """Start the MQTT thread."""
        self._main_loop = asyncio.get_running_loop()
        self._stopping = False
        self._thread = threading.Thread(target=self._run_thread, daemon=True)
        self._thread.start()
        logger.info("MQTT bus thread started")

    async def stop(self):
        """Stop the MQTT thread."""
        self._stopping = True
        if self._mqtt_loop and self._mqtt_loop.is_running():
            self._mqtt_loop.call_soon_threadsafe(self._mqtt_loop.stop)
        if self._thread:
            self._thread.join(timeout=5)
        self._connected = False
        logger.info("MQTT bus stopped")

    def _run_thread(self):
        """Thread entry: create SelectorEventLoop and run MQTT."""
        if sys.platform == "win32":
            loop = asyncio.SelectorEventLoop()
        else:
            loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._mqtt_loop = loop
        try:
            loop.run_until_complete(self._mqtt_main())
        except Exception as e:
            logger.error(f"MQTT thread error: {e}")
        finally:
            loop.close()

    async def _mqtt_main(self):
        """Main MQTT loop — connect, subscribe, dispatch."""
        retry_delay = 1
        while not self._stopping:
            try:
                async with aiomqtt.Client(
                    BROKER_HOST,
                    port=BROKER_PORT,
                    identifier="marchog-server",
                ) as client:
                    self._client = client
                    self._connected = True
                    retry_delay = 1
                    logger.info(f"Connected to MQTT broker at {BROKER_HOST}:{BROKER_PORT}")

                    # Subscribe to topics the server cares about
                    await client.subscribe(f"{TOPIC_PREFIX}/action/#")
                    await client.subscribe(f"{TOPIC_PREFIX}/event/#")
                    await client.subscribe(f"{TOPIC_PREFIX}/sensor/#")
                    await client.subscribe(f"{TOPIC_PREFIX}/heartbeat/#")
                    logger.info("Subscribed to action/event/sensor/heartbeat topics")

                    # Process incoming messages and outgoing publishes concurrently
                    await asyncio.gather(
                        self._listen(client),
                        self._process_publish_queue(client),
                    )

            except aiomqtt.MqttError as e:
                self._connected = False
                self._client = None
                if self._stopping:
                    break
                logger.warning(f"MQTT connection lost: {e}. Retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 30)
            except Exception as e:
                if self._stopping:
                    break
                logger.error(f"MQTT unexpected error: {e}")
                await asyncio.sleep(5)

    async def _listen(self, client: aiomqtt.Client):
        """Listen for incoming MQTT messages."""
        async for message in client.messages:
            if self._stopping:
                break
            await self._dispatch(message)

    async def _process_publish_queue(self, client: aiomqtt.Client):
        """Process publish requests from the main thread."""
        while not self._stopping:
            try:
                # Check queue with timeout so we can exit cleanly
                topic, payload, retain = await asyncio.wait_for(
                    self._get_from_queue(), timeout=1.0
                )
                await client.publish(topic, json.dumps(payload), retain=retain)
                logger.debug(f"Published to {topic}: {payload.get('type', '?')}")
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Publish queue error: {e}")

    async def _get_from_queue(self):
        """Get an item from the cross-thread queue."""
        # We need to bridge the main loop's queue to the MQTT loop
        while True:
            try:
                return self._publish_queue.get_nowait()
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.05)

    # ── Publishing (thread-safe) ──────────────────────

    def _enqueue_publish(self, topic: str, payload: dict, retain: bool = False):
        """Thread-safe: enqueue a publish request for the MQTT thread."""
        if "timestamp" not in payload:
            payload["timestamp"] = datetime.now(timezone.utc).isoformat()
        self._publish_queue.put_nowait((topic, payload, retain))

    async def publish(self, topic: str, payload: dict, retain: bool = False) -> bool:
        """Publish a JSON message to an MQTT topic (callable from main thread)."""
        if not self._connected:
            logger.warning(f"MQTT not connected, cannot publish to {topic}")
            return False
        self._enqueue_publish(topic, payload, retain)
        return True

    async def publish_navigate(self, targets: list[str], page_id: str,
                                params: dict = None, source: str = "server"):
        """Publish navigation commands to target topics."""
        payload = {
            "type": "navigate",
            "page_id": page_id,
            "params": params or {},
            "source": source,
        }
        for target in targets:
            if target.startswith("marchog/"):
                topic = target
            elif target.startswith("scr-"):
                topic = f"{TOPIC_PREFIX}/screen/{target}"
            else:
                topic = f"{TOPIC_PREFIX}/{target}"
            await self.publish(topic, payload)

    # ── Dispatching ───────────────────────────────────

    def on(self, topic_pattern: str, handler):
        """Register a handler for a topic pattern."""
        if topic_pattern not in self._handlers:
            self._handlers[topic_pattern] = []
        self._handlers[topic_pattern].append(handler)

    async def _dispatch(self, message):
        """Dispatch incoming MQTT message to handlers and WS bridge."""
        topic = str(message.topic)
        try:
            payload = json.loads(message.payload.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = {"raw": message.payload.decode(errors="replace")}

        logger.debug(f"Received {topic}: {payload.get('type', '?')}")

        # Match handlers
        for pattern, handlers in self._handlers.items():
            if topic.startswith(pattern.rstrip("#").rstrip("/")):
                for handler in handlers:
                    try:
                        await handler(topic, payload)
                    except Exception as e:
                        logger.error(f"Handler error for {topic}: {e}")

        # Bridge navigate messages to WebSocket screens
        if payload.get("type") == "navigate":
            self._bridge_to_websocket(topic, payload)

    def _bridge_to_websocket(self, topic: str, payload: dict):
        """Forward MQTT navigate to matching WS screens (cross-thread)."""
        if not self._main_loop:
            return

        screens = self.app_state.get("screens", {})
        screen_meta = self.app_state.get("screen_meta", {})

        for screen_id, screen_data in screens.items():
            if self._screen_matches_topic(screen_id, screen_meta.get(screen_id, {}), topic):
                ws = screen_data.get("ws")
                if ws:
                    msg = {
                        "type": "navigate",
                        "page": payload.get("page_id"),
                        "params": payload.get("params", {}),
                    }
                    # Schedule WS send on the main event loop
                    asyncio.run_coroutine_threadsafe(
                        ws.send_json(msg), self._main_loop
                    )
                    logger.debug(f"Bridged {topic} -> WS {screen_id}")

    def _screen_matches_topic(self, screen_id: str, meta: dict, topic: str) -> bool:
        """Check if a screen should receive a message from the given topic."""
        parts = topic.split("/")
        if len(parts) < 2:
            return False

        # marchog/all
        if topic == f"{TOPIC_PREFIX}/all":
            return True

        # marchog/screen/{screen_id}
        if topic == f"{TOPIC_PREFIX}/screen/{screen_id}":
            return True

        # marchog/type/{device_type}
        if len(parts) >= 3 and parts[1] == "type":
            dtype = parts[2]
            if meta.get("device_type") == dtype:
                return True
            if meta.get("device_type_secondary") == dtype:
                return True

        # marchog/room/{room_id}
        if len(parts) >= 3 and parts[1] == "room":
            if meta.get("room_id") == parts[2]:
                return True

        # marchog/zone/{zone_id}
        if len(parts) >= 3 and parts[1] == "zone":
            if meta.get("zone_id") == parts[2]:
                return True

        return False

    # ── Status ────────────────────────────────────────

    @property
    def connected(self) -> bool:
        return self._connected

    def status(self) -> dict:
        return {
            "connected": self._connected,
            "broker": f"{BROKER_HOST}:{BROKER_PORT}",
        }


# ═══════════════════════════════════════════════════════
#  Module-level singleton API
# ═══════════════════════════════════════════════════════

_bus: Optional[MQTTBus] = None


async def start(app_state: dict):
    global _bus
    _bus = MQTTBus(app_state)
    await _bus.start()


async def stop():
    if _bus:
        await _bus.stop()


def get_bus() -> Optional[MQTTBus]:
    return _bus


def is_connected() -> bool:
    return _bus.connected if _bus else False


async def publish(topic: str, payload: dict, retain: bool = False) -> bool:
    if _bus:
        return await _bus.publish(topic, payload, retain)
    return False


async def publish_navigate(targets: list[str], page_id: str,
                           params: dict = None, source: str = "server"):
    if _bus:
        return await _bus.publish_navigate(targets, page_id, params, source)


async def publish_heartbeat(device_id: str, device_type: str = "screen"):
    if _bus:
        return await _bus.publish(
            f"{TOPIC_PREFIX}/heartbeat/{device_id}",
            {
                "type": "heartbeat",
                "device_id": device_id,
                "device_type": device_type,
                "status": "online",
            },
            retain=True,
        )


def status() -> dict:
    if _bus:
        return _bus.status()
    return {"connected": False, "broker": f"{BROKER_HOST}:{BROKER_PORT}"}
