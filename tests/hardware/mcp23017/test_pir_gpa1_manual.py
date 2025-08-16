import pytest

pytestmark = [pytest.mark.hardware, pytest.mark.manual]


def test_pir_gpa1_edges_manual(i2c_bus, hardware_config, pi_int_button):
    """
    ST-001 / FR7: Manual hardware verification for PIR on MCP23017 GPA1.

    Operator instructions:
    - Ensure wiring: PIR -> GPA1, INT -> Pi BCM 5, common ground/power.
    - When prompted, create motion in front of the PIR; then step away and let it settle.
    """
    from hardware.mcp23017 import MCP23017
    from tests.hardware.fixtures.devices import run_pir_motion_sequence

    dev = MCP23017(bus=i2c_bus, device_address=hardware_config.mcp23017_addr)
    dev.setup()

    # Use shared helper to perform baseline capture and motion/settle verification
    run_pir_motion_sequence(
        dev,
        pi_int_button,
        bit_index=1,
        location="PIR on GPA1",
        port="A",
    )
