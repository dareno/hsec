import pytest

pytestmark = pytest.mark.hardware


def test_setup_programs_expected_registers(i2c_bus, hardware_config):
    from hardware.mcp23017 import MCP23017

    dev = MCP23017(bus=i2c_bus, device_address=hardware_config.mcp23017_addr)

    # Execute setup which should configure IOCON, INTCONx, GPINTENx
    dev.setup()

    # Read back and validate
    IOCON = MCP23017.IOCON
    INTCONA = MCP23017.INTCONA
    INTCONB = MCP23017.INTCONB
    GPINTENA = MCP23017.GPINTENA
    GPINTENB = MCP23017.GPINTENB

    iocon = i2c_bus.read_byte_data(hardware_config.mcp23017_addr, IOCON)
    intcona = i2c_bus.read_byte_data(hardware_config.mcp23017_addr, INTCONA)
    intconb = i2c_bus.read_byte_data(hardware_config.mcp23017_addr, INTCONB)
    gpintena = i2c_bus.read_byte_data(hardware_config.mcp23017_addr, GPINTENA)
    gpintenb = i2c_bus.read_byte_data(hardware_config.mcp23017_addr, GPINTENB)

    # IOCON bits: INTPOL=0x02 set, MIRROR=0x40 set, ODR=0x04 cleared
    assert (iocon & 0x02) == 0x02, "INTPOL should be 1 (active-high)"
    assert (iocon & 0x40) == 0x40, "MIRROR should be 1 (INTA/INTB tied)"
    assert (iocon & 0x04) == 0x00, "ODR should be 0 (push-pull)"

    # INTCONx should be 0x00 for any-change mode
    assert intcona == 0x00
    assert intconb == 0x00

    # GPINTENx should be 0xFF (all pins)
    assert gpintena == 0xFF
    assert gpintenb == 0xFF
