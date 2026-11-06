import subprocess
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

from winloc.core import Configuration, Coordinate
from winloc.harmony import HarmonyBridge, _run, connected_devices, gpx, route_samples


class HarmonyTests(unittest.TestCase):
    def test_gpx_and_sample_limit(self):
        one = ET.fromstring(gpx([Coordinate(39.9, 116.4)]))
        self.assertEqual(one.find("{*}wpt").attrib["lat"], "39.90000000")
        route = ET.fromstring(gpx([Coordinate(0, 0), Coordinate(0, .001)]))
        self.assertEqual(len(route.findall(".//{*}trkpt")), 2)
        with self.assertRaises(ValueError):
            gpx([Coordinate(0, 0)] * 1001)

    @patch("winloc.harmony.random.getrandbits", return_value=42)
    def test_route_resamples_within_testhelper_limit(self, _seed):
        config = Configuration(route=[Coordinate(0, 0), Coordinate(0, .01)],
                               speedMetersPerSecond=5, passes=10)
        samples, interval = route_samples(config)
        self.assertLessEqual(len(samples), 1000)
        self.assertGreaterEqual(interval, 1)
        self.assertEqual(samples[0], samples[-1])

    @patch("winloc.harmony._hdc", return_value="hdc")
    @patch("winloc.harmony._run", return_value="key1\nkey2\n[Empty]\nDevice ID Unauthorized\n")
    def test_device_discovery(self, run, _hdc):
        self.assertEqual(connected_devices(), ["key1", "key2"])
        run.assert_called_once_with(["hdc", "list", "targets"], timeout=15)

    @patch("winloc.harmony._hdc", return_value="hdc")
    @patch("winloc.harmony._run")
    def test_set_and_clear_commands(self, run, _hdc):
        def answer(args, timeout=25):
            if "enable-location-mock" in args:
                return "Enable location mock successfully."
            if "set-mocked-locations" in args:
                return "Set mocked locations successfully."
            if "disable-location-mock" in args:
                return "Disable location mock successfully."
            return "FileTransfer finish"
        run.side_effect = answer
        bridge = HarmonyBridge()
        bridge.set("serial1", Coordinate(39.9, 116.4))
        commands = [call.args[0] for call in run.call_args_list]
        self.assertTrue(any("enable-location-mock" in cmd for cmd in commands))
        self.assertTrue(any("set-mocked-locations" in cmd for cmd in commands))
        self.assertTrue(any("file" in cmd and "send" in cmd for cmd in commands))
        bridge.clear("serial1")
        self.assertIn("disable-location-mock", run.call_args.args[0])

    @patch("winloc.harmony.subprocess.run")
    def test_hdc_errors_are_not_silently_accepted(self, run):
        run.return_value = subprocess.CompletedProcess([], 0,
            "Error: Operation is not supported. Location mock is not supported on this device.", "")
        with self.assertRaisesRegex(RuntimeError, "not supported"):
            _run(["hdc", "shell", "testhelper", "enable-location-mock"])


if __name__ == "__main__":
    unittest.main()
