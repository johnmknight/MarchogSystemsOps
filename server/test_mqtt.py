"""Quick MQTT pub/sub smoke test"""
import asyncio, json, sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import aiomqtt

async def test():
    async with aiomqtt.Client("localhost", 1883) as sub:
        await sub.subscribe("marchog/#")

        async with aiomqtt.Client("localhost", 1883) as pub:
            await pub.publish("marchog/type/door-panel", json.dumps({
                "type": "navigate",
                "page_id": "selfdestruct",
                "source": "test"
            }))

        async for msg in sub.messages:
            topic = str(msg.topic)
            payload = json.loads(msg.payload.decode())
            print(f"Topic: {topic}")
            print(f"Type: {payload.get('type')}")
            print(f"Page: {payload.get('page_id')}")
            print("MQTT PUBSUB TEST PASSED")
            break

asyncio.run(test())
