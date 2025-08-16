---
doc_type: domain_model
upstream:
  - 02-product-requirements.md
  - 03-context-map.md
---

# Domain Model

 

## Ubiquitous Language
- Sensor: A physical input (e.g., front door reed, PIR motion) identified by `sensor_id`.
- SensorGroup: A named collection of sensors (e.g., `windows`, `downstairs`).
- SensorReading: Observed value with timestamp for a `sensor_id`.
- SecurityConfig: Configuration governing arming state and rules (e.g., restricted times).
- Event: A domain-relevant occurrence (e.g., door opening, motion detected).
- ErrorEvent: An error condition surfaced as an event.
- PIR: A passive infrared sensor that detects motion.
- Reed: A reed switch that detects the opening or closing of a door or window.

## Aggregates and Entities
- Sensor (Entity)
  - Identity: `sensor_id`
  - Attributes: `type` (reed, PIR, ...), `location`
- SensorGroup (Entity/Aggregate Root)
  - Identity: `group_id`
  - Members: `sensor_id[]`
  - State: `armed: bool`
- Alarm (Entity)
  - Identity: `alarm_id`
  - Attributes: `source` (sensor/group), `time`, `context`

## Value Objects
- SensorReading(value: float, timestamp: datetime)
- SecurityConfig(armed: bool, restricted_time_window, rules)
- TimeWindow(start: HH:MM, end: HH:MM)

## Domain Services
- SensorDeserializerService
  - Responsibility: Map raw hardware bytes into `SensorReading` objects.
  - Notes: Hardware-specific adapters live outside the domain; service operates on abstractions.
- SemanticMapperService
  - Responsibility: Evaluate readings + `SecurityConfig` to produce domain `Event`s (e.g., Alarm).
- SecurityContextService
  - Responsibility: Provide current time/mode context for evaluating rules.

## Repository
- SensorReadingRepository
  - Responsibility: Track previous readings per `sensor_id` to detect state changes.

## Domain Events
- SensorStateChanged(sensor_id, previous_value, current_value, time)
- Alarm(source_id, source_kind: sensor|group, reason, time, context)
- ErrorEvent(code, details, time)

## Invariants and Policies (high level)
- A group can only be armed if all member sensors are in a safe state.
- Alarms are only generated when:
  - The source (sensor or group) is armed, and
  - A meaningful state change occurs, and
  - The change happens within restricted times, if configured.
- Sensor reading transitions and thresholds are defined per sensor type.

## Notes on Boundaries
- Domain model is technology-agnostic; no I2C, GPIO, or MCP23017 details here.
- Hardware integration, debounce, and interrupt behavior are specified in `11-interface-contracts.md` and implementation docs.
- Architecture maps functions (Crawley) to forms; see `10-architecture-overview.md`.
