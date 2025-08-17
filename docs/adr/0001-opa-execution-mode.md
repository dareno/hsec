# ADR 0001: OPA Execution Mode

- Status: Accepted
- Date: 2025-08-14
- Decision Makers: Project Maintainer

## Context
The Alarm business logic should be expressed as policy-as-code to keep domain rules decoupled from I/O. Options for executing Open Policy Agent (OPA) include:
- Embedded WASM in-process (load compiled bundle and evaluate locally)
- Local HTTP sidecar server (Docker container on the Raspberry Pi)
- Remote OPA service (not desired for offline-first)

Key constraints and preferences:
- Offline-first; all processing local to the Pi.
- Simple operations; easy hot-reload of policies during development.
- Clear separation of concerns per bounded context.

## Decision
Run OPA as a local HTTP sidecar in Docker on the Raspberry Pi. Mount policies read-only from a host directory. Query the package `hsec/alarm` to retrieve both `allow` and `reasons` in one response.

- Endpoint: `POST http://127.0.0.1:8181/v1/data/hsec/alarm`
- Policy location (recommended): `policies/` with subfolders per context (e.g., `policies/alarm/`).
- Input includes `schema_version: 0` to allow evolution.

## Rationale
- Decoupling: policies can be updated independently of Python deployment.
- Simplicity: no language-specific WASM runtime wiring; familiar HTTP interface.
- Observability: OPA exposes useful diagnostics and supports `opa test` for unit testing.
- Flexibility: can later switch to WASM if required without changing policy language.

## Consequences
- Small local HTTP hop in the hot path; acceptable for 1–2s end-to-end latency target.
- Requires Docker on the Pi and appropriate OPA image for Pi’s architecture.
- Policies must be mounted or bundled into the container; establish a deployment convention.

## Alternatives Considered
- Embedded WASM:
  - Pros: lowest latency, no Docker.
  - Cons: more integration work; rebuild cycle for policy changes; less operational isolation.
- Remote OPA service:
  - Pros: centralized management.
  - Cons: violates offline-first and increases failure modes.

## Follow-ups
- Keep input schema unfrozen while early; increment `schema_version` as it stabilizes.
- Add golden tests that serialize real decision inputs from the Event Processor component (planned).
- Consider graceful fallback behavior if OPA is unavailable (e.g., deny-by-default with clear logging).
