from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from models import SensorReading


class PayloadValidationError(ValueError):
    """Raised when primitive inputs (gpioa/gpiob/timestamp) are invalid."""


class PortMappingError(ValueError):
    """Raised when the provided port_map contains invalid keys or values."""


_VALID_TYPES = {"reed", "pir"}
_VALID_PINS = tuple([f"gpa{i}" for i in range(8)] + [f"gpb{i}" for i in range(8)])


def _is_int_like(x: object) -> bool:
    # Exclude bools (bool is a subclass of int)
    return isinstance(x, int) and not isinstance(x, bool)


def _validate_gpio_value(name: str, v: object) -> int:
    if not _is_int_like(v):
        raise PayloadValidationError(f"{name} must be int in [0,255], got type={type(v).__name__}")
    iv = int(v)
    if not (0 <= iv <= 255):
        raise PayloadValidationError(f"{name} out of range: {iv} (expected 0..255)")
    return iv


def _validate_timestamp(ts: object) -> float:
    if isinstance(ts, bool) or not isinstance(ts, (int, float)):
        raise PayloadValidationError(f"timestamp must be number of seconds (float), got type={type(ts).__name__}")
    return float(ts)


def _parse_pin_key(pin: str) -> Tuple[str, int]:
    p = pin.lower()
    if p not in _VALID_PINS:
        raise PortMappingError(
            f"invalid port_map key '{pin}' (expected one of: gpa0..gpa7 or gpb0..gpb7)"
        )
    port = p[:3]  # 'gpa' or 'gpb'
    idx = int(p[3:])
    return port, idx


def _validate_port_map(port_map: Dict[str, dict]) -> Dict[str, dict]:
    if not isinstance(port_map, dict):
        raise PortMappingError(f"port_map must be a dict, got {type(port_map).__name__}")

    # Validate keys and essential fields; return normalized copy (lower-case keys)
    normalized: Dict[str, dict] = {}
    for k, v in port_map.items():
        if not isinstance(k, str):
            raise PortMappingError(f"port_map key must be str, got {type(k).__name__}")
        _parse_pin_key(k)  # validates key shape
        if not isinstance(v, dict):
            raise PortMappingError(f"port_map['{k}'] must be a mapping, got {type(v).__name__}")
        sensor_id = v.get("sensor_id")
        if not isinstance(sensor_id, str) or not sensor_id:
            raise PortMappingError(f"port_map['{k}'].sensor_id missing or invalid")
        if "type" in v:
            t = v.get("type")
            if t not in _VALID_TYPES:
                raise PortMappingError(
                    f"port_map['{k}'].type invalid: {t!r} (expected one of {_VALID_TYPES})"
                )
        normalized[k.lower()] = {"sensor_id": sensor_id, **({"type": v["type"]} if "type" in v else {})}
    return normalized


def _bit_value(gpio: int, idx: int) -> float:
    return 1.0 if ((gpio >> idx) & 0x1) else 0.0


def deserialize_ports(
    gpioa: int,
    gpiob: int,
    timestamp: float,
    port_map: Dict[str, dict],
) -> List[SensorReading]:
    """Convert MCP23017 port values into domain SensorReadings using a PortMap.

    - Validates primitive inputs (gpioa/gpiob/timestamp)
    - Validates port_map keys and required fields
    - Produces one SensorReading per entry in port_map, ordered by sensor_id
    - Normalizes bit HIGH->1.0, LOW->0.0
    """
    a = _validate_gpio_value("gpioa", gpioa)
    b = _validate_gpio_value("gpiob", gpiob)
    ts = _validate_timestamp(timestamp)
    mapping = _validate_port_map(port_map)

    readings: List[SensorReading] = []
    for pin, entry in mapping.items():
        port, idx = _parse_pin_key(pin)
        if port == "gpa":
            val = _bit_value(a, idx)
        else:
            val = _bit_value(b, idx)
        readings.append(SensorReading(sensor_id=entry["sensor_id"], value=val, timestamp=ts))

    readings.sort(key=lambda r: r.sensor_id)
    return readings
