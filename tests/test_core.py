import unittest

from winloc.core import (Configuration, Coordinate, DynamicPlan, MotionProfile,
                         RouteStepper, closed, generate_track, pace_to_speed,
                         parse_points, route_length)


class CoreTests(unittest.TestCase):
    def test_config_compatible_with_mac(self):
        original = Configuration(
            name="校园", point=Coordinate(40.15608, 116.28333),
            route=[Coordinate(40.15608, 116.28333), Coordinate(40.157, 116.284)],
            dynamicSpeed=True, dynamicSpeedPlan=DynamicPlan("custom", "campus", .8, 600, 25))
        restored = Configuration.from_json(original.to_json())
        self.assertEqual(restored, original)
        self.assertNotIn("device", original.to_json())
        legacy = original.to_json().replace('  "pathVariationMeters": 2.0,\n', '')
        self.assertEqual(Configuration.from_json(legacy).pathVariationMeters, 2)

    def test_closed_route_drift_and_endpoint(self):
        a, b = Coordinate(39.9, 116.4), Coordinate(39.901, 116.401)
        path = closed([a, b])
        self.assertEqual(path[-1], a)
        stepper = RouteStepper(path, 2, 42)
        mid = stepper.advance(route_length(path) / 4)
        self.assertLess(mid.distance(a), route_length(path))
        self.assertEqual(stepper.advance(route_length(path)), a)

    def test_track_length_and_validation(self):
        a, b = Coordinate(39.9, 116.4), Coordinate(39.9, 116.401)
        track = generate_track(a, b, "right")
        self.assertEqual(track[0], track[-1])
        self.assertAlmostEqual(route_length(track), 400, delta=1)
        with self.assertRaises(ValueError):
            generate_track(a, a, "right")
        with self.assertRaises(ValueError):
            generate_track(a, Coordinate(39.9, 116.403), "right")

    def test_pace_dynamic_and_parser(self):
        self.assertAlmostEqual(pace_to_speed(3, 20), 5)
        with self.assertRaises(ValueError):
            parse_points("39.9,116.4\nwrong")
        motion = MotionProfile(5, True, DynamicPlan("custom", "campus", .1, 600, 5), 42)
        self.assertAlmostEqual(motion.advance(20), 100)
        self.assertGreater(motion.recovery_left, 0)
        self.assertAlmostEqual(motion.advance(2), 1000 / 600 * 2)


if __name__ == "__main__":
    unittest.main()

