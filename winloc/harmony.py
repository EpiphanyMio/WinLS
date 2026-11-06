"""HarmonyOS 7+ physical-device location replay using Huawei's hdc testhelper."""
from __future__ import annotations

import hashlib
import math
import os
import random
import re
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from xml.etree import ElementTree as ET

from .core import Configuration, Coordinate, MotionProfile, RouteStepper, closed, route_length

MAX_POINTS = 1000
MAX_INTERVAL = 3600
_configured_hdc: str | None = None


def configure_hdc(path: str | None = None) -> str | None:
    """Find hdc in common HarmonyOS SDK installs and add its folder to this process PATH."""
    global _configured_hdc
    candidates: list[Path] = []
    if path:
        candidates.append(Path(path))
    if found := shutil.which("hdc"):
        candidates.append(Path(found))
    for key in ("DEVECO_STUDIO_HOME", "HARMONYOS_SDK_HOME", "OHOS_SDK_HOME"):
        if value := os.environ.get(key):
            base = Path(value)
            candidates.extend((base / "sdk/default/HarmonyOS/toolchains/hdc.exe",
                               base / "sdk/default/openharmony/toolchains/hdc.exe",
                               base / "sdk/default/toolchains/hdc.exe",
                               base / "toolchains/hdc.exe"))
    for base in (Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Huawei",
                 Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "Huawei",
                 Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "DevEco Studio"):
        if base.exists():
            candidates.extend(base.glob("**/sdk/default/HarmonyOS/toolchains/hdc.exe"))
            candidates.extend(base.glob("**/sdk/default/openharmony/toolchains/hdc.exe"))
    for candidate in candidates:
        executable = candidate if candidate.is_file() else candidate / "hdc.exe"
        if executable.is_file():
            _configured_hdc = str(executable.resolve())
            os.environ["PATH"] = str(executable.parent) + os.pathsep + os.environ.get("PATH", "")
            return _configured_hdc
    return None


def _hdc() -> str:
    executable = _configured_hdc or shutil.which("hdc") or configure_hdc()
    if not executable:
        raise RuntimeError("未找到 hdc。请安装 DevEco Studio，并将 HarmonyOS SDK 的 toolchains 目录加入 PATH。")
    return executable


def _run(args: list[str], timeout: float = 25) -> str:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                                encoding="utf-8", errors="replace",
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("HarmonyOS 设备命令超时，请检查 hdc 连接。") from exc
    except OSError as exc:
        raise RuntimeError("无法启动 hdc：" + str(exc)) from exc
    output = (result.stdout + "\n" + result.stderr).strip()
    if result.returncode != 0 or re.search(r"\[Fail\]|\bError:|inaccessible or not found|Unknown operation", output, re.I):
        raise RuntimeError("HarmonyOS 设备命令失败：" + (output or f"退出码 {result.returncode}"))
    return output


def connected_devices() -> list[str]:
    output = _run([_hdc(), "list", "targets"], timeout=15)
    return [key for line in output.splitlines() if (key := line.strip())
            and re.fullmatch(r"[^\s\[\]]+", key) and key.casefold() != "unauthorized"]


def gpx(points: list[Coordinate]) -> bytes:
    if not 1 <= len(points) <= MAX_POINTS:
        raise ValueError("HarmonyOS GPX 路线须包含 1～1000 个位置点。")
    root = ET.Element("gpx", {"version": "1.1", "creator": "WinLS",
                              "xmlns": "http://www.topografix.com/GPX/1/1"})
    if len(points) == 1:
        ET.SubElement(root, "wpt", lat=f"{points[0].latitude:.8f}", lon=f"{points[0].longitude:.8f}")
    else:
        segment = ET.SubElement(ET.SubElement(root, "trk"), "trkseg")
        for point in points:
            ET.SubElement(segment, "trkpt", lat=f"{point.latitude:.8f}", lon=f"{point.longitude:.8f}")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def route_samples(config: Configuration) -> tuple[list[Coordinate], int]:
    """Precompute a route at testhelper's integer-second interval and 1000-point limit."""
    config.validate()
    path = closed(config.route)
    if len(path) < 2 or route_length(path) < .001:
        raise ValueError("HarmonyOS 路线至少需要两个不同的坐标点。")
    estimated = route_length(path) * config.passes / config.speedMetersPerSecond
    interval = max(1, math.ceil(estimated / (MAX_POINTS - 2)))
    if interval > MAX_INTERVAL:
        raise ValueError("路线时长超过 HarmonyOS testhelper 的 1000 点、3600 秒间隔上限。")
    seed = random.getrandbits(64)
    for _ in range(16):
        motion = MotionProfile(config.speedMetersPerSecond, config.dynamicSpeed,
                               config.dynamicSpeedPlan, seed)
        rng = random.Random(seed)
        offset = 0.0
        samples = [path[0]]
        for lap in range(config.passes):
            stepper = RouteStepper(path, config.pathVariationMeters, seed + lap)
            while not stepper.finished and len(samples) <= MAX_POINTS:
                offset = .8 * offset + .2 * rng.uniform(-config.jitterPercent / 100,
                                                         config.jitterPercent / 100)
                meters = motion.advance(interval, 1 + offset)
                samples.append(stepper.advance(meters))
            if len(samples) > MAX_POINTS:
                break
        if len(samples) <= MAX_POINTS:
            return samples, interval
        interval = max(interval + 1, math.ceil(interval * 1.5))
        if interval > MAX_INTERVAL:
            break
    raise ValueError("路线无法压缩到 HarmonyOS testhelper 支持的 1000 个位置点。")


class HarmonyBridge:
    def __init__(self):
        self._active: set[str] = set()
        self._lock = threading.RLock()

    @staticmethod
    def _target(serial: str) -> list[str]:
        return [_hdc(), "-t", serial]

    def _send_points(self, serial: str, points: list[Coordinate], interval: int):
        if not 1 <= interval <= MAX_INTERVAL:
            raise ValueError("HarmonyOS 位置更新间隔须为 1～3600 秒。")
        local_path = None
        remote = "/data/local/tmp/winls-" + hashlib.sha256(serial.encode()).hexdigest()[:12] + ".gpx"
        with self._lock:
            try:
                with tempfile.NamedTemporaryFile(suffix=".gpx", delete=False) as file:
                    local_path = Path(file.name)
                    file.write(gpx(points))
                target = self._target(serial)
                if serial not in self._active:
                    output = _run(target + ["shell", "testhelper", "enable-location-mock"])
                    if "successfully" not in output.lower():
                        raise RuntimeError("设备未确认启用模拟定位：" + output)
                    self._active.add(serial)
                _run(target + ["file", "send", str(local_path), remote], timeout=30)
                output = _run(target + ["shell", "testhelper", "set-mocked-locations", remote,
                                        str(interval)], timeout=30)
                if "successfully" not in output.lower():
                    raise RuntimeError("设备未确认模拟定位生效：" + output)
            finally:
                if local_path is not None:
                    local_path.unlink(missing_ok=True)

    def set(self, serial: str, point: Coordinate):
        self._send_points(serial, [point], 1)

    def clear(self, serial: str):
        with self._lock:
            output = _run(self._target(serial) + ["shell", "testhelper", "disable-location-mock"])
            if "successfully" not in output.lower():
                raise RuntimeError("设备未确认清除模拟定位：" + output)
            self._active.discard(serial)

    def replay(self, serial: str, config: Configuration, stop_event: threading.Event,
               status, preview):
        samples, interval = route_samples(config)
        preview((closed(config.route), 42))
        if stop_event.is_set():
            status("路径模拟已停止。")
            return
        status(f"正在向 HarmonyOS 设备发送 {len(samples)} 个位置点，更新间隔 {interval} 秒…")
        self._send_points(serial, samples, interval)
        started = time.monotonic()
        duration = interval * (len(samples) - 1)
        status("HarmonyOS 正在回放路线。")
        while not stop_event.is_set():
            remaining = duration - (time.monotonic() - started)
            if remaining <= 0:
                break
            stop_event.wait(min(1, remaining))
        index = min(len(samples) - 1, max(0, int((time.monotonic() - started) / interval)))
        self.set(serial, samples[index] if stop_event.is_set() else samples[-1])
        status("路径模拟已停止，定位停留在当前点。" if stop_event.is_set()
               else "路径模拟完成，定位停留在最后一个点。")

    def close(self):
        with self._lock:
            active = list(self._active)
        for serial in active:
            try:
                self.clear(serial)
            except RuntimeError:
                pass
