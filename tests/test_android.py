import subprocess
import unittest
from unittest.mock import patch

from winloc.android import AndroidBridge, connected_devices, RECEIVER, ACTION
from winloc.core import Coordinate


class AndroidBridgeTests(unittest.TestCase):
    @patch("winloc.android.shutil.which", return_value="adb")
    @patch("winloc.android.subprocess.run")
    def test_discovery_excludes_unauthorized(self, run, _which):
        run.return_value = subprocess.CompletedProcess([], 0,
            "List of devices attached\nABC123 device product:x\nOFFLINE offline\nNOPE unauthorized\n", "")
        self.assertEqual(connected_devices(), ["ABC123"])
        self.assertEqual(run.call_args.args[0], ["adb", "devices", "-l"])

    @patch("winloc.android.shutil.which", return_value="adb")
    @patch("winloc.android.subprocess.run")
    def test_set_and_clear_require_receiver_success(self, run, _which):
        run.return_value = subprocess.CompletedProcess([], 0,
            'Broadcasting: Intent {...}\nBroadcast completed: result=200, data="OK"\n', "")
        bridge = AndroidBridge()
        bridge.set("ABC123", Coordinate(39.9042, 116.4074))
        args = run.call_args.args[0]
        self.assertEqual(args[:5], ["adb", "-s", "ABC123", "shell", "am"])
        self.assertIn(RECEIVER, args)
        self.assertIn(ACTION, args)
        self.assertIn("39.90420000", args)
        self.assertIn("116.40740000", args)
        bridge.clear("ABC123")
        self.assertIn("clear", run.call_args.args[0])

    @patch("winloc.android.shutil.which", return_value="adb")
    @patch("winloc.android.subprocess.run")
    def test_missing_companion_is_not_reported_as_success(self, run, _which):
        run.return_value = subprocess.CompletedProcess([], 0, "Broadcast completed: result=0\n", "")
        with self.assertRaisesRegex(RuntimeError, "Android 定位失败"):
            AndroidBridge().set("ABC123", Coordinate(0, 0))

    @patch("winloc.android.shutil.which", return_value="adb")
    @patch("winloc.android.subprocess.run")
    def test_close_clears_active_device(self, run, _which):
        run.return_value = subprocess.CompletedProcess([], 0, "Broadcast completed: result=200\n", "")
        bridge = AndroidBridge()
        bridge.set("ABC123", Coordinate(0, 0))
        bridge.close()
        self.assertIn("clear", run.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
