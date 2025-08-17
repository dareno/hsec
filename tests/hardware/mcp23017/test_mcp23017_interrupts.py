import time

import pytest

pytestmark = pytest.mark.hardware


def _read_gpioa(i2c_bus, addr: int) -> int:
    return i2c_bus.read_byte_data(addr, 0x12)  # GPIOA


def _read_gpiob(i2c_bus, addr: int) -> int:
    return i2c_bus.read_byte_data(addr, 0x13)  # GPIOB


def _write_reg(i2c_bus, addr: int, reg: int, val: int) -> None:
    i2c_bus.write_byte_data(addr, reg, val)


def _set_bits(value: int, mask: int) -> int:
    return value | mask


def _clear_bits(value: int, mask: int) -> int:
    return value & (~mask & 0xFF)


def test_interrupt_asserts_and_clears_on_loopback_gpio(
    i2c_bus, hardware_config, pi_int_button
):
    """
    Validate INT asserts on GPIOA0 transitions and clears after read_data().

    Wiring assumptions:
    - Pi BCM17 is wired to MCP23017 GPA0 via your resistor network.
    - INT line from MCP23017 is wired to Pi BCM5 (Button fixture with
      pull_up=False, 50ms debounce).

    Emulation of door sensor:
    - Drive BCM17 HIGH => junction pulled HIGH (door open).
    - Drive BCM17 LOW  => junction pulled LOW  (door closed).
    """
    from gpiozero import DigitalOutputDevice

    from hardware.mcp23017 import MCP23017
    from tests.hardware.fixtures.devices import wait_for_condition

    BCM_LOOPBACK = 17
    MCP_ADDR = hardware_config.mcp23017_addr

    dev = MCP23017(bus=i2c_bus, device_address=MCP_ADDR)

    # Ensure configuration as per project setup
    dev.setup()

    # Configure GPA0 as input; ensure internal pull-up disabled (external
    # pull-up exists)
    IODIRA = 0x00
    GPPUA = 0x0C
    GPINTENA = 0x04
    GPINTENB = 0x05
    iodira = i2c_bus.read_byte_data(MCP_ADDR, IODIRA)
    gppua = i2c_bus.read_byte_data(MCP_ADDR, GPPUA)
    iodira = _set_bits(iodira, 0x01)  # GPA0 as input
    gppua = _clear_bits(gppua, 0x01)  # disable internal pull-up on GPA0
    _write_reg(i2c_bus, MCP_ADDR, IODIRA, iodira)
    _write_reg(i2c_bus, MCP_ADDR, GPPUA, gppua)
    # Restrict interrupts to GPA0 only; disable all Port B interrupts
    _write_reg(i2c_bus, MCP_ADDR, GPINTENA, 0x01)
    _write_reg(i2c_bus, MCP_ADDR, GPINTENB, 0x00)

    # Clear any pending interrupts by reading both ports
    _ = _read_gpioa(i2c_bus, MCP_ADDR)
    _ = _read_gpiob(i2c_bus, MCP_ADDR)

    # Loopback driver on Pi
    driver = DigitalOutputDevice(BCM_LOOPBACK, active_high=True, initial_value=True)
    try:
        # Start in 'door open' = HIGH
        driver.on()
        time.sleep(0.05)
        gpioa = _read_gpioa(i2c_bus, MCP_ADDR)
        assert (gpioa & 0x01) == 0x01

        # Transition to 'door closed' = LOW => expect INT asserted (active-high)
        driver.off()
        assert wait_for_condition(lambda: pi_int_button.is_pressed, timeout_s=1.0)

        # read_data() should clear INT
        _ = dev.read_data()
        # After debounce, INT should deassert
        assert wait_for_condition(lambda: not pi_int_button.is_pressed, timeout_s=1.0)
        gpioa = _read_gpioa(i2c_bus, MCP_ADDR)
        assert (gpioa & 0x01) == 0x00

        # Transition back to 'door open' = HIGH => expect another INT
        driver.on()
        assert wait_for_condition(lambda: pi_int_button.is_pressed, timeout_s=1.0)
        _ = dev.read_data()
        assert wait_for_condition(lambda: not pi_int_button.is_pressed, timeout_s=1.0)
        gpioa = _read_gpioa(i2c_bus, MCP_ADDR)
        assert (gpioa & 0x01) == 0x01
    finally:
        try:
            driver.close()
        except Exception:
            pass


def test_intcap_latches_state_and_clear_works(i2c_bus, hardware_config, pi_int_button):
    """
    Conditions under test:
    - INTCAP registers (0x10/0x11) latch the PORT values at the moment an
      interrupt occurs.
    - INT line asserts (active-high) on any change of GPA0 (configured via setup()).
    - Reading GPIOA/GPIOB (or INTCAP then GPIO) clears the interrupt and
      deasserts INT.

    Pass criteria:
    - On HIGH->LOW transition at GPA0, `INTCAPA & 0x01 == 0` and INT is asserted,
      then clears after readback.
    - On LOW->HIGH transition at GPA0, `INTCAPA & 0x01 == 1` and INT is asserted,
      then clears after readback.

    Failure indicates potential issues in wiring, debounce, register programming,
    or INT clear logic.
    """
    from gpiozero import DigitalOutputDevice

    from hardware.mcp23017 import MCP23017
    from tests.hardware.fixtures.devices import wait_for_condition

    BCM_LOOPBACK = 17
    MCP_ADDR = hardware_config.mcp23017_addr

    dev = MCP23017(bus=i2c_bus, device_address=MCP_ADDR)
    dev.setup()

    # Registers
    IODIRA = 0x00
    GPPUA = 0x0C
    GPINTENA = 0x04
    GPINTENB = 0x05
    INTCAPA = 0x10
    # Ensure GPA0 is input and internal pull-up disabled (external pull-up
    # present)
    iodira = i2c_bus.read_byte_data(MCP_ADDR, IODIRA)
    gppua = i2c_bus.read_byte_data(MCP_ADDR, GPPUA)
    iodira = _set_bits(iodira, 0x01)
    gppua = _clear_bits(gppua, 0x01)
    _write_reg(i2c_bus, MCP_ADDR, IODIRA, iodira)
    _write_reg(i2c_bus, MCP_ADDR, GPPUA, gppua)
    # Restrict interrupts to GPA0 only; disable all Port B interrupts
    _write_reg(i2c_bus, MCP_ADDR, GPINTENA, 0x01)
    _write_reg(i2c_bus, MCP_ADDR, GPINTENB, 0x00)

    # Clear any pending INT
    _ = _read_gpioa(i2c_bus, MCP_ADDR)
    _ = _read_gpiob(i2c_bus, MCP_ADDR)

    driver = DigitalOutputDevice(BCM_LOOPBACK, active_high=True, initial_value=True)
    try:
        # Ensure starting HIGH (door open)
        driver.on()
        time.sleep(0.05)

        # 1) HIGH -> LOW transition
        driver.off()
        assert wait_for_condition(lambda: pi_int_button.is_pressed, timeout_s=1.0), (
            "INT did not assert on HIGH->LOW"
        )
        latched = i2c_bus.read_byte_data(MCP_ADDR, INTCAPA)
        assert (latched & 0x01) == 0x00, (
            f"INTCAPA expected bit0=0 on falling edge, got {latched:#04x}"
        )
        # Clear INT by reading GPIO
        _ = dev.read_data()
        assert wait_for_condition(
            lambda: not pi_int_button.is_pressed, timeout_s=1.0
        ), "INT did not deassert after clear"

        # 2) LOW -> HIGH transition
        driver.on()
        assert wait_for_condition(lambda: pi_int_button.is_pressed, timeout_s=1.0), (
            "INT did not assert on LOW->HIGH"
        )
        latched = i2c_bus.read_byte_data(MCP_ADDR, INTCAPA)
        assert (latched & 0x01) == 0x01, (
            f"INTCAPA expected bit0=1 on rising edge, got {latched:#04x}"
        )
        # Clear INT again
        _ = dev.read_data()
        assert wait_for_condition(
            lambda: not pi_int_button.is_pressed, timeout_s=1.0
        ), "INT did not deassert after clear"
    finally:
        try:
            driver.close()
        except Exception:
            pass
