from neural_model import EscapeCircuit
from vision import ThreatSignal


FAST_RIGHT_LOOM = ThreatSignal(
    strength=0.8,
    distance=44,
    approach_speed=650,
    direction_x=1,
    direction_y=0,
    angular_size=0.8,
    expansion_velocity=1.0,
)


def stimulate(circuit: EscapeCircuit, frames: int = 30):
    activity = None
    for _ in range(frames):
        activity = circuit.update(FAST_RIGHT_LOOM, 1 / 60)
    return activity


def test_loads_real_bilateral_malecns_weights() -> None:
    circuit = EscapeCircuit()

    assert circuit.escape_threshold == 0.10
    assert circuit.weights == {
        "L": {"LC4": 3782, "LPLC2": 2642},
        "R": {"LC4": 2580, "LPLC2": 2220},
    }


def test_fast_right_loom_activates_right_dnp01_and_escape() -> None:
    activity = stimulate(EscapeCircuit())

    assert activity is not None
    assert activity.dnp01_right > activity.dnp01_left
    assert activity.escape_active


def test_disabling_visual_class_weakens_response() -> None:
    normal = stimulate(EscapeCircuit())
    lesioned = EscapeCircuit()
    lesioned.toggle("LC4")
    without_lc4 = stimulate(lesioned)

    assert normal is not None and without_lc4 is not None
    assert without_lc4.escape_output < normal.escape_output


def test_disabling_dnp01_prevents_escape() -> None:
    circuit = EscapeCircuit()
    circuit.toggle("DNp01")
    activity = stimulate(circuit)

    assert activity is not None
    assert activity.lc4_right > 0
    assert activity.dnp01_right == 0
    assert not activity.escape_active
