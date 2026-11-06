"""Android physical-device mock location through ADB and the companion app."""
from __future__ import annotations

import re
import shutil
import subprocess
import threading

from .core import Coordinate

PACKAGE = "com.windowslocationsimulator.mock"
RECEIVER = PACKAGE + "/.LocationCommandReceiver"
ACTION = PACKAGE + ".LOCATION_COMMAND"
_RESULT = re.compile(r"Broadcast completed: result=(-?\d+)")


def _adb() -> str:
    executable = shutil.which("adb")
    if not executable:
        raise RuntimeError("未找到 adb。请安装 Android SDK Platform-Tools 并加入 PATH。")
    return executable


def connected_devices() -> list[str]:
    try:
        result = subprocess.run([_adb(), "devices", "-l"], capture_output=True, text=True,
                                timeout=15, check=True, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("ADB 设备查询超时。") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("ADB 设备查询失败：" + (exc.stderr or "").strip()) from exc
    devices = []
    for line in result.stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])
    return devices


class AndroidBridge:
    def __init__(self):
        self._active: set[str] = set()
        self._lock = threading.RLock()

    def _broadcast(self, serial: str, command: str, point: Coordinate | None = None):
        args = [_adb(), "-s", serial, "shell", "am", "broadcast", "-n", RECEIVER,
                "-a", ACTION, "--es", "command", command]
        if point is not None:
            args += ["--es", "latitude", f"{point.latitude:.8f}",
                     "--es", "longitude", f"{point.longitude:.8f}"]
        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=20,
                                    encoding="utf-8", errors="replace")
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("Android 定位命令超时；请检查 USB 连接。") from exc
        output = result.stdout + "\n" + result.stderr
        match = _RESULT.search(output)
        if result.returncode != 0 or match is None or match.group(1) != "200":
            detail = output.strip() or f"ADB 退出码 {result.returncode}"
            raise RuntimeError("Android 定位失败。请安装并打开配套 App，在开发者选项中将其设为模拟位置信息应用。" + detail)

    def set(self, serial: str, point: Coordinate):
        self._broadcast(serial, "set", point)
        with self._lock:
            self._active.add(serial)

    def clear(self, serial: str):
        self._broadcast(serial, "clear")
        with self._lock:
            self._active.discard(serial)

    def close(self):
        with self._lock:
            active = list(self._active)
        for serial in active:
            try:
                self.clear(serial)
            except RuntimeError:
                pass
