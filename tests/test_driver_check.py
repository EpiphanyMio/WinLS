import subprocess
import sys
import types
import unittest
from unittest.mock import patch

from winloc.driver_check import DriverReport, probe


class DriverCheckTests(unittest.TestCase):
    def test_aisi_installation_does_not_hide_missing_apple_components(self):
        report = DriverReport(windows=True, apple_usb_connected=True,
                              mobile_service_installed=False, usb_driver_installed=False,
                              aisi_installed=True)
        self.assertIn("Apple Mobile Device Service", report.missing)
        self.assertIn("Apple Mobile Device USB Driver", report.missing)
        self.assertIn("爱思助手", report.guide_html())
        self.assertIn("apps.microsoft.com", report.guide_html())
        self.assertIn("support.apple.com", report.guide_html())

    def test_stopped_service_has_specific_repair_step(self):
        report = DriverReport(windows=True, mobile_service_installed=True,
                              mobile_service_running=False, usb_driver_installed=True)
        self.assertIn("未运行", report.summary())
        self.assertIn("services.msc", report.guide_html())

    def test_no_apple_usb_does_not_claim_iphone_is_connected(self):
        report = DriverReport(windows=True, apple_usb_connected=False,
                              mobile_service_installed=True, mobile_service_running=True,
                              usb_driver_installed=True)
        self.assertFalse(report.apple_usb_connected)
        self.assertEqual(report.missing, ())

    def test_probe_uses_service_state_and_registered_inf(self):
        def result(args):
            if args[0] == "sc.exe":
                return subprocess.CompletedProcess(args, 0, "STATE : 4 RUNNING", "")
            if "/enum-drivers" in args:
                return subprocess.CompletedProcess(args, 0, "Original Name: usbaapl64.inf", "")
            return subprocess.CompletedProcess(args, 0, "USB\\VID_05AC&PID_12A8", "")

        with (patch("winloc.driver_check.sys.platform", "win32"),
              patch.dict(sys.modules, {"winreg": types.SimpleNamespace()}),
              patch("winloc.driver_check._registry_key_exists", side_effect=[True, False, False, False]),
              patch("winloc.driver_check._detect_aisi", return_value=True),
              patch("winloc.driver_check._run", side_effect=result)):
            report = probe()
        self.assertTrue(report.apple_usb_connected)
        self.assertTrue(report.mobile_service_running)
        self.assertTrue(report.usb_driver_installed)
        self.assertTrue(report.aisi_installed)


if __name__ == "__main__":
    unittest.main()
