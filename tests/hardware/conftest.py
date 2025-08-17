import os
import platform
from dataclasses import dataclass
from typing import Optional

import pytest


@dataclass(frozen=True)
class HardwareConfig:
    i2c_bus: int
    mcp23017_addr: int
    int_gpio: Optional[int]

    @staticmethod
    def from_env() -> "HardwareConfig":
        bus = int(os.getenv("HSEC_I2C_BUS", "1"))
        addr_str = os.getenv("HSEC_MCP23017_ADDR", "0x20")
        addr = int(addr_str, 0)
        int_gpio_str = os.getenv("HSEC_INT_GPIO")
        # Default to BCM 5 if not provided
        int_gpio = int(int_gpio_str) if int_gpio_str is not None else 5
        return HardwareConfig(i2c_bus=bus, mcp23017_addr=addr, int_gpio=int_gpio)


@pytest.fixture(scope="session")
def hardware_config() -> HardwareConfig:
    """Session-scoped hardware configuration from environment.

    - HSEC_I2C_BUS (default: 1)
    - HSEC_MCP23017_ADDR (default: 0x20)
    - HSEC_INT_GPIO (optional)
    """
    return HardwareConfig.from_env()


@pytest.fixture(scope="session")
def i2c_bus(hardware_config: HardwareConfig):
    """Provide an smbus2.SMBus instance for I2C access.

    Skips with a clear message if smbus2 is unavailable.
    """
    smbus2 = pytest.importorskip("smbus2", reason="smbus2 required for HIL tests")
    try:
        bus = smbus2.SMBus(hardware_config.i2c_bus)
    except FileNotFoundError as e:
        pytest.skip(f"I2C bus /dev/i2c-{hardware_config.i2c_bus} not available: {e}")
    yield bus
    try:
        bus.close()
    except Exception:
        pass


@pytest.fixture(scope="session")
def pi_int_button(hardware_config: HardwareConfig):
    """Provide a gpiozero.Button for the Pi INT line if configured.

    Skips if not on Linux or gpiozero unavailable or env var not provided.
    """
    if platform.system() != "Linux":
        pytest.skip("GPIO tests require Linux (Raspberry Pi)")
    gpiozero = pytest.importorskip(
        "gpiozero", reason="gpiozero required for Pi GPIO tests"
    )
    # INT line uses pull_down on the Pi side; debounce ~50ms as per project notes
    btn = gpiozero.Button(hardware_config.int_gpio, pull_up=False, bounce_time=0.05)
    yield btn
    try:
        btn.close()
    except Exception:
        pass
