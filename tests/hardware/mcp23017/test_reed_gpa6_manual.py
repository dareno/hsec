import pytest
from hardware.mcp23017 import MCP23017
from tests.hardware.fixtures.devices import run_reed_edge_sequence

pytestmark = [pytest.mark.hardware, pytest.mark.manual]


def test_reed_gpa6_edges_manual(i2c_bus, hardware_config, pi_int_button):
    """
    ST-002 / FR7: Manual hardware verification for front door reed on MCP23017 GPA6.

    Operator instructions:
    - Ensure wiring: Reed -> GPA6, INT -> Pi BCM 5, common ground/power.
    - When prompted, open the front door (separate magnet), then close it to settle.

    Expected:
    - Establish baseline GPA6 (bit 6) level with a pre-read.
    - Open door: observe INT and a toggle of GPA6 away from baseline.
    - Close door: observe INT and a toggle back to the baseline level.
    """
    dev = MCP23017(bus=i2c_bus, device_address=hardware_config.mcp23017_addr)
    dev.setup()

    # Use shared helper to perform baseline capture and edge verification
    run_reed_edge_sequence(dev, pi_int_button, bit_index=6, location="front door")
