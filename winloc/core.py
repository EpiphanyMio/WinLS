"""Platform independent route, pace and Mac-compatible configuration logic."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import math
import random

EARTH = 6_371_000.0


@dataclass(frozen=True)
class Coordinate:
    latitude: float
    longitude: float

    def __post_init__(self):
        if not (math.isfinite(self.latitude) and -90 <= self.latitude <= 90
                and math.isfinite(self.longitude) and -180 <= self.longitude <= 180):
            raise ValueError("纬度须在 -90～90，经度须在 -180～180。")

    def distance(self, other: Coordinate) -> float:
        lat1, lat2 = math.radians(self.latitude), math.radians(other.latitude)
        dlat, dlon = lat2 - lat1, math.radians(other.longitude - self.longitude)
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return 2 * EARTH * math.asin(min(1, math.sqrt(a)))

    def interpolate(self, other: Coordinate, fraction: float) -> Coordinate:
        t = min(1, max(0, fraction))
        delta = (other.longitude - self.longitude + 180) % 360 - 180
        longitude = (self.longitude + delta * t + 180) % 360 - 180
        return Coordinate(self.latitude + (other.latitude - self.latitude) * t, longitude)

    def offset(self, east: float, north: float) -> Coordinate:
        if abs(self.latitude) >= 89.9:
            return self
        latitude = self.latitude + math.degrees(north / EARTH)
        if abs(latitude) >= 90:
            return self
        longitude = (self.longitude + math.degrees(east / (EARTH * math.cos(math.radians(latitude)))) + 180) % 360 - 180
        return Coordinate(latitude, longitude)


def parse_points(text: str) -> list[Coordinate]:
    points = []
    for number, raw in enumerate(text.splitlines(), 1):
        if not raw.strip():
            continue
        try:
            lat, lon = raw.split(",")
            points.append(Coordinate(float(lat), float(lon)))
        except (ValueError, TypeError) as exc:
            raise ValueError(f"第 {number} 行格式有误。每行输入：纬度,经度") from exc
    if len(points) < 2:
        raise ValueError("路径至少需要两个坐标点。")
    if len(points) > 10_000:
        raise ValueError("路径最多支持 10000 个点。")
    return points


def closed(points: list[Coordinate]) -> list[Coordinate]:
    return points + [points[0]] if len(points) >= 2 and points[0] != points[-1] else points[:]


def route_length(points: list[Coordinate]) -> float:
    return sum(a.distance(b) for a, b in zip(points, points[1:]))


def pace_to_speed(minutes: int, seconds: int) -> float:
    if minutes < 0 or not 0 <= seconds <= 59 or minutes * 60 + seconds <= 0:
        raise ValueError("配速格式有误。")
    return 1000 / (minutes * 60 + seconds)


def speed_to_pace(speed: float) -> tuple[int, int]:
    if not math.isfinite(speed) or speed <= 0:
        raise ValueError("速度须大于 0。")
    total = max(1, round(1000 / speed))
    return divmod(total, 60)


@dataclass
class DynamicPlan:
    mode: str = "automatic"
    preset: str = "campus"
    intervalKilometers: float = 0.8
    lowPaceSeconds: int = 600
    recoverySeconds: float = 25

    def validate(self, speed: float):
        if self.mode not in ("automatic", "custom") or self.preset not in ("campus", "easy", "endurance"):
            raise ValueError("动态速度方案无效。")
        if self.mode == "custom" and not (
            math.isfinite(self.intervalKilometers) and 0.1 <= self.intervalKilometers <= 20
            and 60 <= self.lowPaceSeconds <= 3600 and self.lowPaceSeconds > 1000 / speed
            and math.isfinite(self.recoverySeconds) and 5 <= self.recoverySeconds <= 300
        ):
            raise ValueError("自定义动态速度：间隔须为 0.1～20 公里，低速配速需慢于跑步配速，持续 5～300 秒。")


@dataclass
class Configuration:
    name: str = "我的路线"
    point: Coordinate = Coordinate(39.9042, 116.4074)
    route: list[Coordinate] = field(default_factory=list)
    speedMetersPerSecond: float = 5.0
    jitterPercent: float = 15.0
    passes: int = 2
    pathVariationMeters: float = 2.0
    dynamicSpeed: bool = False
    dynamicSpeedPlan: DynamicPlan = field(default_factory=DynamicPlan)
    schemaVersion: int = 1

    def validate(self):
        if self.schemaVersion != 1:
            raise ValueError("不支持此配置文件版本。")
        if not self.name.strip():
            raise ValueError("请填写配置名称。")
        if len(self.route) > 10_000:
            raise ValueError("路径最多支持 10000 个点。")
        if not (math.isfinite(self.speedMetersPerSecond) and self.speedMetersPerSecond > 0
                and math.isfinite(self.jitterPercent) and 0 <= self.jitterPercent <= 100
                and type(self.passes) is int and 1 <= self.passes <= 1000
                and math.isfinite(self.pathVariationMeters) and 0 <= self.pathVariationMeters <= 20):
            raise ValueError("速度、抖动、圈数或路线偏移参数无效。")
        if self.dynamicSpeed:
            self.dynamicSpeedPlan.validate(self.speedMetersPerSecond)

    def to_json(self) -> str:
        self.validate()
        return json.dumps(asdict(self), ensure_ascii=False, indent=2, allow_nan=False)

    @classmethod
    def from_json(cls, text: str) -> Configuration:
        raw = json.loads(text)
        if not isinstance(raw, dict):
            raise ValueError("配置须是 JSON 对象。")
        data = {key: raw[key] for key in ("schemaVersion", "name", "point", "route",
                "speedMetersPerSecond", "jitterPercent", "passes")}
        data["point"] = Coordinate(**data["point"])
        data["route"] = [Coordinate(**point) for point in data["route"]]
        data["pathVariationMeters"] = raw.get("pathVariationMeters", 2)
        data["dynamicSpeed"] = raw.get("dynamicSpeed", False)
        data["dynamicSpeedPlan"] = DynamicPlan(**raw.get("dynamicSpeedPlan", {}))
        config = cls(**data)
        config.validate()
        return config


def generate_track(start: Coordinate, end: Coordinate, side: str) -> list[Coordinate]:
    if side not in ("left", "right"):
        raise ValueError("跑道方向无效。")
    mid = start.interpolate(end, 0.5)
    if abs(mid.latitude) >= 85:
        raise ValueError("此位置无法生成跑道。")
    lat_scale = EARTH * math.pi / 180
    lon_scale = lat_scale * math.cos(math.radians(mid.latitude))
    dlon = (end.longitude - start.longitude + 180) % 360 - 180
    east, north = dlon * lon_scale, (end.latitude - start.latitude) * lat_scale
    straight = math.hypot(east, north)
    if not 20 <= straight < 200 or start.distance(end) >= 200:
        raise ValueError("两个端点应标出同一条长直边，相距 20～200 米（不含 200 米）。")
    ae, an = east / straight, north / straight
    ce, cn = (-an, ae) if side == "left" else (an, -ae)

    def coord(along: float, across: float) -> Coordinate:
        lat = start.latitude + (along * an + across * cn) / lat_scale
        lon = (start.longitude + (along * ae + across * ce) / lon_scale + 180) % 360 - 180
        return Coordinate(lat, lon)

    def path(radius: float) -> list[Coordinate]:
        points = [start, end]
        for index in range(1, 49):
            angle = -math.pi / 2 + math.pi * index / 48
            points.append(coord(straight + radius * math.cos(angle), radius + radius * math.sin(angle)))
        points.append(coord(0, 2 * radius))
        for index in range(1, 48):
            angle = math.pi / 2 + math.pi * index / 48
            points.append(coord(radius * math.cos(angle), radius + radius * math.sin(angle)))
        points.append(start)
        return points

    low, high = 0.0, 200.0
    for _ in range(30):
        radius = (low + high) / 2
        if route_length(path(radius)) < 400:
            low = radius
        else:
            high = radius
    return path((low + high) / 2)


class RouteStepper:
    def __init__(self, points: list[Coordinate], variation: float, seed: int):
        if len(points) < 2:
            raise ValueError("路径至少需要两个点。")
        self.points, self.variation, self.seed = points, variation, seed
        self.total = route_length(points)
        self.segment = 0
        self.into = 0.0
        self.travelled = 0.0
        rng = random.Random(seed)
        self.phases = [rng.random() * 2 * math.pi for _ in range(4)]
        self.wavelengths = [35 + rng.random() * 35, 12 + rng.random() * 18,
                            35 + rng.random() * 35, 12 + rng.random() * 18]

    @property
    def finished(self) -> bool:
        return self.segment >= len(self.points) - 1

    def advance(self, meters: float) -> Coordinate:
        remaining = max(0, meters)
        while not self.finished:
            a, b = self.points[self.segment:self.segment + 2]
            length = a.distance(b)
            if length < 0.001:
                self.segment += 1
                self.into = 0
                continue
            available = length - self.into
            if remaining < available:
                self.into += remaining
                self.travelled += remaining
                center = a.interpolate(b, self.into / length)
                return self._drift(center)
            remaining -= available
            self.travelled += available
            self.segment += 1
            self.into = 0
        return self.points[-1]

    def _drift(self, center: Coordinate) -> Coordinate:
        if self.variation <= 0 or self.total <= 0:
            return center
        d = self.travelled
        p, w = self.phases, self.wavelengths
        east = .7 * math.sin(2 * math.pi * d / w[0] + p[0]) + .3 * math.sin(2 * math.pi * d / w[1] + p[1])
        north = .7 * math.sin(2 * math.pi * d / w[2] + p[2]) + .3 * math.sin(2 * math.pi * d / w[3] + p[3])
        envelope = math.sin(math.pi * min(1, d / self.total)) ** 2
        limit = min(self.variation, self.total * .12) * envelope
        scale = limit / max(1, math.hypot(east, north))
        return center.offset(east * scale, north * scale)


class MotionProfile:
    RANGES = {"campus": ((600, 1000), (18, 35), (1.1, 1.4)),
              "easy": ((400, 700), (25, 40), (.9, 1.2)),
              "endurance": ((1200, 1800), (15, 25), (1.2, 1.5))}

    def __init__(self, speed: float, enabled: bool, plan: DynamicPlan, seed: int):
        self.speed, self.enabled, self.plan = speed, enabled, plan
        self.rng = random.Random(seed)
        self.running_meters = 0.0
        self.recovery_left = 0.0
        self.recovery_speed = 0.0
        self.next_recovery = self._interval()

    def _interval(self) -> float:
        if self.plan.mode == "custom":
            return self.plan.intervalKilometers * 1000
        return self.rng.uniform(*self.RANGES[self.plan.preset][0])

    def advance(self, seconds: float, multiplier: float = 1.0) -> float:
        if not self.enabled:
            return self.speed * multiplier * seconds
        distance = 0.0
        while seconds > 1e-6:
            if self.recovery_left > 0:
                duration = min(seconds, self.recovery_left)
                distance += self.recovery_speed * duration
                seconds -= duration
                self.recovery_left -= duration
                if self.recovery_left <= 1e-6:
                    self.recovery_left = 0
                    self.running_meters = 0
                    self.next_recovery = self._interval()
            else:
                speed = self.speed * multiplier
                duration = min(seconds, max(0, self.next_recovery - self.running_meters) / speed)
                distance += speed * duration
                self.running_meters += speed * duration
                seconds -= duration
                if self.running_meters >= self.next_recovery - 1e-6:
                    if self.plan.mode == "custom":
                        self.recovery_left = self.plan.recoverySeconds
                        self.recovery_speed = 1000 / self.plan.lowPaceSeconds
                    else:
                        _, duration_range, speed_range = self.RANGES[self.plan.preset]
                        self.recovery_left = self.rng.uniform(*duration_range)
                        self.recovery_speed = max(.25, min(self.speed * .55, self.rng.uniform(*speed_range)))
        return distance

