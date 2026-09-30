from vision import ARRIVAL_RADIUS, sense_swatter_arrival, sense_threat


def test_approaching_swatter_creates_stronger_signal() -> None:
    approaching = sense_threat((100, 100), (150, 100), (200, 100), 0.1)
    retreating = sense_threat((100, 100), (200, 100), (150, 100), 0.1)

    assert approaching.approach_speed == 500
    assert approaching.strength > retreating.strength
    assert approaching.expansion_velocity > retreating.expansion_velocity
    assert approaching.angular_size > 0
    assert approaching.direction_x == 1
    assert approaching.direction_y == 0


def test_distant_swatter_is_not_a_threat() -> None:
    signal = sense_threat((0, 0), (500, 0), (600, 0), 0.1)

    assert signal.strength == 0
    assert not signal.is_dangerous


def test_stationary_nearby_swatter_is_not_a_loom() -> None:
    signal = sense_threat((100, 100), (120, 100), (120, 100), 0.1)

    assert signal.angular_size > 0
    assert signal.expansion_velocity == 0
    assert signal.strength == 0


def test_behavior_stimulus_activates_when_swatter_arrives() -> None:
    outside = sense_swatter_arrival((100, 100), (100 + ARRIVAL_RADIUS + 1, 100))
    inside = sense_swatter_arrival((100, 100), (100 + ARRIVAL_RADIUS - 1, 100))

    assert outside.strength == 0
    assert inside.strength == 1
    assert inside.angular_size == 1
    assert inside.expansion_velocity == 1
    assert inside.is_dangerous
