"""Observable escape phases driven by the neural circuit output."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from neural_model import NeuralActivity
from vision import ThreatSignal


class BehaviorPhase(str, Enum):
    WANDERING = "wandering"
    PREPARING = "postural preparation"
    JUMPING = "leg extension / jump"
    AIRBORNE = "airborne"
    RECOVERING = "recovering"


@dataclass(frozen=True)
class BehaviorSnapshot:
    phase: BehaviorPhase = BehaviorPhase.WANDERING
    program: str = "none"
    preparation_progress: float = 0.0
    launch: bool = False
    launch_speed: float = 0.0
    escape_x: float = 0.0
    escape_y: float = 0.0
    wings_raised: bool = False
    tumbling: bool = False


class FlyBehavior:
    """A transparent state machine for visible, literature-inspired actions."""

    PREPARATION_INPUT_THRESHOLD = 0.07
    RAPID_LC4_THRESHOLD = 0.14
    RAPID_PREPARATION_S = 0.08
    PLANNED_PREPARATION_S = 0.20
    JUMP_DURATION_S = 0.08
    AIRBORNE_DURATION_S = 0.45
    RECOVERY_DURATION_S = 0.30

    def __init__(self) -> None:
        self.phase = BehaviorPhase.WANDERING
        self.program = "none"
        self.phase_elapsed = 0.0
        self.preparation_elapsed = 0.0
        self.no_threat_elapsed = 0.0
        self.escape_x = 0.0
        self.escape_y = -1.0
        self.pending_takeoff = False
        self.snapshot = BehaviorSnapshot()

    def reset(self) -> None:
        self.__init__()

    def update(
        self, activity: NeuralActivity, signal: ThreatSignal, dt: float
    ) -> BehaviorSnapshot:
        dt = max(0.0, dt)
        self.phase_elapsed += dt
        launch = False
        visual_activity = max(
            activity.lc4_left,
            activity.lc4_right,
            activity.lplc2_left,
            activity.lplc2_right,
        )

        if signal.strength > 0:
            self.no_threat_elapsed = 0.0
        else:
            self.no_threat_elapsed += dt

        if (
            self.phase == BehaviorPhase.WANDERING
            and visual_activity >= self.PREPARATION_INPUT_THRESHOLD
        ):
            self.phase = BehaviorPhase.PREPARING
            self.phase_elapsed = 0.0
            self.preparation_elapsed = 0.0
            self.escape_x = -signal.direction_x
            self.escape_y = -signal.direction_y

        if self.phase == BehaviorPhase.PREPARING:
            self.preparation_elapsed += dt
            if signal.direction_x or signal.direction_y:
                self.escape_x = -signal.direction_x
                self.escape_y = -signal.direction_y

            if activity.escape_active and not self.pending_takeoff:
                lc4_peak = max(activity.lc4_left, activity.lc4_right)
                if lc4_peak >= self.RAPID_LC4_THRESHOLD:
                    self.program = "rapid GF-like"
                else:
                    self.program = "prepared long-mode"
                self.pending_takeoff = True

            required_preparation = (
                self.RAPID_PREPARATION_S
                if self.program == "rapid GF-like"
                else self.PLANNED_PREPARATION_S
            )
            if self.pending_takeoff and self.preparation_elapsed >= required_preparation:
                self.phase = BehaviorPhase.JUMPING
                self.phase_elapsed = 0.0
                launch = True
            elif self.no_threat_elapsed > 0.35 and not self.pending_takeoff:
                self.reset()

        elif (
            self.phase == BehaviorPhase.JUMPING
            and self.phase_elapsed >= self.JUMP_DURATION_S
        ):
            self.phase = BehaviorPhase.AIRBORNE
            self.phase_elapsed = 0.0
        elif (
            self.phase == BehaviorPhase.AIRBORNE
            and self.phase_elapsed >= self.AIRBORNE_DURATION_S
        ):
            self.phase = BehaviorPhase.RECOVERING
            self.phase_elapsed = 0.0
        elif (
            self.phase == BehaviorPhase.RECOVERING
            and self.phase_elapsed >= self.RECOVERY_DURATION_S
        ):
            self.reset()

        if self.program == "rapid GF-like":
            launch_speed = 430.0
            wings_raised = False
            tumbling = self.phase in {BehaviorPhase.JUMPING, BehaviorPhase.AIRBORNE}
            preparation_duration = self.RAPID_PREPARATION_S
        else:
            launch_speed = 280.0
            wings_raised = self.phase == BehaviorPhase.PREPARING
            tumbling = False
            preparation_duration = self.PLANNED_PREPARATION_S

        preparation_progress = min(
            1.0, self.preparation_elapsed / preparation_duration
        )
        self.snapshot = BehaviorSnapshot(
            phase=self.phase,
            program=self.program,
            preparation_progress=preparation_progress,
            launch=launch,
            launch_speed=launch_speed if launch else 0.0,
            escape_x=self.escape_x,
            escape_y=self.escape_y,
            wings_raised=wings_raised,
            tumbling=tumbling,
        )
        return self.snapshot
