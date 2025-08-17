---
doc_type: device
linked_stories: [ST-004]
linked_frs: [FR7]
---

# Window Magnetic Reed Sensor — Behavior and Integration Notes

This document outlines how a two-piece magnetic window contact (reed switch + magnet) integrates with the MCP23017 and the Raspberry Pi INT line. It serves as the basis for upcoming window HIL tests.

## Wiring and Environment

- Reed switch (window contact) -> MCP23017 `GPIO` pin on port A or B
  - Main bedroom windows: `GPB7` (bit 7)
- MCP23017 `INT` -> Raspberry Pi GPIO BCM 5 (Pi input has internal pull-down)
- I2C bus: `1` (configurable via `HSEC_I2C_BUS`)
- MCP23017 address: `0x20` (configurable via `HSEC_MCP23017_ADDR`)

## MCP23017 Configuration (from `hardware/mcp23017.py`)

- `IOCON`: INTPOL=1 (active-high INT), MIRROR=1 (INTA/INTB tied), ODR=0 (push-pull)
- `INTCONA/B=0x00` (compare-to-previous) => interrupt on any edge
- `GPINTENA/B=0xFF` (enable on all pins)
- Driver API for reads:
  - `read_ports()` -> `(gpioa, gpiob)`: reads both ports (A then B) to clear interrupts reliably when MIRROR is used.
  - `read_port('A'|'B')` -> `int`: reads the selected port (internally reads both to clear INT).
  - `read_data()` (deprecated): returns `GPIOA`; preserved for backward compatibility.

Rationale: any-change detection keeps the test polarity-agnostic (NO vs NC).

## Expected Behavior

- Baseline is captured at idle (window closed, magnet near the reed).
- Opening the window (magnet moves away) toggles the selected port/bit away from the baseline; closing toggles it back.
- Exact logic level depends on reed form (A/B/C) and circuit bias. Treat acceptance as toggle-based relative to baseline.

## Observed Behavior

Observed on 2025-08-16 for the main bedroom windows on `GPB7` (story `ST-004`).

- Baseline at idle: `GPIOB` bit7 = 0
- Opening window: `GPIOB` bit7 toggles to 1
- Closing window: `GPIOB` bit7 returns to 0
- Hardware bias: external 10k pull-up to 3.3V per schematic (`img/port expander submodle schematic.png`). Recommended: disable MCP internal pull-up on this line when external bias exists.
- Note: The captured HIL run below enabled the MCP internal pull-up on B7 via the test fixture; polarity still matched the external pull-up circuit. Future runs should leave `GPPU` cleared on B7.

Verification (HIL) run and output:

```text
$ uv run pytest -s -q -m hardware tests/hardware/mcp23017/test_reed_main_bedroom_gpb7_manual.py
[HIL] Preparing baseline for main bedroom windows (GPB7): capturing idle state now…
[HIL] Configured B bit7: IODIR=0xff, GPPU=0x80, GPINTEN=0xff
[HIL] Baseline captured GPIOB=01111111 (bit7=0).
[HIL] OPEN the main bedroom windows (GPB7) now; waiting up to 120s for edge.
[HIL] OPEN detected GPIOB=11111111 (bit7=1).
[HIL] Now CLOSE the main bedroom windows (GPB7) and hold steady; waiting up to 120s for edge.
[HIL] CLOSE detected GPIOB=01111111 (bit7=0).
[HIL] Success: Observed bit7 toggle on OPEN and toggle back on CLOSE for main bedroom windows (GPB7).
```

## Operator Procedure (summary)

- Ensure wiring as above and I2C enabled on the Pi.
- Install hardware deps: `uv sync --group test --group hardware`.
- Run the main bedroom windows test with prompts:
  - `uv run pytest -m hardware -s tests/hardware/mcp23017/test_reed_main_bedroom_gpb7_manual.py`
  - Follow prompts: quiet for baseline, open during first interval, close during second.

## Debounce and Stability

- Pi INT line is debounced at ~50 ms (Pi side). Avoid door slamming to minimize bounce.
- Inputs should be properly biased; MCP23017 offers internal pull-ups (no pull-downs). Configure per circuit if needed.
- Test pre-clears pending INTs and uses edge detection on the selected `GPIO` port/pin.

## Traceability

- Functional Requirement: `FR7 — Sensor Data Processing`
- Story: `ST-004 — Window magnetic reed change detection (GPB7, main bedroom windows)` in `docs/03-release-plan.md`
