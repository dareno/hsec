---
doc_type: system_arch
upstream:
  - 02-product-requirements.md
  - 03-context-map.md
  - 04-domain-model.md
---

# Architecture Overview

## Overview
This document outlines the high-level technical architecture for the Home Security System, describing how concrete software/hardware forms map to system functions (Crawley) and how contexts interact (see `03-context-map.md` and `04-domain-model.md`).

## Assumptions
- Runs on Raspberry Pi (Linux) with I2C enabled; MCP23017 connected per wiring guide.
- Pi GPIO INT line is available and debounced in software (~50 ms) via `gpiozero.Button`.
- Local-first system: no cloud dependency in initial phase.
- Event-driven in-process messaging between components is sufficient.

## System Functions (Crawley)
- Sensing: Acquire and decode sensor states from MCP23017.
- Alarm Evaluation: Apply arming/time-window rules to generate alarms.
- Configuration: Manage groups, arming states, and schedules.
- Notification (optional): Deliver alarms to outputs (e.g., logs, sounder).

## Mapping Form to Function (Crawley)
| Form (Implementation) | Function | Source |
|------------------------|---------|--------|
| `hardware/mcp23017.py` (I2C config, read), `hardware/mygpio.py` (Pi INT line), `sensor_monitor.py` (loop/handlers) | Sensing | PRD FR7–FR9; Context Map: Hardware I/O → Sensing |
| `event_processor.py` (PEP: state tracking + decision request), OPA (Rego) PDP | Alarm Evaluation | PRD FR3–FR6; Domain Model |
| Config storage (TBD file or simple store) consumed by sensing/alarm components | Configuration | PRD FR1–FR4, FR10 |
| Simple logger/sounder adapters subscribed to Alarm events | Notification (optional) | PRD FR5–FR6 |

## Interrupt and Event Flow
- MCP23017 configuration (see `hardware/mcp23017.py`):
  - IOCON: INTPOL=1 (active-high INT), MIRROR=1 (INTA/INTB tied), ODR=0 (push-pull).
  - INTCONA/B=0x00 (compare-to-previous → any-edge), GPINTENx enable for monitored pins.
- Pi GPIO INT handling (see `hardware/mygpio.py`):
  - `gpiozero.Button(pin, pull_up=False, bounce_time≈0.05)`; use `when_pressed` for rising edge.
- Interrupt clearing strategy:
  - Read GPIOA (0x12) then GPIOB (0x13) to clear regardless of triggering port; consider INTCAPx to capture latched state.
- Event sequence:
  1) Hardware change → INT rises → `sensor_monitor.py` reads ports
  2) Sensing maps pins→`sensor_id`, compares with repository → emits `SensorStateChanged`
  3) Alarm evaluation checks arming + time window → emits `Alarm` as needed

## Testing Seams

- **Unit seams (pure logic)**
  - Edge detection on raw MCP23017 bytes: isolate a function that consumes `GPIOA`/`GPIOB` values and previous state to produce changes. Test with synthetic bytes (no hardware).
  - State tracking and mapping: verify `sensor_id` mapping and change detection in `event_processor.py`/helpers without I/O.

- **Integration seams (software-only)**
  - Mock `hardware/mcp23017.py` reads and `hardware/mygpio.py` callbacks to drive `sensor_monitor.py` and `event_processor.py` end-to-end.
  - Assert emitted events/logs and repository updates.

- **Hardware-in-loop (opt-in)**
  - Real I2C + GPIO using Raspberry Pi; marked with `@pytest.mark.hardware` and excluded by default in `pyproject.toml`.
  - Validate INT handling, port reads, and wiring (see `img/` and wiring notes; `hardware/` modules).

- **Execution defaults**
  - Default CI/local runs exclude hardware tests; run with `uv run pytest` or `-m hardware` for HIL.
  - Test layout follows `tests/` structure: `unit/`, `integration/`, `hardware/`.

## Policy-as-Code (OPA) for Alarm Evaluation
- Pattern: PEP in `event_processor.py` constructs a decision request; OPA (PDP) evaluates Rego policies.
- Scope: Business logic decisions only (e.g., should a sensor/group alarm now?). I/O (sensor reads, notifications) stays in Python.
- Execution options:
  - Embedded: load an OPA WASM bundle from disk and evaluate in-process (offline-first, fast).
  - Sidecar: call a local OPA server over HTTP on localhost.
  - Selected: Sidecar in Docker on Raspberry Pi; mount policies into the container.
- Policy layout (options):
  - Recommended: top-level `policies/` by context, mounted read-only into OPA.
    ```
    policies/
      alarm/          # alarm evaluation policies
        policy.rego
        tests/        # `opa test` unit tests
      sensing/        # (future) sensing-related policies if needed
      shared/         # common helpers (e.g., time window utils)
    ```
  - Alternative: co-locate under each context (e.g., `src/hsec/alarm/policies/`).
    - Pro: keeps code+policy together. Con: packaging/publishing may mix concerns.
- Decision inputs (schema excerpt): `operation`, `sensor_id/group_id`, `armed`, `prev/curr`, `time`, `time_windows`, `mode`, config metadata.
- Decision outputs: `{ "allow": true|false, "reasons": ["armed", "change", "in_window"] }`.
- Testing: Unit tests for Rego rules; golden tests using captured decision inputs.

## Functional Requirements Mapping
- FR1: Sensor Grouping
  - Function: Allow users to define groups (`group_id`) mapping to lists of `sensor_id`s.
  - Form: Configuration store (TBD file-backed) read by `sensor_monitor.py` and `event_processor.py`.
- FR2: Sensor Capacity
  - Function: Support up to 16 sensors per MCP23017 and ≥5 groups.
  - Form: Hardware limit via `hardware/mcp23017.py` (16 pins); config validation in Configuration/UI; simple guard checks in `sensor_monitor.py`.
- FR3: Arming Preconditions
  - Function: Permit arming only if all targeted sensors are in safe states (reed 0.0, PIR 0.0).
  - Form: `event_processor.py` checks latest readings from repository before setting `armed=True`.
- FR4: Arming State Persistence
  - Function: Persist `armed` state per sensor/group.
  - Form: `SecurityConfig` (see `04-domain-model.md`) persisted via configuration store; consumed by `event_processor.py`.
- FR5: Alarm Generation
  - Function: Emit `Alarm` when an armed sensor/group changes state during restricted times.
  - Form: `event_processor.py` (PEP) requests OPA decision; on allow emits `Alarm`.
- FR6: Alarm Context
  - Function: Include `sensor_id`/`group_id` and context (location, time) in alarms.
  - Form: Event payload fields populated by `event_processor.py` using config metadata.
- FR7: Sensor Data Processing
  - Function: Parse MCP23017 raw bytes into `SensorReading(sensor_id, value, timestamp)`.
  - Form: `hardware/mcp23017.py` provides port reads; `sensor_monitor.py` maps pins→`sensor_id` and constructs `SensorReading`.
- FR8: State Tracking
  - Function: Store/retrieve latest `SensorReading` per `sensor_id` for change detection.
  - Form: In-memory `SensorReadingRepository` (per `04-domain-model.md`) owned by `event_processor.py`/`sensor_monitor.py`.
- FR9: Contextual Evaluation
  - Function: Provide current time and security mode to evaluate rules.
  - Form: Time source injected into `event_processor.py`; security mode from `SecurityConfig`; both passed to OPA input.
- FR10: User-Defined Time Windows
  - Function: Support user-defined restricted time windows.
  - Form: `TimeWindow` value object in `SecurityConfig`; evaluated by OPA policy (input provided by `event_processor.py`).

## Non-Functional Requirements Mapping
- Performance: Process INT→Alarm within 1–2 s.
  - Tactics: Debounce at Pi input; efficient port reads; minimal allocation in hot path.
- Reliability: False alarms <1%.
  - Tactics: Compare-to-previous filtering; repository of last readings; optional INTCAP reads.
- Maintainability: Functional core (pure rules) + imperative shell (I/O).
  - Tactics: Keep domain rules in `event_processor.py` and simple adapters around hardware.

## System Structure
- Contexts: Hardware I/O, Sensing, Alarm, Configuration/UI, Notification (optional).
- Integration:
  - Events: `SensorStateChanged`, `Alarm`.
  - Interfaces: I2C via `smbus2` (inside `hardware/mcp23017.py`), Pi GPIO via `gpiozero`.

## Integration Contracts
- Events (see `11-interface-contracts.md`):
  - `SensorStateChanged`
    ```json
    { "type": "SensorStateChanged", "sensor_id": "front_door_reed", "prev": 0.0, "curr": 1.0, "time": "2025-08-14T21:30:00Z" }
    ```
  - `Alarm`
    ```json
    { "type": "Alarm", "source_kind": "sensor", "source_id": "front_door_reed", "reason": "armed && change && in_window", "time": "2025-08-14T21:30:00Z", "context": { "location": "Front Door" } }
    ```

### Policy Decision API (OPA)
- Input
```json
{
  "operation": "alarm.evaluate",
  "subject": { "sensor_id": "front_door_reed", "group_id": "doors" },
  "state": { "prev": 0.0, "curr": 1.0, "time": "2025-08-14T21:30:00Z" },
  "config": { "armed": true, "mode": "home_night", "time_windows": [{"start":"22:00","end":"06:00"}] },
  "context": { "location": "Front Door" }
}
```
- Output
```json
{ "allow": true, "reasons": ["armed", "change", "in_window"] }
```

## Key Decisions
- MCP23017 INT: active-high, push-pull, INTA/INTB mirrored.
- Compare-to-previous interrupt mode (any-edge) for change detection.
- Pi INT line uses internal pulldown; debounce ≈50 ms via `gpiozero.Button`.

## Risks and Mitigations
- Hardware bounce or noise.
  - Mitigation: Debounce at Pi input; validate transitions against last state.
- Power brownouts causing inconsistent reads.
  - Mitigation: Stable power; detect and reinitialize MCP23017 on recovery.
- Floating inputs when sensors disconnected.
  - Mitigation: Use appropriate pull-ups (external or GPPU) as per wiring.

## Open Questions
- Event schema versioning approach for `SensorStateChanged`/`Alarm`?
- Use INTCAPx vs GPIOx reads to avoid races?
- Where to persist configuration (file, env, minimal UI)?