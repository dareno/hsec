import pytest

pytestmark = pytest.mark.hardware


def test_can_construct_and_read_iocon(i2c_bus, hardware_config):
    """Non-destructive smoke: read IOCON register.

    Ensures the device is reachable on the configured I2C bus/address.
    """
    from hardware.mcp23017 import MCP23017

    _ = MCP23017(bus=i2c_bus, device_address=hardware_config.mcp23017_addr)

    # Read current IOCON value (register 0x0A) without changing configuration
    value = i2c_bus.read_byte_data(hardware_config.mcp23017_addr, MCP23017.IOCON)

    # Basic sanity: IOCON is a byte 0..255
    assert 0 <= value <= 0xFF
