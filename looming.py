"""Controlled virtual looming stimulus for reproducible biological trials."""

from __future__ import annotations

import math
from dataclasses import dataclass

from vision import ThreatSignal


LC4_REFERENCE_VELOCITY_DEG_S = 500.0
LPLC2_PREFERRED_SIZE_DEG = 60.0
LPLC2_SIZE_WIDTH_DEG = 20.0


@dataclass(frozen=True)
class LoomSample:
    signal: ThreatSignal
    running: bool
    completed: bool
    distance_mm: float
    angular_size_deg: float
    angular_velocity_deg_s: float
    time_to_collision_s: float
    progress: float


class LoomingTrial:
    """A circular object approaching the fly at a constant virtual speed."""

    SPEEDS_MM_S = {"slow": 200.0, "fast": 500.0}

    def __init__(
        self,
        object_radius_mm: float = 20.0,
        start_distance_mm: float = 250.0,
        minimum_distance_mm: float = 3.0,
    ) -> None:
        self.object_radius_mm = object_radius_mm
        self.start_distance_mm = start_distance_mm
        self.minimum_distance_mm = minimum_distance_mm
        self.speed_name = "fast"
        self.side = "right"
        self.running = False
        self.completed = False
        self.distance_mm = start_distance_mm

    @property
    def speed_mm_s(self) -> float:
        return self.SPEEDS_MM_S[self.speed_name]

    @property
    def side_sign(self) -> float:
        return -1.0 if self.side == "left" else 1.0

    @property
    def l_over_v_ms(self) -> float:
        return 1000.0 * self.object_radius_mm / self.speed_mm_s

    def configure(self, side: str | None = None, speed_name: str | None = None) -> None:
        if side is not None:
            if side not in {"left", "right"}:
                raise ValueError(f"Unknown loom side: {side}")
            self.side = side
        if speed_name is not None:
            if speed_name not in self.SPEEDS_MM_S:
                raise ValueError(f"Unknown loom speed: {speed_name}")
            self.speed_name = speed_name

    def start(self) -> LoomSample:
        self.distance_mm = self.start_distance_mm
        self.running = True
        self.completed = False
        return self.sample()

    def reset(self) -> LoomSample:
        self.distance_mm = self.start_distance_mm
        self.running = False
        self.completed = False
        return self.sample()

    def update(self, dt: float) -> LoomSample:
        if self.running:
            self.distance_mm = max(
                self.minimum_distance_mm,
                self.distance_mm - self.speed_mm_s * max(dt, 0.0),
            )
            if self.distance_mm <= self.minimum_distance_mm:
                self.running = False
                self.completed = True
        return self.sample()

    def sample(self) -> LoomSample:
        distance = self.distance_mm
        angle_rad = 2.0 * math.atan(self.object_radius_mm / distance)
        angular_size_deg = math.degrees(angle_rad)
        angular_velocity_rad_s = (
            2.0
            * self.object_radius_mm
            * self.speed_mm_s
            / (distance * distance + self.object_radius_mm * self.object_radius_mm)
        )
        angular_velocity_deg_s = math.degrees(angular_velocity_rad_s)
        time_to_collision_s = max(0.0, distance / self.speed_mm_s)

        if self.running:
            lc4_response = min(
                1.0, angular_velocity_deg_s / LC4_REFERENCE_VELOCITY_DEG_S
            )
            size_offset = (
                angular_size_deg - LPLC2_PREFERRED_SIZE_DEG
            ) / LPLC2_SIZE_WIDTH_DEG
            lplc2_response = math.exp(-0.5 * size_offset * size_offset)
        else:
            lc4_response = 0.0
            lplc2_response = 0.0

        progress = 1.0 - (
            (distance - self.minimum_distance_mm)
            / (self.start_distance_mm - self.minimum_distance_mm)
        )
        progress = max(0.0, min(1.0, progress))
        signal = ThreatSignal(
            strength=max(lc4_response, lplc2_response),
            distance=distance,
            approach_speed=self.speed_mm_s if self.running else 0.0,
            direction_x=self.side_sign,
            direction_y=0.0,
            angular_size=lplc2_response,
            expansion_velocity=lc4_response,
            angular_size_degrees=angular_size_deg,
            angular_velocity_deg_s=angular_velocity_deg_s,
            time_to_collision_s=time_to_collision_s,
        )
        return LoomSample(
            signal=signal,
            running=self.running,
            completed=self.completed,
            distance_mm=distance,
            angular_size_deg=angular_size_deg,
            angular_velocity_deg_s=angular_velocity_deg_s,
            time_to_collision_s=time_to_collision_s,
            progress=progress,
        )
