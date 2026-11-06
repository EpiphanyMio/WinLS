"""Entry point for both the source tree and the PyInstaller executable."""
import asyncio
import json
import sys


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--list-devices":
        from pymobiledevice3.usbmux import list_devices
        print(json.dumps([device.serial for device in asyncio.run(list_devices()) if device.is_usb]), flush=True)
    elif len(sys.argv) > 2 and sys.argv[1] == "--iphone-bridge":
        from winloc.iphone_bridge import run, reply
        try:
            asyncio.run(run(sys.argv[2]))
        except Exception as exc:
            reply(ready=False, error=str(exc))
            sys.exit(1)
    else:
        from winloc.app import main
        raise SystemExit(main())
