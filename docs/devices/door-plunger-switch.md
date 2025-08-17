---
doc_type: device
linked_stories: [ST-002, ST-003]
linked_frs: [FR7]
---

# Door Plunger Switch — Behavior and Integration Notes

This document describes the mechanical door plunger/micro-switch contacts used on doors and how they integrate with the MCP23017 and the Raspberry Pi INT line. It consolidates observed HIL evidence for the front door and additional doors verified in ST-002 and ST-003.

## Wiring and Environment

- Plunger switch (mechanical contact) -> MCP23017 `GPIOA` pin per door circuit
  - Front door: `GPA6` (bit 6)
  - Kitchen door: `GPA3` (bit 3)
  - Family-room door: `GPA4` (bit 4)
  - Basement door: `GPA7` (bit 7)
- MCP23017 `INT` -> Raspberry Pi GPIO BCM 5 (Pi input has internal pull-down)
- I2C bus: `1` (configurable via `HSEC_I2C_BUS`)
- MCP23017 address: `0x20` (configurable via `HSEC_MCP23017_ADDR`)

## MCP23017 Configuration (from `hardware/mcp23017.py`)

- `IOCON`: INTPOL=1 (active-high INT), MIRROR=1 (INTA/INTB tied), ODR=0 (push-pull)
- `INTCONA/B=0x00` (compare-to-previous) => interrupt on any edge
- `GPINTENA/B=0xFF` (enable on all pins)
- `read_data()` reads `GPIOA` then `GPIOB` to clear INT

Rationale: any-change detection keeps tests polarity-agnostic (NO vs NC) and robust to wiring bias.

## Expected Behavior

- Baseline is captured at idle (door closed; plunger depressed).
- Opening the door (releasing the plunger) should toggle the selected `GPIOA` bit away from baseline; closing toggles it back.
- Exact logic level depends on wiring (NO vs NC) and bias. Acceptance is toggle-based relative to baseline.

## Observed Behavior (HIL evidence)

- Front door (GPA6 / bit 6):
  - Baseline `GPIOA=00101101` → `bit6=0`
  - Open `GPIOA=01101101` → `bit6=1`
  - Close `GPIOA=00101101` → `bit6=0`
  - Test: `tests/hardware/mcp23017/test_reed_gpa6_manual.py`

- Kitchen door (GPA3 / bit 3):
  - Baseline `GPIOA=00100101` → `bit3=0`
  - Open `GPIOA=00101101` → `bit3=1`
  - Close `GPIOA=00100101` → `bit3=0`
  - Test: `tests/hardware/mcp23017/test_reed_kitchen_gpa3_manual.py`

- Family-room door (GPA4 / bit 4):
  - Baseline `GPIOA=00101101` → `bit4=0`
  - Open `GPIOA=00111111` → `bit4=1`
  - Close `GPIOA=00101101` → `bit4=0`
  - Test: `tests/hardware/mcp23017/test_reed_family_room_gpa4_manual.py`

- Basement door (GPA7 / bit 7):
  - Baseline `GPIOA=00101101` → `bit7=0`
  - Open `GPIOA=10101101` → `bit7=1`
  - Close `GPIOA=00101101` → `bit7=0`
  - Test: `tests/hardware/mcp23017/test_reed_basement_gpa7_manual.py`

## Operator Procedure (summary)

- Ensure wiring as above and I2C enabled on the Pi.
- Install hardware deps: `uv sync --group test --group hardware`.
- Run individual tests with prompts (`-s`):
  - Front: `uv run pytest -m hardware -s tests/hardware/mcp23017/test_reed_gpa6_manual.py`
  - Kitchen: `uv run pytest -m hardware -s tests/hardware/mcp23017/test_reed_kitchen_gpa3_manual.py`
  - Family-room: `uv run pytest -m hardware -s tests/hardware/mcp23017/test_reed_family_room_gpa4_manual.py`
  - Basement: `uv run pytest -m hardware -s tests/hardware/mcp23017/test_reed_basement_gpa7_manual.py`
- Follow prompts: quiet for baseline, open during first interval, close during second.

## Debounce and Stability

- Pi INT line is debounced at ~50 ms (Pi side). Avoid slamming doors to minimize mechanical bounce.
- Inputs should be properly biased; MCP23017 offers internal pull-ups (no pull-downs). Configure per circuit if needed.
- Tests pre-clear pending INTs and rely on any-edge detection per configuration above.

## Traceability

- Stories: `ST-002 — Front door plunger contact change detection (GPA6)`, `ST-003 — Door plunger contact sensors verification (GPA3/GPA4/GPA7)` in `docs/03-release-plan.md`
- Functional Requirement: `FR7 — Sensor Data Processing`
- Tests: see paths listed above
