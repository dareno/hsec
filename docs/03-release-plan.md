---
doc_type: plan
upstream:
  - 02-product-requirements.md
---
# Release Plan

Purpose: Prioritize and track delivery of stories mapped to Functional Requirements (FRs) in `docs/02-product-requirements.md`. FR numbers are stable identifiers; priority lives here.

## Priority Rubric (P-levels)
- P0 — Must-have/critical path for MVP; unblock immediately
- P1 — High priority for current release
- P2 — Normal priority; schedule by capacity
- P3 — Nice-to-have; defer post-MVP

Status: Planned | In Progress | Blocked | Done | Deferred

## FR Priorities
Edit Priority/Target per release planning. Do not renumber FRs.
Note: FR titles below are convenience labels; authoritative definitions live in `docs/02-product-requirements.md`.

| FR ID                                                            | Title                    | Priority | Target Release | Notes |
|:----------------------------------------------------------------:|:-------------------------|:--------:|:--------------:|:-----:|
| [FR1](02-product-requirements.md#fr1-sensor-grouping)            | Sensor Grouping          |          |                |       |
| [FR2](02-product-requirements.md#fr2-sensor-capacity)            | Sensor Capacity          |          |                |       |
| [FR3](02-product-requirements.md#fr3-arming-preconditions)       | Arming Preconditions     |          |                |       |
| [FR4](02-product-requirements.md#fr4-arming-state-persistence)   | Arming State Persistence |          |                |       |
| [FR5](02-product-requirements.md#fr5-alarm-generation)           | Alarm Generation         |          |                |       |
| [FR6](02-product-requirements.md#fr6-alarm-context)              | Alarm Context            |          |                |       |
| [FR7](02-product-requirements.md#fr7-sensor-data-processing)     | Sensor Data Processing   |          |                |       |
| [FR8](02-product-requirements.md#fr8-state-tracking)             | State Tracking           |          |                |       |
| [FR9](02-product-requirements.md#fr9-contextual-evaluation)      | Contextual Evaluation    |          |                |       |
| [FR10](02-product-requirements.md#fr10-user-defined-time-windows)| User-Defined Time Windows|          |                |       |

## Story Backlog
Stories slice FRs into deliverable units. Relationship is many-to-many: a story may advance multiple FRs, and an FR typically requires multiple stories.

| Story ID | Title                                  | Linked FRs | Priority | Status  |
|:--------:|:---------------------------------------|:-----------|:--------:|:-------:|
| ST-001   | PIR change detection                   | FR7        |       P1  | Done |
| ST-002   | Front door plunger contact change detection (GPA6)| FR7        |       P1  | Done |
| ST-003   | Door plunger contact sensors verification (kitchen GPA3, family-room GPA4, basement GPA7) | FR7 |       P1  | Done    |
| ST-004   | Window magnetic reed change detection (GPB7, main bedroom windows) | FR7 |       P1  | Done |
| ST-005   | MCP23017 bits -> SensorReading         | FR7        |       P1  | Planned |
| ST-006   | Schema-versioned payload ingestion (v0)| FR7        |       P2  | Planned |

## ST-001 — Acceptance Criteria & Scope

Scope
- Manual hardware verification of PIR on MCP23017 `GPA1` using the Raspberry Pi.
- Code under test: `hardware/mcp23017.py` (and `hardware/mygpio.py` only for INT-line debounce if needed).
- Exclude application layer (Sensor Monitor, Event Processor) and any mocks/fakes.

Acceptance Criteria (FR7: Sensor Data Processing via hardware test)
- Wiring: PIR output -> MCP23017 `GPA1`; MCP `INT` -> Raspberry Pi BCM 5; common ground and power per project notes.
- After calling `MCP23017.setup()`:
  - When you manually trigger motion, the INT line asserts and `MCP23017.read_data()` reports a toggle of `GPIOA` bit 1 away from its baseline level.
  - After the PIR settles, the INT line asserts again and `read_data()` reports `GPIOA` bit 1 toggled back to the baseline.
  - Observed on our current hardware/module: baseline `GPA1=0` (`GPIOA=00101101`), motion `GPA1=1` (`GPIOA=00101111`), settle `GPA1=0` (`GPIOA=00101101`). Module polarity can vary; see `docs/devices/pir-sensor.md`.
  - No repeated interrupts in steady state beyond INT input debounce (~50 ms on the Pi side).
- Tests live under `tests/hardware/mcp23017/`, marked `@pytest.mark.hardware`. These are manual and excluded from default CI.

Operator Procedure (manual hardware test)
- Prepare: Raspberry Pi with I2C enabled; MCP23017 at address `0x20` on bus `1` (adjust via env if different).
- Run: `uv sync --group test --group hardware` then `uv run pytest -m hardware -s tests/hardware/mcp23017/` (use `-s` to see prompts/output)
- Follow the test prompts to walk in front of the PIR to create motion and then wait for it to settle. Tests use generous timeouts.

Out of Scope (deferred)
- Domain entities, logging/aggregation, grouping/arming, restricted time windows.
- Any processing outside `hardware/`.

## Accounting in Story
- Attach a short note or snippet of observed readings (e.g., GPIOA values across edges) in the PR linked to `ST-001` and `FR7`.
- Evidence (ST-001): Baseline `GPIOA=00101101` → `GPA1=0`; Motion `GPIOA=00101111` → `GPA1=1`; Settle `GPIOA=00101101` → `GPA1=0`.
  Test: `tests/hardware/mcp23017/test_pir_gpa1_manual.py`; Run: `uv run pytest -m hardware -s tests/hardware/mcp23017/test_pir_gpa1_manual.py`.

- Observed (2025-08-16): Baseline `GPIOA=00101101` (bit1=0) → Motion `GPIOA=00101111` (bit1=1) → Settle `GPIOA=00101101` (bit1=0).

## ST-002 — Acceptance Criteria & Scope

Scope
- Manual hardware verification of a door plunger switch (mechanical contact) on MCP23017 `GPA6` (front door) using the Raspberry Pi.
- Code under test: `hardware/mcp23017.py` (and `hardware/mygpio.py` only for INT-line debounce if needed).
- Exclude application layer (Sensor Monitor and Event Processor components) and any mocks/fakes.

Acceptance Criteria (FR7: Sensor Data Processing via hardware test)
- Wiring: Door plunger switch output -> MCP23017 `GPA6`; MCP `INT` -> Raspberry Pi BCM 5; common ground and power per project notes.
- After calling `MCP23017.setup()`:
  - When you open the door (release the plunger), the INT line asserts and `MCP23017.read_data()` reports a toggle of `GPIOA` bit 6 away from its baseline level.
  - When you close the door (plunger is depressed), the INT line asserts again and `read_data()` reports `GPIOA` bit 6 toggled back to the baseline.
  - Contact wiring (NO vs NC) can vary; treat acceptance as toggle-based relative to baseline. See `docs/devices/door-plunger-switch.md`.
  - No repeated interrupts in steady state beyond INT input debounce (~50 ms on the Pi side).
- Tests live under `tests/hardware/mcp23017/`, marked `@pytest.mark.hardware`. These are manual and excluded from default CI.

Operator Procedure (manual hardware test)
- Prepare: Raspberry Pi with I2C enabled; MCP23017 at address `0x20` on bus `1` (adjust via env if different).
- Run: `uv sync --group test --group hardware` then `uv run pytest -m hardware -s tests/hardware/mcp23017/test_reed_gpa6_manual.py`
- Follow the test prompts: remain still for baseline capture, then open the front door during the first interval, then close it during the second interval.

Out of Scope (deferred)
- Domain entities, logging/aggregation, grouping/arming, restricted time windows.
- Any processing outside `hardware/`.

## Accounting in Story
- Attach a short note or snippet of observed readings (e.g., GPIOA bit 6 values across edges) in the PR linked to `ST-002` and `FR7`.

- Evidence (ST-002): Baseline `GPIOA=00101101` → `GPA6=0`; Open `GPIOA=01101101` → `GPA6=1`; Close `GPIOA=00101101` → `GPA6=0`.
  Test: `tests/hardware/mcp23017/test_reed_gpa6_manual.py`; Run: `uv run pytest -m hardware -s tests/hardware/mcp23017/test_reed_gpa6_manual.py`.

- Observed (2025-08-16): Baseline `GPIOA=00101111` (bit6=0) → Open `GPIOA=01101111` (bit6=1) → Close `GPIOA=00101101` (bit6=0).

## ST-003 — Acceptance Criteria & Scope

Scope
- Manual hardware verification of three door plunger switches (mechanical contacts) using MCP23017 `GPIOA` pins:
  - Kitchen door on `GPA3` (bit 3)
  - Family room door on `GPA4` (bit 4)
  - Basement door on `GPA7` (bit 7)
- Code under test: `hardware/mcp23017.py` (and `hardware/mygpio.py` only for INT-line debounce if needed).
- Exclude application layer (Sensor Monitor and Event Processor components) and any mocks/fakes.

Acceptance Criteria (FR7: Sensor Data Processing via hardware tests)
- Wiring per device docs; MCP `INT` -> Raspberry Pi BCM 5; common ground and power.
- After calling `MCP23017.setup()` for each location:
  - Opening the door asserts INT and `MCP23017.read_data()` shows the corresponding `GPIOA` bit toggled away from its baseline.
  - Closing the door asserts INT and `read_data()` shows the bit toggled back to the baseline.
  - Contact wiring (NO/NC) may vary; acceptance is toggle-based relative to baseline.
  - No repeated interrupts in steady state beyond Pi-side INT debounce (~50 ms).
- Tests live under `tests/hardware/mcp23017/`, marked `@pytest.mark.hardware`. Manual and excluded from default CI.

Operator Procedure (manual hardware tests)
- Prepare: Raspberry Pi with I2C enabled; MCP23017 at `0x20` on bus `1` (adjust via env if different).
- Run individually with visible prompts (`-s`):
  - Kitchen: `uv run pytest -m hardware -s tests/hardware/mcp23017/test_reed_kitchen_gpa3_manual.py`
  - Family room: `uv run pytest -m hardware -s tests/hardware/mcp23017/test_reed_family_room_gpa4_manual.py`
  - Basement: `uv run pytest -m hardware -s tests/hardware/mcp23017/test_reed_basement_gpa7_manual.py`
- Follow prompts for each: quiet for baseline, open during the first interval, close during the second interval.

Out of Scope (deferred)
- Domain entities, logging/aggregation, grouping/arming, restricted time windows.
- Any processing outside `hardware/`.
- Window reed sensors (to be scoped as a separate story; excluded from this door-focused story).

Accounting in Story
- Attach observed readings for each location (GPIOA snapshots and bit values across edges) in the PR linked to `ST-003` and `FR7`.

 - Evidence (ST-003):
   - Kitchen (GPA3 / bit 3): Baseline `GPIOA=00100101` → Open `GPIOA=00101101` → Close `GPIOA=00100101`
     Test: `tests/hardware/mcp23017/test_reed_kitchen_gpa3_manual.py`
   - Family-room (GPA4 / bit 4): Baseline `GPIOA=00101101` → Open `GPIOA=00111111` → Close `GPIOA=00101101`
     Test: `tests/hardware/mcp23017/test_reed_family_room_gpa4_manual.py`
   - Basement (GPA7 / bit 7): Baseline `GPIOA=00101101` → Open `GPIOA=10101101` → Close `GPIOA=00101101`
     Test: `tests/hardware/mcp23017/test_reed_basement_gpa7_manual.py`

- Observed (2025-08-16):
  - Kitchen (GPA3 / bit 3): Baseline `GPIOA=00101111` → Open `GPIOA=00100101` → Close `GPIOA=00101101`
  - Family-room (GPA4 / bit 4): Baseline `GPIOA=00101101` → Open `GPIOA=00111111` → Close `GPIOA=00101111`
  - Basement (GPA7 / bit 7): Baseline `GPIOA=00101101` → Open `GPIOA=10101101` → Close `GPIOA=00101101`

## ST-004 — Acceptance Criteria & Scope

Scope
- Manual hardware verification of a magnetic window reed contact on MCP23017 `GPB7` (bit 7) using the Raspberry Pi (main bedroom windows).
- Code under test: `hardware/mcp23017.py` (and `hardware/mygpio.py` only for INT-line debounce if needed).
- Exclude application layer (Sensor Monitor and Event Processor components) and any mocks/fakes.

Acceptance Criteria (FR7: Sensor Data Processing via hardware test)
- Wiring: Window reed contact output -> MCP23017 `GPB7`; MCP `INT` -> Raspberry Pi BCM 5; common ground and power per project notes.
- After calling `MCP23017.setup()`:
  - When you open the window (magnet moves away), the INT line asserts and the selected port shows a toggle of `GPIOB` bit 7 away from its baseline level.
  - When you close the window (magnet returns), the INT line asserts again and the selected port shows `GPIOB` bit 7 toggled back to the baseline.
  - Reed contact form (A/B/C) and wiring (NO/NC) can vary; treat acceptance as toggle-based relative to baseline. See `docs/devices/reed-sensor.md`.
  - No repeated interrupts in steady state beyond INT input debounce (~50 ms on the Pi side).
- Tests live under `tests/hardware/mcp23017/`, marked `@pytest.mark.hardware`. These are manual and excluded from default CI.

Operator Procedure (manual hardware test)
- Prepare: Raspberry Pi with I2C enabled; MCP23017 at address `0x20` on bus `1` (adjust via env if different).
- Run: `uv sync --group test --group hardware` then `uv run pytest -m hardware -s tests/hardware/mcp23017/test_reed_main_bedroom_gpb7_manual.py`
- Follow the test prompts: remain still for baseline capture, then open the window during the first interval, then close it during the second interval.

Out of Scope (deferred)
- Other window magnetic contacts (to be scoped as separate stories).

Accounting in Story
- Attach observed readings for `GPB7` (GPIOB snapshots and bit values across edges) in the PR linked to `ST-004` and `FR7`.

- Observed (2025-08-16): Baseline `GPIOB=01111111` (bit7=0) → Open `GPIOB=11111111` (bit7=1) → Close `GPIOB=01111111` (bit7=0).

## ST-005 — Acceptance Criteria & Scope

Scope
- Implement a minimal ACL deserializer that converts a pair of MCP23017 port values into domain `SensorReading` objects (no JSON/schema handling).
- Primary code location: `services/sensor_deserializer.py` (ACL). Outputs `SensorReading` value objects per `docs/05-domain-model.md`.
- No hardware dependencies. Unit tests only.

Acceptance Criteria (FR7: Sensor Data Processing)
- Input: `gpioa` and `gpiob` as integers in [0, 255], plus a timestamp (float seconds) and a PortMap (mapping bits to `sensor_id` and `type`).
- Behavior:
  - Validate ranges/types for `gpioa`/`gpiob`.
  - For each mapped pin, produce one `SensorReading(sensor_id: str, value: float, timestamp: float)`.
  - Normalization: bit HIGH → `1.0`, bit LOW → `0.0` for both reed and PIR (per wiring notes in `docs/07-interface-contracts.md#hardware-interfaces`).
  - Deterministic ordering of outputs (e.g., by `sensor_id`).
- Errors (typed):
  - `PayloadValidationError` for type/range issues.
  - `PortMappingError` if PortMap refers to an invalid pin key.

Test Strategy (TDD)
- Unit tests under `tests/unit/`:
  - Happy path: given `gpioa`/`gpiob` and a PortMap, returns expected list of `SensorReading` with correct values and stable ordering.
  - Range/type validation: raise `PayloadValidationError` on invalid `gpioa`/`gpiob`.
  - Port mapping edge: unknown pin key → `PortMappingError`.

Traceability
- FR: [FR7](02-product-requirements.md#fr7-sensor-data-processing)
- Architecture: aligns with `docs/06-architecture-overview.md` ACL deserializer producing `SensorReadings` for the Sensor Monitor.

## ST-006 — Acceptance Criteria & Scope

Scope
- Add schema-versioned transport ingestion for inbound payloads, producing the same `SensorReading` outputs by delegating to the ST-005 deserializer.
- Primary code location: `services/sensor_deserializer.py` (ACL) or adjacent module.
- Docs-first: define `mcp23017.reading` v0 under `docs/07-interface-contracts.md#acl-inbound-payloads`.

Acceptance Criteria (FR7: Sensor Data Processing)
- Input formats (v0):
  - JSON string or Python `dict` representing a single MCP23017 read.
  - Schema (v0):
    ```json
    { "type": "mcp23017.reading", "gpioa": 0, "gpiob": 0, "time": "2025-08-14T21:30:00Z", "schema_version": 0 }
    ```
- Behavior:
  - Strict validation: reject unknown `schema_version`, missing/extra fields, type mismatches, or out-of-range values with typed errors.
  - Time handling: convert ISO-8601 to a UNIX timestamp (float seconds) before delegating to ST-005 logic.
- Errors (typed):
  - `UnknownSchemaVersion` when `schema_version != 0`.
  - `PayloadValidationError` for missing/extra fields or type/range issues.

Test Strategy (TDD)
- Unit tests under `tests/unit/`:
  - Happy path JSON/dict inputs → correct `SensorReading`s (mock PortMap).
  - Errors: version, missing/extra fields, type/range.

Traceability
- FR: [FR7](02-product-requirements.md#fr7-sensor-data-processing)
- Interface Contracts: `docs/07-interface-contracts.md#acl-inbound-payloads` (v0) introduced in this story.

## Delivery & Traceability Conventions
- Link PRs and commits to FRs and Stories:
  - Commit message example: `feat(sensor): FR5, ST-002 - generate alarm on state change during restricted times`
  - PR title example: `FR5 ST-002 Alarm generation for armed sensors`
- Update `CHANGELOG.md` with user-visible changes per release; include FR/Story IDs.
- When a Story is merged, set Status to Done and add PR link in Notes or PR URL field if added.
- If a new capability is discovered, update `docs/02-product-requirements.md` first (docs-first), then reflect priority/story mapping here.

## Story Authoring Guidelines (TDD-aligned)

- **Testable acceptance criteria**: Each story must define observable behaviors that can be validated by automated tests.
- **Test Strategy note**: For each story, include where tests will live and how they run, choosing among:
  - Unit (default, no hardware): synthetic inputs, pure logic.
  - Integration (software-only): mocks/fakes across components.
  - Hardware-in-loop (opt-in): marked `@pytest.mark.hardware`, excluded by default.
- **Execution defaults**: Default CI/local runs execute unit/integration tests only; hardware tests require `-m hardware`.
- **Process reference**: Follow the TDD workflow and Definition of Done in `DEVELOPER_GUIDE.md`.
