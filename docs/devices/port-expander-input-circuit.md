---
doc_type: device
linked_stories: [ST-001, ST-002, ST-003, ST-004]
linked_frs: [FR7]
---

# MCP23017 Port Expander Input Circuit — Wiring and Calculations

> Important: This document has moved to `docs/hardware/port-expander-input-circuit.md`.
> The copy below remains for continuity but the hardware section is now the source of truth.

This document describes the input circuit used to read door plunger switches, window reed sensors, and compatible PIR outputs with an MCP23017 I/O expander. It complements the per-device notes in `docs/devices/` by documenting the shared electrical design, wiring, and expected levels/currents.

- Schematic reference: `img/port expander submodle schematic.png`
- Related device notes: `docs/devices/door-plunger-switch.md`, `docs/devices/reed-sensor.md`, `docs/devices/pir-sensor.md`
- Driver references: `hardware/mcp23017.py`, `hardware/mygpio.py`

## Circuit overview

- Controller: MCP23017 at 3.3 V (`VDD = 3.3 V`, `VSS = GND`).
- Per-channel series resistor: 1 kΩ from each MCP GPIO pin to the field node (ESD/misconfig current limiting). Shown as `R1…R16`.
- Pull-ups: Two 8× resistor networks, each 10 kΩ to 3.3 V (one per 8-bit port). Shown as `R17` and `R18`. Each field node is pulled up to 3.3 V through 10 kΩ.
- Connectors:
  - Signal headers: `J1` (8 ch) and `J4` (8 ch) → field nodes after the 1 kΩ series resistors.
  - Ground headers: `J2` and `J3` → board ground for return wiring.
  - Host header: `JP1` exposes 3.3 V, GND, I2C `SCL/SDA`, and `INTA/INTB`.
- Interrupt: Only one INT line is used — Raspberry Pi `BCM5` connected to `INTB` at `JP1` pin 7. Software mirrors A/B so either port can assert INT.

## Wiring patterns

- Reed/window contacts and door plungers (dry contacts):
  - One lead to a chosen channel on `J1` or `J4` (field node).
  - Other lead to GND on `J2` or `J3`.
  - Twisted pair with one conductor as ground is recommended for long runs.
- PIR modules:
  - If the output is open-collector/drain-to-GND, wire as a dry contact (no extra parts needed).
  - If push-pull at 3.3 V logic, connect output to a channel; share ground.
  - If 5 V push-pull, do not connect directly. Use a level shifter or convert to open-drain-to-GND, or power the PIR at 3.3 V if supported.

## Logic levels (normal operation)

- The 10 kΩ pull-up biases each field node HIGH (~3.3 V) when the sensor is open.
- When the sensor closes to ground, the field node is driven LOW (~0 V).
- The MCP23017 pin sees the node through 1 kΩ. Because the MCP input is high-impedance, this 1 kΩ does not materially change the logic level in normal operation; it primarily limits fault/ESD current.
- Software default interpretation in `hardware/cli_status.py`:
  - `reed/contact`: level `1` → "open", `0` → "closed".
  - `pir`: level `1` → "motion", `0` → "no motion".

## Electrical math

Assume `VCC = 3.3 V`, `R_pullup = 10 kΩ`, sensor closes to ground (dry contact).

- Current per closed channel:  
  `I_closed = V / R = 3.3 V / 10,000 Ω = 0.00033 A = 0.33 mA`
- Power in pull-up per closed channel:  
  `P_channel = V^2 / R = (3.3 V)^2 / 10,000 Ω = 0.001089 W ≈ 1.09 mW`
- Total when n channels are closed simultaneously:  
  `I_total = n × 0.33 mA`, `P_total ≈ n × 1.09 mW`
  - Example n=5 → `I_total ≈ 1.65 mA`, `P_total ≈ 5.45 mW`
  - Worst-case n=16 → `I_total ≈ 5.28 mA`, `P_total ≈ 17.4 mW`

Notes:
- The 1 kΩ series resistor is not in the main current path from 3.3 V to GND when the contact closes; the pull-up (10 kΩ) carries that current. The 1 kΩ limits current if an MCP pin is accidentally configured as an output or during ESD events.
- With the contact open, DC current is ~0 (ignoring input leakage).

### Optional RC filtering (noise/bounce)

To tame contact bounce and long-wire noise, add a capacitor from the field node to GND.

- Time constant `τ ≈ R_pullup × C`.
- Examples:
  - `C = 0.1 µF` → `τ ≈ 10 kΩ × 0.1 µF ≈ 1 ms` (light filtering)
  - `C = 0.47 µF` → `τ ≈ 4.7 ms` (stronger filtering)

Choose `C` based on acceptable response time vs. noise environment.

## MCP23017 configuration (summary)

See `hardware/mcp23017.py` module docstring and `MCP23017.setup()`.

- `IOCON`: `MIRROR=1` (tie A/B to one INT), `ODR=0` (push-pull), `INTPOL=1` (active-high).  
  Rationale: clean, active-high INT on a single Pi line (BCM5).
- Interrupt-on-change on both ports: `INTCONA/B=0x00` (compare-to-previous), `GPINTENA/B=0xFF`.
- Reads: `read_ports()` reads `GPIOA` then `GPIOB` to clear INT when mirroring is used.
- Pulls: External 10 kΩ are already present; keep `GPPU` disabled (`0x00`) for these channels unless a specific input needs internal pull-up.

## Connector guide (high level)

- `J1`, `J4`: 8 channel signal headers, each channel includes 10 kΩ pull-up to 3.3 V and a 1 kΩ series to the MCP pin.
- `J2`, `J3`: Ground headers (return for sensors).
- `JP1`: Host header: 3.3 V, GND, I2C `SCL/SDA`, `INTA/INTB` (only `INTB` is wired to Pi `BCM5` in our build).

Exact pin→GPIO bit mapping is board-revision-specific. Verify using continuity or by toggling bits and observing the header pin with a meter/LED. Software refers to pins as `GPA0…GPA7` and `GPB0…GPB7`.

## Safety and ratings

- Per-channel dissipation (~1.09 mW) and total worst-case (~17 mW) are well within typical 1/8 W or 1/4 W resistor network ratings.
- Ensure PIR or other active modules do not drive above 3.3 V into the MCP pins. Use level shifting or open-drain coupling when in doubt.

## Traceability

- Functional Requirement: `FR7 — Sensor Data Processing` (see `docs/10-requirements-traceability.md`).
- Stories: `ST-001` (PIR), `ST-002`/`ST-003` (doors), `ST-004` (windows) in `docs/03-release-plan.md`.
