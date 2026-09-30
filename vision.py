"""Translate swatter motion into a simple visual-threat signal."""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot


DETECTION_RADIUS = 220.0
REFERENCE_SPEED = 650.0
ARRIVAL_RADIUS = 85.0


@dataclass(frozen=True)
class ThreatSignal:
    strength: float
    distance: float
    approach_speed: float
    direction_x: float
    direction_y: float
    angular_size: float = 0.0
    expansion_velocity: float = 0.0
    angular_size_degrees: float = 0.0
    angular_velocity_deg_s: float = 0.0
    time_to_collision_s: float = 0.0

    @property
    def is_dangerous(self) -> bool:
        return self.strength >= 0.35


def sense_swatter_arrival(
    fly_position: tuple[float, float],
    swatter_position: tuple[float, float],
    arrival_radius: float = ARRIVAL_RADIUS,
) -> ThreatSignal:
    """Create a standard visual pulse while the swatter is close to the fly.

    This behavior-test stimulus deliberately ignores approach speed. Distance
    is used only as collision-style input detection, not as a neural feature.
    """
    dx = swatter_position[0] - fly_position[0]
    dy = swatter_position[1] - fly_position[1]
    distance = hypot(dx, dy)
    arrived = distance <= arrival_radius

    if distance:
        direction_x, direction_y = dx / distance, dy / distance
    else:
        direction_x, direction_y = 0.0, 0.0

    pulse = 1.0 if arrived else 0.0
    return ThreatSignal(
        strength=pulse,
        distance=distance,
        approach_speed=0.0,
        direction_x=direction_x,
        direction_y=direction_y,
        angular_size=pulse,
        expansion_velocity=pulse,
    )


def sense_threat(
    fly_position: tuple[float, float],
    swatter_position: tuple[float, float],
    previous_swatter_position: tuple[float, float],
    dt: float,
    detection_radius: float = DETECTION_RADIUS,
    reference_speed: float = REFERENCE_SPEED,
) -> ThreatSignal:
    """Return a normalized looming signal and the direction toward the threat.

    Strength increases only when a nearby swatter is moving toward the fly.
    A stationary swatter therefore does not continuously trigger escape.
    """
    dx = swatter_position[0] - fly_position[0]
    dy = swatter_position[1] - fly_position[1]
    distance = hypot(dx, dy)

    old_dx = previous_swatter_position[0] - fly_position[0]
    old_dy = previous_swatter_position[1] - fly_position[1]
    previous_distance = hypot(old_dx, old_dy)
    approach_speed = max(0.0, (previous_distance - distance) / max(dt, 1e-6))

    proximity = max(0.0, min(1.0, 1.0 - distance / detection_radius))
    speed_factor = min(1.0, approach_speed / reference_speed)
    strength = proximity * speed_factor

    if distance:
        direction_x, direction_y = dx / distance, dy / distance
    else:
        direction_x, direction_y = 0.0, 0.0

    return ThreatSignal(
        strength=strength,
        distance=distance,
        approach_speed=approach_speed,
        direction_x=direction_x,
        direction_y=direction_y,
        # These are screen-space proxies, not calibrated retinal measurements.
        angular_size=proximity,
        expansion_velocity=speed_factor,
    )
