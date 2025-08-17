---
doc_type: interface_contracts
upstream:
  - 02-product-requirements.md
  - 04-context-map.md
  - 05-domain-model.md
  - 06-architecture-overview.md
---

# Interface Contracts

This document defines the interfaces between hardware, software components, and policy evaluation for the Home Security System. Upstream references define the “why”; this file defines the “how we integrate”.

## Versioning
- Event and API payloads include `schema_version` (integer). Current: 0.
- Backwards-compatible changes: add optional fields; do not repurpose semantics.
- Breaking changes: bump `schema_version` and document migration notes here.

## Hardware Interfaces

- MCP23017 (I2C)
  - Address: configurable (default 0x20–0x27 range). Env: `HSEC_MCP23017_ADDR`. Bus env: `HSEC_I2C_BUS`.
  - Setup (see `hardware/mcp23017.py`):
    - IOCON: INTPOL=1 (active-high), MIRROR=1 (tie INTA/INTB), ODR=0 (push-pull INT).
    - GPINTENx: enable per monitored pin.
    - INTCONx: 0x00 (compare-to-previous → any-edge). DEFVALx optional for rising-only.
    - IODIRx/GPPUx: configured as needed by wiring. Note: MCP has pull-ups only; use external bias if pull-down required.
  - Interrupt clearing: read GPIOA (0x12) then GPIOB (0x13) to clear regardless of triggering port. Optional: use INTCAPx to capture latched state at interrupt time.
  - Read semantics: reads return 8-bit port state. Mapping to `sensor_id` is provided by configuration.

- Raspberry Pi GPIO (INT line)
  - INT pin: active-high push-pull from MCP23017 to Pi (e.g., BCM 5). Env: `HSEC_INT_GPIO`.
  - Debounce: `gpiozero.Button(pin, pull_up=False, bounce_time=0.05)`; use `when_pressed` (rising edge). Pi uses internal pulldown; this does not affect MCP inputs.

- Wiring notes (reference)
  - Typical reed: external 10k pull-up → junction → series ~1k → MCP pin; junction → reed → GND.
  - Behavior: open = HIGH; closed = LOW. Disable MCP internal pull-up if external exists on that line.

- Runtime usage: see `docs/08-runtime-flows.md#interrupt-and-event-flow` for sequencing and timing.

## Events

- SensorStateChanged
  - Purpose: emitted by the Security BC — Sensing module when a sensor’s effective state changes.
  - Schema (example):
    ```json
    { "type": "SensorStateChanged", "sensor_id": "front_door_reed", "prev": 0.0, "curr": 1.0, "time": "2025-08-14T21:30:00Z", "schema_version": 0 }
    ```
  - Notes: `prev`/`curr` are domain-normalized floats (0.0 or 1.0 for reed/PIR). Time is ISO-8601 UTC.

- Alarm
  - Purpose: emitted by the Security BC — Alarm Evaluation module when policy allows.
  - Schema (example):
    ```json
    { "type": "Alarm", "source_kind": "sensor", "source_id": "front_door_reed", "reason": "armed && change && in_window", "time": "2025-08-14T21:30:00Z", "context": { "location": "Front Door" }, "schema_version": 0 }
    ```
  - Optional transparency: add `reasons` array (e.g., `["armed","change","in_window"]`) sourced from OPA decision.

## Configuration Read Interfaces

- Groups
  - Shape:
    ```json
    { "groups": [ { "group_id": "doors", "sensor_ids": ["front_door_reed"], "metadata": {"location": "Downstairs"} } ] }
    ```
  - Consumers: Sensor Monitor (planned, mapping), Event Processor (planned, context).

- Arming State (SecurityConfig)
  - Shape:
    ```json
    { "armed": { "sensors": {"front_door_reed": true}, "groups": {"doors": true} }, "mode": "home_night" }
    ```
  - Persisted by Configuration/UI; read-only to Sensing/Alarm.

- Time Windows
  - Shape:
    ```json
    { "time_windows": [{ "start": "22:00", "end": "06:00" }] }
    ```
  - Local time policy: evaluate against configured local timezone; convert to UTC for events.

## Policy Decision API (OPA sidecar)

- Endpoint: `POST http://127.0.0.1:8181/v1/data/hsec/alarm` (package path to retrieve both `allow` and `reasons`)
- Headers: `Content-Type: application/json`
- Input (example):
  ```json
  {
    "operation": "alarm.evaluate",
    "subject": { "sensor_id": "front_door_reed", "group_id": "doors" },
    "state": { "prev": 0.0, "curr": 1.0, "time": "2025-08-14T21:30:00Z" },
    "config": { "armed": true, "mode": "home_night", "time_windows": [{"start":"22:00","end":"06:00"}] },
    "context": { "location": "Front Door" },
    "schema_version": 0
  }
  ```
- Output (example):
  ```json
  { "result": { "allow": true, "reasons": ["armed", "change", "in_window"] } }
  ```
- Error handling:
  - Treat non-2xx responses as transport/server errors (OPA not ready, internal error).
  - A successful evaluation typically includes a top-level `result`. If `result` is missing/undefined, handle as "deny by default" and log details.
  - Implement retries/backoff on transient failures.
- Execution mode: OPA runs in Docker on Raspberry Pi; policies mounted read-only.
- Policy location (recommended): top-level `policies/` dir with subfolders by context; alternative: co-locate under each context in `src/`.

## Diagnostics & Testability

- OPA unit tests: `opa test policies/`
- Golden inputs: capture real decision inputs from the Event Processor component (planned) for regression tests.
- Hardware-in-loop: ensure interrupts clear on both ports and loopback tests exercise `SensorStateChanged` and `Alarm` end-to-end.
