"""Read-only Windows checks for iPhone USB support and repair guidance."""
from __future__ import annotations

from dataclasses import dataclass
import re
import subprocess
import sys

APPLE_HELP_URL = "https://support.apple.com/en-us/108643"
APPLE_DEVICES_URL = "https://apps.microsoft.com/detail/9np83lwlpz9k"
APPLE_ITUNES_URL = "https://www.apple.com/itunes/"


@dataclass(frozen=True)
class DriverReport:
    windows: bool
    apple_usb_connected: bool | None = None
    mobile_service_installed: bool | None = None
    mobile_service_running: bool | None = None
    usb_driver_installed: bool | None = None
    aisi_installed: bool | None = None

    @property
    def missing(self) -> tuple[str, ...]:
        if not self.windows:
            return ()
        missing = []
        if self.mobile_service_installed is False:
            missing.append("Apple Mobile Device Service")
        elif self.mobile_service_running is False:
            missing.append("Apple Mobile Device Service 未运行")
        if self.usb_driver_installed is False:
            missing.append("Apple Mobile Device USB Driver")
        return tuple(missing)

    def summary(self) -> str:
        if not self.windows:
            return "iOS 驱动检测仅适用于 Windows。"
        if self.missing:
            return "iOS 驱动诊断：" + "、".join(self.missing) + " 未就绪。"
        if (self.mobile_service_installed is None or self.mobile_service_running is None
                or self.usb_driver_installed is None):
            return "iOS 驱动诊断：部分组件无法确认，请按指南检查。"
        return "iOS 驱动已检测到；若仍找不到 iPhone，请检查 USB、信任状态和开发者模式。"

    def guide_html(self) -> str:
        if not self.windows:
            return self.summary()
        lines = ["<b>iOS 连接诊断</b><br>" + self.summary()]
        if self.aisi_installed:
            lines.append("检测到爱思助手。它可能已安装 Apple 驱动，但请以服务和 USB 驱动检测结果为准；"
                         "若组件缺失，可先使用爱思助手内的驱动修复功能。")
        else:
            lines.append("未检测到爱思助手；无需专门安装它。")
        if self.mobile_service_running is False:
            lines.append("服务已安装但未运行：打开 Windows“服务”（services.msc），找到 Apple Mobile Device Service，尝试启动或重新启动。")
        if self.missing or self.mobile_service_installed is None or self.usb_driver_installed is None:
            lines.append(f'下载/修复：安装或更新 <a href="{APPLE_DEVICES_URL}">Apple Devices（微软商店）</a>；'
                         f'也可从 <a href="{APPLE_ITUNES_URL}">Apple 官网</a>安装 iTunes。安装后重启电脑并重新连接 iPhone。')
        lines.append(f'连接排查：解锁手机并选择“信任此电脑”；使用可传输数据的 USB 线；'
                     f'参考 <a href="{APPLE_HELP_URL}">Apple 官方识别设备指南</a>。')
        return "<br>".join(lines)


def _run(args: list[str]) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=10,
                              encoding="utf-8", errors="replace",
                              creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.TimeoutExpired):
        return None


def _registry_key_exists(winreg, path: str) -> bool | None:
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path):
            return True
    except FileNotFoundError:
        return False
    except OSError:
        return None


def _detect_aisi(winreg) -> bool | None:
    prefixes = (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall")
    readable = False
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for prefix in prefixes:
            try:
                with winreg.OpenKey(hive, prefix) as uninstall:
                    readable = True
                    index = 0
                    while True:
                        try:
                            subkey = winreg.EnumKey(uninstall, index)
                        except OSError:
                            break
                        index += 1
                        try:
                            with winreg.OpenKey(uninstall, subkey) as app:
                                name = str(winreg.QueryValueEx(app, "DisplayName")[0]).casefold()
                                if "爱思助手" in name or "i4tools" in name:
                                    return True
                        except OSError:
                            continue
            except OSError:
                continue
    return False if readable else None


def probe() -> DriverReport:
    if sys.platform != "win32":
        return DriverReport(windows=False)
    import winreg

    service = _registry_key_exists(winreg, r"SYSTEM\CurrentControlSet\Services\Apple Mobile Device Service")
    running = None
    if service:
        response = _run(["sc.exe", "query", "Apple Mobile Device Service"])
        if response and response.returncode == 0:
            # The state number is stable across localized Windows installations.
            match = re.search(r":\s*([1-7])\s+(?:\S+)", response.stdout)
            if match:
                running = match.group(1) == "4"

    driver_keys = (r"SYSTEM\CurrentControlSet\Services\usbaapl64",
                   r"SYSTEM\CurrentControlSet\Services\usbaapl",
                   r"SYSTEM\CurrentControlSet\Services\AppleMobileDeviceUSBDriver")
    key_results = [_registry_key_exists(winreg, key) for key in driver_keys]
    driver = True if True in key_results else None if None in key_results else False
    if driver is False:
        response = _run(["pnputil.exe", "/enum-drivers"])
        if response and response.returncode == 0:
            driver = bool(re.search(r"usbaapl(?:64)?\.inf", response.stdout, re.IGNORECASE))
        else:
            driver = None

    apple_usb = None
    response = _run(["pnputil.exe", "/enum-devices", "/connected"])
    if response and response.returncode == 0:
        apple_usb = bool(re.search(r"USB\\VID_05AC", response.stdout, re.IGNORECASE))

    return DriverReport(windows=True, apple_usb_connected=apple_usb,
                        mobile_service_installed=service, mobile_service_running=running,
                        usb_driver_installed=driver, aisi_installed=_detect_aisi(winreg))
