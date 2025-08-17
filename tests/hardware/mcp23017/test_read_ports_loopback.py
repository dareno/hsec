import time

import pytest

pytestmark = pytest.mark.hardware


def _set_bits(value: int, mask: int) -> int:
    return value | mask


def _clear_bits(value: int, mask: int) -> int:
    return value & (~mask & 0xFF)


def _read_gpioa(i2c_bus, addr: int) -> int:
    return i2c_bus.read_byte_data(addr, 0x12)  # GPIOA


def _read_gpiob(i2c_bus, addr: int) -> int:
    return i2c_bus.read_byte_data(addr, 0x13)  # GPIOB


def _write_reg(i2c_bus, addr: int, reg: int, val: int) -> None:
    i2c_bus.write_byte_data(addr, reg, val)


def _common_setup(dev, i2c_bus, addr: int):
    """Configure GPA0 input, disable its internal pull-up, enable INT only on GPA0, disable PortB INTs.

    Mirrors the configuration pattern from test_mcp23017_interrupts.py.
    """
    # Ensure configuration as per project setup
    dev.setup()

    # Registers
    IODIRA = 0x00
    GPPUA = 0x0C
    GPINTENA = 0x04
    GPINTENB = 0x05

    # Ensure GPA0 is input and internal pull-up disabled (external pull-up present)
    iodira = i2c_bus.read_byte_data(addr, IODIRA)
    gppua = i2c_bus.read_byte_data(addr, GPPUA)
    iodira = _set_bits(iodira, 0x01)  # GPA0 as input
    gppua = _clear_bits(gppua, 0x01)  # disable internal pull-up on GPA0
    _write_reg(i2c_bus, addr, IODIRA, iodira)
    _write_reg(i2c_bus, addr, GPPUA, gppua)

    # Restrict interrupts to GPA0 only; disable all Port B interrupts
    _write_reg(i2c_bus, addr, GPINTENA, 0x01)
    _write_reg(i2c_bus, addr, GPINTENB, 0x00)

    # Clear any pending interrupts by reading both ports
    _ = _read_gpioa(i2c_bus, addr)
    _ = _read_gpiob(i2c_bus, addr)


def test_read_ports_clears_int_on_gpa0_loopback(
    i2c_bus, hardware_config, pi_int_button
):
    from gpiozero import DigitalOutputDevice
    from hardware.mcp23017 import MCP23017
    from tests.hardware.fixtures.devices import wait_for_condition

    BCM_LOOPBACK = 17
    addr = hardware_config.mcp23017_addr

    dev = MCP23017(bus=i2c_bus, device_address=addr)
    _common_setup(dev, i2c_bus, addr)

    driver = DigitalOutputDevice(BCM_LOOPBACK, active_high=True, initial_value=True)
    try:
        # Confirm starting HIGH
        time.sleep(0.05)
        a0, b0 = dev.read_ports()
        assert (a0 & 0x01) == 0x01

        # Cause falling edge on GPA0 -> expect INT
        driver.off()
        assert wait_for_condition(lambda: pi_int_button.is_pressed, timeout_s=1.0)

        # read_ports() should clear INT and return new A,B values
        a1, b1 = dev.read_ports()
        assert wait_for_condition(lambda: not pi_int_button.is_pressed, timeout_s=1.0)
        assert (a1 & 0x01) == 0x00
        # b value is not controlled here; just assert it's a byte
        assert 0 <= b1 <= 0xFF

        # Rising edge -> expect INT again
        driver.on()
        assert wait_for_condition(lambda: pi_int_button.is_pressed, timeout_s=1.0)
        a2, _b2 = dev.read_ports()
        assert wait_for_condition(lambda: not pi_int_button.is_pressed, timeout_s=1.0)
        assert (a2 & 0x01) == 0x01
    finally:
        try:
            driver.close()
        except Exception:
            pass


def test_read_port_A_clears_int(i2c_bus, hardware_config, pi_int_button):
    from gpiozero import DigitalOutputDevice
    from hardware.mcp23017 import MCP23017
    from tests.hardware.fixtures.devices import wait_for_condition

    BCM_LOOPBACK = 17
    addr = hardware_config.mcp23017_addr

    dev = MCP23017(bus=i2c_bus, device_address=addr)
    _common_setup(dev, i2c_bus, addr)

    driver = DigitalOutputDevice(BCM_LOOPBACK, active_high=True, initial_value=True)
    try:
        time.sleep(0.05)
        # Falling edge -> expect INT
        driver.off()
        assert wait_for_condition(lambda: pi_int_button.is_pressed, timeout_s=1.0)

        # read_port('A') clears and returns A value
        a_val = dev.read_port("A")
        assert wait_for_condition(lambda: not pi_int_button.is_pressed, timeout_s=1.0)
        assert (a_val & 0x01) == 0x00

        # Rising edge -> expect INT again
        driver.on()
        assert wait_for_condition(lambda: pi_int_button.is_pressed, timeout_s=1.0)
        a_val2 = dev.read_port("A")
        assert wait_for_condition(lambda: not pi_int_button.is_pressed, timeout_s=1.0)
        assert (a_val2 & 0x01) == 0x01
    finally:
        try:
            driver.close()
        except Exception:
            pass


def test_read_port_B_clears_int_even_when_A_triggered(
    i2c_bus, hardware_config, pi_int_button
):
    from gpiozero import DigitalOutputDevice
    from hardware.mcp23017 import MCP23017
    from tests.hardware.fixtures.devices import wait_for_condition

    BCM_LOOPBACK = 17
    addr = hardware_config.mcp23017_addr

    dev = MCP23017(bus=i2c_bus, device_address=addr)
    _common_setup(dev, i2c_bus, addr)

    driver = DigitalOutputDevice(BCM_LOOPBACK, active_high=True, initial_value=True)
    try:
        time.sleep(0.05)
        # Falling edge -> expect INT
        driver.off()
        assert wait_for_condition(lambda: pi_int_button.is_pressed, timeout_s=1.0)

        # read_port('B') should still clear INT due to MIRROR + read of both ports
        b_val = dev.read_port("B")
        assert wait_for_condition(lambda: not pi_int_button.is_pressed, timeout_s=1.0)
        assert 0 <= b_val <= 0xFF

        # Rising edge -> expect INT
        driver.on()
        assert wait_for_condition(lambda: pi_int_button.is_pressed, timeout_s=1.0)
        b_val2 = dev.read_port("B")
        assert wait_for_condition(lambda: not pi_int_button.is_pressed, timeout_s=1.0)
        assert 0 <= b_val2 <= 0xFF
    finally:
        try:
            driver.close()
        except Exception:
            pass
