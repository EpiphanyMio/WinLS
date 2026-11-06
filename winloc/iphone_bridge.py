"""Persistent pymobiledevice3 DVT location session; one JSON request per line."""
import asyncio
import json
import sys

from pymobiledevice3.remote.userspace_tunnel import UserspaceRsdTunnel
from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
from pymobiledevice3.services.dvt.instruments.location_simulation import LocationSimulation


def reply(**values):
    print(json.dumps(values, ensure_ascii=False), flush=True)


async def run(udid):
    async with UserspaceRsdTunnel(serial=udid) as device:
        async with DvtProvider(device) as dvt, LocationSimulation(dvt) as location:
            reply(ready=True)
            while True:
                line = await asyncio.to_thread(sys.stdin.readline)
                if not line:
                    await location.clear()
                    return
                try:
                    request = json.loads(line)
                    if request.get("action") == "set":
                        await location.set(float(request["latitude"]), float(request["longitude"]))
                        reply(ok=True)
                    elif request.get("action") == "clear":
                        await location.clear()
                        reply(ok=True)
                    else:
                        reply(ok=False, error="未知定位命令")
                except Exception as error:
                    reply(ok=False, error=str(error))


if __name__ == "__main__":
    try:
        asyncio.run(run(sys.argv[1]))
    except Exception as error:
        reply(ready=False, error=str(error))
        sys.exit(1)
