---
doc_type: prd
upstream:
  - 01-project-vision.md
---
# Product Requirements Document (PRD)

## Purpose and Scope
The Home Security System monitors sensors (reed for doors/windows, PIR for motion) via a Raspberry Pi and MCP23017 I/O expander, allowing users to group sensors (e.g., windows, upstairs) and trigger alarms for state changes (e.g., door opening, motion detected) when armed during restricted times. This PRD defines functional and non-functional requirements for a reliable, user-configurable security solution.

## Functional Requirements

### FR1: Sensor Grouping
Create named groups (e.g., ‘Windows’, ‘Downstairs’) by selecting sensors by their names. A group may only reference existing sensors.

### FR2: Sensor Capacity
Support up to 16 sensors per MCP23017 module and at least 5 user-defined groups.

### FR3: Arming Preconditions
Allow arming only when every selected sensor shows a safe state (doors/windows closed; no motion).

### FR4: Arming State Persistence
Remember armed/disarmed settings across restarts. Only the configuration/UI changes these settings; sensing and alarms only read them.

### FR5: Alarm Generation
When armed, raise an alarm if a sensor or group changes state during the homeowner’s restricted times (quiet hours) configured in settings.

### FR6: Alarm Context
Each alarm shows what triggered it (sensor or group), its name, when it happened, and—when known—where it is.

### FR7: Sensor Data Processing
Produce readings that include the sensor name, its current state (open/closed or motion/no motion), and when it was observed.

### FR8: State Tracking
Remember the last known state for each sensor so the system can spot changes.


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