import math
import pytest

from models import SensorReading

# System under test (to be implemented)
from services.sensor_deserializer import (
    deserialize_ports,
    PayloadValidationError,
    PortMappingError,
)


def test_happy_path_mapping_and_ordering():
    port_map = {
        "gpa6": {"sensor_id": "front_door_reed", "type": "reed"},
        "gpb7": {"sensor_id": "mb_window_reed", "type": "reed"},
        "gpa1": {"sensor_id": "hall_pir", "type": "pir"},
    }
    # Set GPA6=1, GPB7=1, GPA1=0
    gpioa = 0b0100_0000  # bit6
    gpiob = 0b1000_0000  # bit7
    ts = 1723930000.0

    readings = deserialize_ports(gpioa, gpiob, ts, port_map)

    # Expect one reading per mapped entry, ordered by sensor_id
    assert [r.sensor_id for r in readings] == [
        "front_door_reed",
        "hall_pir",
        "mb_window_reed",
    ]
    # Values normalized 1.0 for HIGH, 0.0 for LOW
    expected = {
        "front_door_reed": 1.0,
        "hall_pir": 0.0,
        "mb_window_reed": 1.0,
    }
    assert all(isinstance(r, SensorReading) for r in readings)
    for r in readings:
        assert math.isclose(r.timestamp, ts)
        assert r.value == expected[r.sensor_id]


def test_invalid_gpio_range_raises():
    port_map = {"gpa0": {"sensor_id": "any", "type": "reed"}}

    with pytest.raises(PayloadValidationError) as ei:
        deserialize_ports(256, 0, 0.0, port_map)
    assert "gpioa" in str(ei.value)

    with pytest.raises(PayloadValidationError) as ei:
        deserialize_ports(-1, 0, 0.0, port_map)
    assert "gpioa" in str(ei.value)

    with pytest.raises(PayloadValidationError) as ei:
        deserialize_ports(0, 300, 0.0, port_map)
    assert "gpiob" in str(ei.value)


def test_type_mismatch_and_ts_validation():
    port_map = {"gpa0": {"sensor_id": "any", "type": "reed"}}

    with pytest.raises(PayloadValidationError):
        deserialize_ports("ff", 0, 0.0, port_map)  # type: ignore[arg-type]

    with pytest.raises(PayloadValidationError):
        deserialize_ports(0, "ff", 0.0, port_map)  # type: ignore[arg-type]

    with pytest.raises(PayloadValidationError) as ei:
        deserialize_ports(0, 0, "now", port_map)  # type: ignore[arg-type]
    assert "timestamp" in str(ei.value)


def test_invalid_port_map_key_and_missing_sensor_id():
    # Invalid key
    bad_map = {"gpz1": {"sensor_id": "x", "type": "reed"}}
    with pytest.raises(PortMappingError) as ei:
        deserialize_ports(0, 0, 0.0, bad_map)
    assert "gpz1" in str(ei.value)

    # Missing sensor_id
    bad_map2 = {"gpa1": {"type": "reed"}}
    with pytest.raises(PortMappingError) as ei:
        deserialize_ports(0, 0, 0.0, bad_map2)
    assert "sensor_id" in str(ei.value)


def test_invalid_type_if_present():
    bad_map = {"gpa1": {"sensor_id": "x", "type": "temp"}}
    with pytest.raises(PortMappingError) as ei:
        deserialize_ports(0, 0, 0.0, bad_map)
    assert "type" in str(ei.value)
