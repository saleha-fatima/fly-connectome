"""Simplified LC4/LPLC2 -> DNp01 dynamics using MaleCNS edge weights."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

from vision import ThreatSignal


DEFAULT_WEIGHTS_PATH = (
    Path(__file__).resolve().parent / "data" / "escape_connection_summary.csv"
)
NEURON_CLASSES = ("LC4", "LPLC2", "DNp01")


@dataclass(frozen=True)
class NeuralActivity:
    lc4_left: float = 0.0
    lc4_right: float = 0.0
    lplc2_left: float = 0.0
    lplc2_right: float = 0.0
    dnp01_left: float = 0.0
    dnp01_right: float = 0.0
    escape_output: float = 0.0
    escape_active: bool = False


class EscapeCircuit:
    """A rate model whose feed-forward weights come from MaleCNS v1.0.

    Synapse counts are normalized per DNp01 neuron. The activation equations,
    time constant, and threshold are modeling choices rather than measured
    physiological values.
    """

    def __init__(
        self,
        weights_path: Path | str = DEFAULT_WEIGHTS_PATH,
        escape_threshold: float = 0.10,
        time_constant: float = 0.055,
    ) -> None:
        self.weights = self._load_weights(Path(weights_path))
        self.escape_threshold = escape_threshold
        self.time_constant = time_constant
        self.disabled: set[str] = set()
        self.activity = NeuralActivity()

    @staticmethod
    def _load_weights(path: Path) -> dict[str, dict[str, int]]:
        weights: dict[str, dict[str, int]] = {"L": {}, "R": {}}
        with path.open(newline="", encoding="utf-8") as source:
            for row in csv.DictReader(source):
                target_instance = row["target_instance"]
                side = "L" if target_instance.endswith("_L") else "R"
                weights[side][row["source_type"]] = int(row["synapse_count"])

        for side in ("L", "R"):
            if set(weights[side]) != {"LC4", "LPLC2"}:
                raise ValueError(f"Incomplete circuit weights for side {side}: {weights[side]}")
        return weights

    def toggle(self, neuron_class: str) -> bool:
        """Toggle a simulated class lesion and return True when disabled."""
        if neuron_class not in NEURON_CLASSES:
            raise ValueError(f"Unknown neuron class: {neuron_class}")
        if neuron_class in self.disabled:
            self.disabled.remove(neuron_class)
        else:
            self.disabled.add(neuron_class)
        self.reset_activity()
        return neuron_class in self.disabled

    def reset_activity(self) -> None:
        self.activity = NeuralActivity()

    def reset_all(self) -> None:
        self.disabled.clear()
        self.reset_activity()

    def update(self, signal: ThreatSignal, dt: float) -> NeuralActivity:
        # Horizontal stimulus location allocates activity across the two visual
        # hemispheres. A centered loom is split equally.
        right_fraction = max(0.0, min(1.0, (signal.direction_x + 1.0) / 2.0))
        left_fraction = 1.0 - right_fraction

        # The vision layer supplies normalized feature responses: LC4 receives
        # angular expansion velocity and LPLC2 receives angular size.
        lc4_input = signal.expansion_velocity
        lplc2_input = signal.angular_size

        if "LC4" in self.disabled:
            lc4_input = 0.0
        if "LPLC2" in self.disabled:
            lplc2_input = 0.0

        alpha = 1.0 - math.exp(-max(dt, 0.0) / self.time_constant)
        previous = self.activity
        lc4_left = self._approach(previous.lc4_left, lc4_input * left_fraction, alpha)
        lc4_right = self._approach(previous.lc4_right, lc4_input * right_fraction, alpha)
        lplc2_left = self._approach(
            previous.lplc2_left, lplc2_input * left_fraction, alpha
        )
        lplc2_right = self._approach(
            previous.lplc2_right, lplc2_input * right_fraction, alpha
        )

        left_drive = self._weighted_drive("L", lc4_left, lplc2_left)
        right_drive = self._weighted_drive("R", lc4_right, lplc2_right)
        if "DNp01" in self.disabled:
            dnp01_left = dnp01_right = 0.0
        else:
            dnp01_left = self._approach(previous.dnp01_left, left_drive, alpha)
            dnp01_right = self._approach(previous.dnp01_right, right_drive, alpha)

        escape_output = max(dnp01_left, dnp01_right)
        self.activity = NeuralActivity(
            lc4_left=lc4_left,
            lc4_right=lc4_right,
            lplc2_left=lplc2_left,
            lplc2_right=lplc2_right,
            dnp01_left=dnp01_left,
            dnp01_right=dnp01_right,
            escape_output=escape_output,
            escape_active=escape_output >= self.escape_threshold,
        )
        return self.activity

    def _weighted_drive(self, side: str, lc4: float, lplc2: float) -> float:
        side_weights = self.weights[side]
        total = side_weights["LC4"] + side_weights["LPLC2"]
        return (
            lc4 * side_weights["LC4"] + lplc2 * side_weights["LPLC2"]
        ) / total

    @staticmethod
    def _approach(current: float, target: float, alpha: float) -> float:
        return current + alpha * (target - current)
