"""iOS 17+ developer location bridge through pymobiledevice3 USB RSD."""
from __future__ import annotations

import json
import queue
import subprocess
import sys
import threading
from pathlib import Path

from .core import Coordinate

BRIDGE = Path(__file__).with_name("iphone_bridge.py")


def connected_devices() -> list[str]:
    try:
        command = ([sys.executable, "--list-devices"] if getattr(sys, "frozen", False)
                   else [sys.executable, "-m", "pymobiledevice3", "usbmux", "list", "--simple", "--usb"])
        result = subprocess.run(
            command,
            capture_output=True, text=True, timeout=15, check=True,
        )
        devices = json.loads(result.stdout)
        if not isinstance(devices, list) or not all(isinstance(d, str) for d in devices):
            raise ValueError("设备列表格式无效。")
        return devices
    except FileNotFoundError as exc:
        raise RuntimeError("未找到 Python。请重新安装程序。") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip()
        raise RuntimeError(f"无法读取 iPhone：{detail or '请安装 Apple Mobile Device Support、解锁并信任电脑。'}") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("读取 iPhone 超时，请检查 USB 连接。") from exc


class PhoneSession:
    def __init__(self):
        self._lock = threading.RLock()
        self._process: subprocess.Popen | None = None
        self._udid: str | None = None

    def _read(self, timeout: float = 30) -> dict:
        process = self._process
        if process is None or process.stdout is None:
            raise RuntimeError("iPhone 定位会话未启动。")
        responses: queue.Queue[str] = queue.Queue(maxsize=1)
        threading.Thread(target=lambda: responses.put(process.stdout.readline()), daemon=True).start()
        try:
            line = responses.get(timeout=timeout)
        except queue.Empty as exc:
            self._disconnect()
            raise RuntimeError("iPhone 定位服务响应超时。") from exc
        if not line:
            self._disconnect()
            raise RuntimeError("iPhone 定位服务意外退出。请检查开发者模式和 USB 连接。")
        try:
            return json.loads(line)
        except json.JSONDecodeError as exc:
            self._disconnect()
            raise RuntimeError("iPhone 定位服务返回无效数据。") from exc

    def _connect(self, udid: str):
        if self._process is not None and self._process.poll() is None and self._udid == udid:
            return
        if self._process is not None:
            self._disconnect()
        command = ([sys.executable, "--iphone-bridge", udid] if getattr(sys, "frozen", False)
                   else [sys.executable, "-u", str(BRIDGE), udid])
        self._process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, encoding="utf-8", bufsize=1,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        self._udid = udid
        response = self._read(timeout=60)
        if response.get("ready") is not True:
            self._disconnect()
            raise RuntimeError("无法连接 iPhone 开发者定位服务：" + str(response.get("error", "未知错误")))

    def _send(self, request: dict):
        process = self._process
        if process is None or process.stdin is None:
            raise RuntimeError("iPhone 定位会话已断开。")
        try:
            process.stdin.write(json.dumps(request, allow_nan=False) + "\n")
            process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            self._disconnect()
            raise RuntimeError("iPhone 定位会话已断开。") from exc
        response = self._read()
        if response.get("ok") is not True:
            raise RuntimeError(str(response.get("error", "iPhone 定位操作失败。")))

    def set(self, udid: str, point: Coordinate):
        with self._lock:
            self._connect(udid)
            self._send({"action": "set", "latitude": point.latitude, "longitude": point.longitude})

    def clear(self, udid: str):
        with self._lock:
            self._connect(udid)
            try:
                self._send({"action": "clear"})
            finally:
                self._disconnect()

    def close(self):
        with self._lock:
            if self._process is not None and self._process.poll() is None:
                try:
                    self._send({"action": "clear"})
                except Exception:
                    pass
            self._disconnect()

    def _disconnect(self):
        process = self._process
        self._process = None
        self._udid = None
        if process is not None:
            try:
                process.terminate()
                process.wait(timeout=3)
            except (OSError, subprocess.TimeoutExpired):
                process.kill()
                process.wait(timeout=3)
            finally:
                for pipe in (process.stdin, process.stdout):
                    if pipe:
                        pipe.close()
