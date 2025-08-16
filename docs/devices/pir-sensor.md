---
doc_type: device
linked_stories: [ST-001]
linked_frs: [FR7]
---
# PIR Sensor — Observed Behavior and Integration Notes

This document captures how our PIR motion sensor behaves when connected to the MCP23017 (`GPA1`) and Raspberry Pi INT line as exercised by the manual HIL test `tests/hardware/mcp23017/test_pir_gpa1_manual.py`.

## Wiring and Environment

- PIR output -> MCP23017 `GPA1`
- MCP23017 `INT` -> Raspberry Pi GPIO BCM 5 (Pi input has internal pull-down)
- I2C bus: `1` (configurable via `HSEC_I2C_BUS`)
- MCP23017 address: `0x20` (configurable via `HSEC_MCP23017_ADDR`)

## MCP23017 Configuration (from `hardware/mcp23017.py`)

- `IOCON`: INTPOL=1 (active-high INT), MIRROR=1 (INTA/INTB tied), ODR=0 (push-pull)
- `INTCONA/B=0x00` (compare-to-previous) => interrupt on any edge
- `GPINTENA/B=0xFF` (enable on all pins)
- `read_data()` reads `GPIOA` then `GPIOB` to clear INT

Rationale: simplest any-change detection while we learn sensor polarity. Mirrored, active-high, push-pull INT provides a clean Pi interrupt without external pull-ups.

## Observed Behavior (our module)

From a passing run with full output (`-s`):

- Baseline (idle, no motion): `GPIOA=00101101` → `GPA1=0`
- Motion (walk in front): `GPIOA=00101111` → `GPA1=1`
- Settle (step away, wait): `GPIOA=00101101` → `GPA1=0`

Interpretation:
- This PIR module idles LOW on `GPA1` and goes HIGH on motion; returns LOW after its hold time.
- Other bits may be HIGH depending on wiring/pulls; the test keys on `GPA1` only.

Note: PIR modules vary in polarity and hold times. Treat the “toggle away from baseline, then toggle back” as the acceptance, not absolute levels. If using a module with opposite polarity, the edge-based test remains valid.

## Operator Procedure (summary)

- Ensure wiring as above and I2C enabled on the Pi.
- Run: `uv sync --group test --group hardware` then `uv run pytest -m hardware -s tests/hardware/mcp23017/`
- Follow prompts: quiet for baseline, countdown to motion window (walk in front), then countdown to settle window (step away).

## Debounce and Stability

- Pi INT line may be debounced at ~50 ms (on the Pi side) to avoid spurious triggers.
- MCP23017 GPIO inputs should be properly biased; internal pull-ups (`GPPU`) exist but no pull-downs.
- Our test pre-clears any pending INTs and captures a baseline before waiting for events.

## Traceability

- Story: `ST-001 — PIR change detection` in `docs/02-release-plan.md`
- Functional Requirement: `FR7 — Sensor Data Processing`
- Test: `tests/hardware/mcp23017/test_pir_gpa1_manual.py`
