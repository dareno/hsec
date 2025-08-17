---
doc_type: traceability
upstream:
  - 02-product-requirements.md
  - 06-architecture-overview.md
---

# Requirements Traceability

Maps PRD Functional Requirements (FR) to implementing components and references.
Note: FR definitions live in `docs/02-product-requirements.md`; this table is derivative and does not restate requirements.

| Requirement (FR)                                                   | Implemented By (Components)                               | Source (PRD)                                            | References (Specs/Code)                              |
|:-------------------------------------------------------------------|:----------------------------------------------------------|:--------------------------------------------------------|:-----------------------------------------------------|
| [FR1](02-product-requirements.md#fr1-sensor-grouping)              | TBD: configuration store (file-backed)                    | [§FR1](02-product-requirements.md#fr1-sensor-grouping)  | Sensor Monitor (planned); Event Processor (planned)  |
| [FR2](02-product-requirements.md#fr2-sensor-capacity)              | `hardware/mcp23017.py`                                     | [§FR2](02-product-requirements.md#fr2-sensor-capacity)  | `hardware/mcp23017.py`; PRD constraints              |
| [FR3](02-product-requirements.md#fr3-arming-preconditions)         | Event Processor (planned)                                  | [§FR3](02-product-requirements.md#fr3-arming-preconditions) | Event Processor (planned)                             |
| [FR4](02-product-requirements.md#fr4-arming-state-persistence)     | TBD: configuration store (`SecurityConfig`)                | [§FR4](02-product-requirements.md#fr4-arming-state-persistence) | `05-domain-model.md`                                   |
| [FR5](02-product-requirements.md#fr5-alarm-generation)             | Event Processor (planned); `policies/alarm/policy.rego`    | [§FR5](02-product-requirements.md#fr5-alarm-generation) | Event Processor (planned); `policies/alarm/`          |
| [FR6](02-product-requirements.md#fr6-alarm-context)                | Event Processor (planned)                                  | [§FR6](02-product-requirements.md#fr6-alarm-context)    | Event Processor (planned); `07-interface-contracts.md` |
| [FR7](02-product-requirements.md#fr7-sensor-data-processing)       | `hardware/mcp23017.py`; Sensor Monitor (planned)           | [§FR7](02-product-requirements.md#fr7-sensor-data-processing) | `hardware/mcp23017.py`; Sensor Monitor (planned)      |
| [FR8](02-product-requirements.md#fr8-state-tracking)               | TBD: state repository; Event Processor (planned)           | [§FR8](02-product-requirements.md#fr8-state-tracking)   | Event Processor (planned); Sensor Monitor (planned)   |
| [FR9](02-product-requirements.md#fr9-contextual-evaluation)        | TBD: security context provider; Event Processor (planned)  | [§FR9](02-product-requirements.md#fr9-contextual-evaluation) | Event Processor (planned); OPA input schema           |
| [FR10](02-product-requirements.md#fr10-user-defined-time-windows)  | TBD: configuration store (`TimeWindow`); policies          | [§FR10](02-product-requirements.md#fr10-user-defined-time-windows) | `05-domain-model.md`; OPA policy                       |

Notes:
- Interface payloads and versions: `docs/07-interface-contracts.md` (schema_version=0).
- For detailed runtime behavior see `docs/08-runtime-flows.md`.
