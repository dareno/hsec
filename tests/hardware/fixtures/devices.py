from __future__ import annotations

import time
from typing import Protocol

# Shared defaults for manual toggle sequences
DEFAULT_FIRST_TIMEOUT_S = 90.0
DEFAULT_SECOND_TIMEOUT_S = 90.0
DEFAULT_QUIET_LEAD_S = 3.0


class I2CBus(Protocol):
    def read_byte_data(self, i2c_addr: int, register: int) -> int: ...
    def write_byte_data(self, i2c_addr: int, register: int, value: int) -> None: ...


def wait_for_condition(cond, timeout_s: float = 2.0, poll_s: float = 0.01) -> bool:
    """Poll until cond() returns True or timeout.

    Returns True if condition met within timeout, else False.
    """
    end = time.time() + timeout_s
    while time.time() < end:
        if cond():
            return True
        time.sleep(poll_s)
    return False


# ----- Shared helpers for manual reed tests -----


def bit_at(value: int, index: int) -> int:
    """Return the bit at index from an 8-bit value."""
    return (value >> index) & 0x1


def _preclear_int(dev, pi_int_button, max_iter: int = 20) -> None:
    """Clear any pending INT by reading until line deasserts or max_iter reached."""
    for _ in range(max_iter):
        if not getattr(pi_int_button, "is_pressed", False):
            break
        # Read both ports to clear interrupt regardless of source
        _ = dev.read_ports()
        time.sleep(0.05)


def _read_port(dev, port: str) -> int:
    """Read the selected MCP23017 port value.

    Uses driver-provided APIs.
    """
    p = port.upper()
    if p not in ("A", "B"):
        raise ValueError(f"Unsupported port '{port}', expected 'A' or 'B'.")
    return dev.read_port(p)


def _configure_input_pullup_and_int(
    dev, port: str, bit_index: int, *, use_internal_pullup: bool = False
) -> None:
    """Ensure the selected pin is input and enable its interrupt; optionally enable internal pull-up.

    When external bias exists (per schematic: 10k pull-up → 1k series → MCP pin → reed to GND),
    keep the MCP internal pull-up disabled (default). Set `use_internal_pullup=True` only when
    no external bias is present and the line might float during HIL.
    """
    mask = 1 << bit_index
    p = port.upper()
    if p == "A":
        IODIR = 0x00
        GPPU = 0x0C
        GPINTEN = 0x04
    elif p == "B":
        IODIR = 0x01
        GPPU = 0x0D
        GPINTEN = 0x05
    else:
        raise ValueError("port must be 'A' or 'B'")

    addr = dev.device_address
    bus: I2CBus = dev.bus  # type: ignore

    # Set as input (bit=1)
    iodir = bus.read_byte_data(addr, IODIR)
    iodir |= mask
    bus.write_byte_data(addr, IODIR, iodir)

    # Optionally enable internal pull-up on this bit
    gppu = bus.read_byte_data(addr, GPPU)
    if use_internal_pullup:
        gppu |= mask
        bus.write_byte_data(addr, GPPU, gppu)

    # Ensure interrupt is enabled on this bit (keep others as-is)
    gpinten = bus.read_byte_data(addr, GPINTEN)
    gpinten |= mask
    bus.write_byte_data(addr, GPINTEN, gpinten)

    # Clear any pending INT by reading both ports
    _ = dev.read_ports()
    print(
        f"[HIL] Configured {p} bit{bit_index}: IODIR=0x{iodir:02x}, GPPU=0x{gppu:02x}, GPINTEN=0x{gpinten:02x}"
    )


def _run_toggle_sequence(
    dev,
    pi_int_button,
    *,
    port: str,
    bit_index: int,
    location: str,
    phase1_label: str,
    phase2_label: str,
    first_timeout_s: float,
    second_timeout_s: float,
    quiet_lead_s: float | None = None,
) -> None:
    """Generic manual sequence verifying bit toggles away from baseline then back.

    - Optional quiet lead before baseline capture
    - Phase 1: expect toggle away from baseline within first_timeout_s
    - Phase 2: expect toggle back to baseline within second_timeout_s
    """
    if quiet_lead_s and quiet_lead_s > 0:
        print(
            f"[HIL] Preparing baseline for {location}: ensure area is quiet for ~{int(quiet_lead_s)}s…"
        )
        time.sleep(quiet_lead_s)
    else:
        print(f"[HIL] Preparing baseline for {location}: capturing idle state now…")

    _preclear_int(dev, pi_int_button)
    _configure_input_pullup_and_int(dev, port, bit_index)
    value0 = _read_port(dev, port)
    baseline = bit_at(value0, bit_index)
    gpio_label = "GPIOA" if port.upper() == "A" else "GPIOB"
    print(
        f"[HIL] Baseline captured {gpio_label}={value0:08b} (bit{bit_index}={baseline})."
    )

    print(
        f"[HIL] {phase1_label} the {location} now; waiting up to {int(first_timeout_s)}s for edge."
    )
    first_deadline = time.time() + first_timeout_s
    phase1_seen = False
    while time.time() < first_deadline:
        _ = pi_int_button.wait_for_press(timeout=0.05)
        v = _read_port(dev, port)
        b = bit_at(v, bit_index)
        if b != baseline:
            print(
                f"[HIL] {phase1_label} detected {gpio_label}={v:08b} (bit{bit_index}={b})."
            )
            phase1_seen = True
            break
    if not phase1_seen:
        raise AssertionError(
            f"Timed out waiting for {phase1_label} edge on bit{bit_index} at {location} (toggle from baseline)"
        )

    print(
        f"[HIL] Now {phase2_label} the {location} and hold steady; waiting up to {int(second_timeout_s)}s for edge."
    )
    second_deadline = time.time() + second_timeout_s
    while time.time() < second_deadline:
        _ = pi_int_button.wait_for_press(timeout=0.05)
        v2 = _read_port(dev, port)
        b2 = bit_at(v2, bit_index)
        if b2 == baseline:
            print(
                f"[HIL] {phase2_label} detected {gpio_label}={v2:08b} (bit{bit_index}={b2})."
            )
            break
    else:
        raise AssertionError(
            f"Timed out waiting for {phase2_label} edge on bit{bit_index} at {location} (toggle back to baseline)"
        )

    print(
        f"[HIL] Success: Observed bit{bit_index} toggle on {phase1_label} and toggle back on {phase2_label} for {location}."
    )


def run_reed_edge_sequence(
    dev,
    pi_int_button,
    bit_index: int,
    location: str,
    port: str = "A",
    open_timeout_s: float = DEFAULT_FIRST_TIMEOUT_S,
    close_timeout_s: float = DEFAULT_SECOND_TIMEOUT_S,
    quiet_lead_s: float = DEFAULT_QUIET_LEAD_S,
) -> None:
    """Manual reed open/close sequence verifying toggle vs baseline on given port/bit.

    quiet_lead_s provides a short calm period before baseline capture; harmless for reed,
    useful when operator motion might disturb nearby sensors.
    """
    _run_toggle_sequence(
        dev,
        pi_int_button,
        port=port,
        bit_index=bit_index,
        location=location,
        phase1_label="OPEN",
        phase2_label="CLOSE",
        first_timeout_s=open_timeout_s,
        second_timeout_s=close_timeout_s,
        quiet_lead_s=quiet_lead_s,
    )


def run_pir_motion_sequence(
    dev,
    pi_int_button,
    bit_index: int,
    location: str,
    port: str = "A",
    motion_timeout_s: float = DEFAULT_FIRST_TIMEOUT_S,
    settle_timeout_s: float = DEFAULT_SECOND_TIMEOUT_S,
    quiet_lead_s: float = DEFAULT_QUIET_LEAD_S,
) -> None:
    """Manual PIR motion/settle sequence verifying toggle vs baseline (no countdown)."""
    _run_toggle_sequence(
        dev,
        pi_int_button,
        port=port,
        bit_index=bit_index,
        location=location,
        phase1_label="MOTION",
        phase2_label="SETTLE",
        first_timeout_s=motion_timeout_s,
        second_timeout_s=settle_timeout_s,
        quiet_lead_s=quiet_lead_s,
    )
