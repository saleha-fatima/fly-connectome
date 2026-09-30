from behavior import BehaviorPhase, FlyBehavior
from looming import LoomingTrial
from neural_model import EscapeCircuit


def run_trial(speed_name: str, disable_dnp01: bool = False):
    trial = LoomingTrial()
    trial.configure(side="right", speed_name=speed_name)
    trial.start()
    circuit = EscapeCircuit()
    if disable_dnp01:
        circuit.toggle("DNp01")
    behavior = FlyBehavior()
    launch = None
    phases = set()

    for _ in range(180):
        sample = trial.update(1 / 120)
        activity = circuit.update(sample.signal, 1 / 120)
        snapshot = behavior.update(activity, sample.signal, 1 / 120)
        phases.add(snapshot.phase)
        if snapshot.launch:
            launch = snapshot
            break
    return launch, phases


def test_loom_geometry_expands_as_object_approaches() -> None:
    trial = LoomingTrial()
    trial.configure(speed_name="fast")
    first = trial.start()
    later = trial.update(0.25)

    assert later.distance_mm < first.distance_mm
    assert later.angular_size_deg > first.angular_size_deg
    assert later.angular_velocity_deg_s > first.angular_velocity_deg_s
    assert later.time_to_collision_s < first.time_to_collision_s


def test_fast_and_slow_looms_produce_distinct_takeoff_programs() -> None:
    fast_launch, fast_phases = run_trial("fast")
    slow_launch, slow_phases = run_trial("slow")

    assert BehaviorPhase.PREPARING in fast_phases
    assert BehaviorPhase.PREPARING in slow_phases
    assert fast_launch is not None and fast_launch.program == "rapid GF-like"
    assert slow_launch is not None and slow_launch.program == "prepared long-mode"
    assert fast_launch.launch_speed > slow_launch.launch_speed


def test_dnp01_lesion_prevents_loom_evoked_takeoff() -> None:
    launch, phases = run_trial("fast", disable_dnp01=True)

    assert BehaviorPhase.PREPARING in phases
    assert launch is None
