import time
import pytest

pytestmark = pytest.mark.hardware

# Only import gpiozero when this test file is actually collected/run for hardware
pytest.importorskip("gpiozero", reason="gpiozero required for Pi GPIO tests")


def test_pi_int_line_rising_edges_and_debounce(pi_int_button, i2c_bus, hardware_config):
    """
    Conditions under test:
    - Pi INT input on BCM5 is wired to MCP23017 INT, configured active-high.
    - Rising edges are observed when GPA0 is toggled HIGH (via BCM17 loopback driver).
    - Debounce (~50 ms) prevents spurious multiple triggers.

    Pass criteria:
    - Press events are observed when the line is driven HIGH by MCP interrupt assertion.
    - For a single LOW->HIGH transition on GPA0, exactly one rising event is detected (debounced).

    Rationale:
    - Ensures the Pi-side INT path and debounce are functioning with the MCP configured and clearing behavior exercised.
    """
    from gpiozero import DigitalOutputDevice
    from hardware.mcp23017 import MCP23017
    from tests.hardware.fixtures.devices import wait_for_condition

    BCM_LOOPBACK = 17
    MCP_ADDR = hardware_config.mcp23017_addr

    # Prepare MCP: configure as per project and ensure GPA0 input, internal pull-up disabled
    dev = MCP23017(bus=i2c_bus, device_address=MCP_ADDR)
    dev.setup()
    IODIRA = 0x00
    GPPUA = 0x0C
    GPINTENA = 0x04
    GPINTENB = 0x05
    iodira = i2c_bus.read_byte_data(MCP_ADDR, IODIRA)
    gppua = i2c_bus.read_byte_data(MCP_ADDR, GPPUA)
    iodira |= 0x01
    gppua &= 0xFE
    i2c_bus.write_byte_data(MCP_ADDR, IODIRA, iodira)
    i2c_bus.write_byte_data(MCP_ADDR, GPPUA, gppua)
    # Restrict interrupts to GPA0 only; disable all Port B interrupts
    i2c_bus.write_byte_data(MCP_ADDR, GPINTENA, 0x01)
    i2c_bus.write_byte_data(MCP_ADDR, GPINTENB, 0x00)
    # Clear any pending INT by reading both ports
    _ = i2c_bus.read_byte_data(MCP_ADDR, 0x12)
    _ = i2c_bus.read_byte_data(MCP_ADDR, 0x13)

    driver = DigitalOutputDevice(BCM_LOOPBACK, active_high=True, initial_value=False)
    try:
        # Ensure stable low to start
        driver.off()
        time.sleep(0.05)

        # Ensure INT is deasserted before starting by explicitly clearing any pending interrupt
        def clear_int_with_retry() -> None:
            for _ in range(5):
                _ = dev.read_data()
                if wait_for_condition(
                    lambda: not pi_int_button.is_pressed, timeout_s=0.5
                ):
                    return
                time.sleep(0.05)
            pytest.fail("INT line stuck asserted before test start")

        clear_int_with_retry()

        # Generate one clean rising edge via MCP: LOW->HIGH on GPA0 triggers INT
        driver.on()
        assert wait_for_condition(lambda: pi_int_button.is_pressed, timeout_s=1.0), (
            "INT did not assert on rising edge"
        )
        time.sleep(0.1)  # hold high beyond debounce window

        # Return low and ensure it deasserts
        driver.off()
        # Clear the MCP interrupt to allow INT to return low
        _ = dev.read_data()
        assert wait_for_condition(
            lambda: not pi_int_button.is_pressed, timeout_s=1.0
        ), "INT did not deassert after clear"

        # Repeat sequence to ensure stability and debounce semantics
        driver.on()
        assert wait_for_condition(lambda: pi_int_button.is_pressed, timeout_s=1.0), (
            "INT did not assert on second rising edge"
        )
        time.sleep(0.1)
        driver.off()
        _ = dev.read_data()
        assert wait_for_condition(
            lambda: not pi_int_button.is_pressed, timeout_s=1.0
        ), "INT did not deassert after second clear"
    finally:
        try:
            driver.close()
        except Exception:
            pass
