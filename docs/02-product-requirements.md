---
doc_type: prd
upstream:
  - 01-project-vision.md
---
# Product Requirements Document (PRD)


## Purpose and Scope
The Home Security System monitors sensors (reed for doors/windows, PIR for motion) via a Raspberry Pi and MCP23017 I/O expander, allowing users to group sensors (e.g., windows, upstairs) and trigger alarms for state changes (e.g., door opening, motion detected) when armed during restricted times. This PRD defines functional and non-functional requirements for a reliable, user-configurable security solution.

## Functional Requirements
- FR1: Sensor Grouping
  - Users shall define sensor groups (e.g., `windows`, `doors`) with unique `group_id` and a list of `sensor_id`s (e.g., `["front_door_reed", "back_door_reed"]`).
- FR2: Sensor Capacity
  - System shall support up to 16 sensors per MCP23017 chip and at least 5 user-defined groups.
- FR3: Arming Preconditions
  - System shall allow arming a group or individual sensor only if all sensors have safe states (reed: `value=0.0` for closed; PIR: `value=0.0` for no motion).
- FR4: Arming State Persistence
  - Arming state (`armed=True/False`) shall be stored in `SecurityConfig` per sensor or group.
- FR5: Alarm Generation
  - System shall generate an Alarm event when an armed sensor/group detects a state change (reed 0.0→1.0; PIR 0.0→1.0) during restricted times.
- FR6: Alarm Context
  - Alarms shall include `sensor_id` or `group_id` and context (e.g., location, time).
- FR7: Sensor Data Processing
  - System shall parse MCP23017 raw bytes into `SensorReading` objects (`sensor_id`, `value: float`, `timestamp`).
- FR8: State Tracking
  - System shall store/retrieve the latest `SensorReading` per `sensor_id` for state change detection.
- FR9: Contextual Evaluation
  - System shall provide current time and security mode to evaluate rules against restricted time windows.
- FR10: User-Defined Time Windows
  - System shall support user-defined restricted times (e.g., `{ "start": "22:00", "end": "06:00" }`).

## Non-Functional Requirements
- Performance: Process interrupts and generate alarms within 1–2 seconds.
- Reliability: False alarm rate <1% via state-change and arming checks.
- Usability: Configuration (groups, times) settable in <2 minutes via a simple interface.
- Hardware: Stable I2C communication with MCP23017 and Raspberry Pi.

## Constraints
- Platform: Runs on Raspberry Pi (Linux) with I2C enabled; uses MCP23017 I/O expanders for sensor inputs.
- Power: Requires stable power for Pi and peripherals; brownouts may cause unreliable readings.
- Offline-first: No cloud/mobile dependency in the initial phase; all processing is local.
- Environment: Indoor operation; typical residential temperature/humidity ranges.
- Data privacy: No transmission of PII off-device by default.