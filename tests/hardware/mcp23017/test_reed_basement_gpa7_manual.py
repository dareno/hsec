import pytest
from hardware.mcp23017 import MCP23017
from tests.hardware.fixtures.devices import run_reed_edge_sequence

pytestmark = [pytest.mark.hardware, pytest.mark.manual]


def test_reed_basement_gpa7_manual(i2c_bus, hardware_config, pi_int_button):
    """
    ST-003 / FR7: Manual HIL verification for basement door reed on MCP23017 GPA7.

    Procedure:
    - Use visible prompts to capture baseline, then open (interval 1) and close (interval 2) the basement door.
    - Accepts toggle-based behavior relative to baseline (NO/NC agnostic).
    """
    dev = MCP23017(bus=i2c_bus, device_address=hardware_config.mcp23017_addr)
    dev.setup()

    run_reed_edge_sequence(dev, pi_int_button, bit_index=7, location="basement door")
