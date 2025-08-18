from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SensorReading:
    """Domain value object representing a single sensor reading.

    Fields:
      - sensor_id: stable domain identifier for the sensor (not a pin name)
      - value: normalized float value (0.0 or 1.0 for reed/PIR)
      - timestamp: UNIX timestamp in seconds (float)
    """

    sensor_id: str
    value: float
    timestamp: float
