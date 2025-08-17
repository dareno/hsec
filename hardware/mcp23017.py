"""
MCP23017 interrupt configuration: goals, terminology, critical registers, and expected behavior.

Goal
- Generate an interrupt when there is a change on any MCP23017 GPIO (A or B), regardless of edge.
- Provide an active-high, push-pull interrupt signal to the Raspberry Pi (no external pull-up required).
- Mirror INTA/INTB so either port change asserts the single INT line to the Pi.

Terminology (in context of MCP23017 + Raspberry Pi)
- Edge: A change in signal level. Rising edge = LOW→HIGH, falling edge = HIGH→LOW.
  Any-change/both-edges means either transition causes an interrupt.
- Push-pull (IOCON.ODR=0): The INT pin actively drives HIGH and LOW (no pull-up needed).
- Open-drain (IOCON.ODR=1): INT only pulls LOW; it never drives HIGH, so a pull-up is required.
- Active-high (IOCON.INTPOL=1): INT is asserted when HIGH, deasserted when LOW.
- Mirror (IOCON.MIRROR=1): INTA and INTB are tied logically; either port A or B can assert the same INT line.
- Interrupt-on-change (GPINTENx): Per-bit enable for generating interrupts on GPIO changes.
- Compare-to-previous (INTCONx=0): Triggers when a bit changes from its last value (both edges).
- Compare-to-DEFVAL (INTCONx=1): Triggers when GPIO != DEFVAL (useful for rising-only or falling-only via DEFVALx).
- DEFVALx: Baseline value used when INTCONx=1; define expected level for edge select behavior.
- INTCAPx: Latches the GPIO state at the moment the interrupt occurred. Reading INTCAP clears the interrupt.
  Reading GPIOx also clears, but INTCAP avoids races if a pin toggles again before the read.
- Pull-ups (GPPU): MCP23017 provides internal pull-ups only (no pull-downs). Enable if inputs might float.
  The Pi’s pull-down on its INT input does not bias MCP23017 GPIO pins.
- Debounce: We debounce the Pi’s INT input in `hardware/mygpio.py`; you may still need input-side filtering
  on MCP pins depending on sensors/switches.

Critical registers (changed from defaults) and effects
- IOCON: INTPOL=1 (active-high INT), MIRROR=1 (INTA/INTB tied), ODR=0 (push-pull INT).
  Effect: Pi sees a clean, active-high interrupt on a single line; no external pull-up required on INT.
- GPINTENA=0xFF, GPINTENB=0xFF (enable interrupt-on-change on all pins).
  Effect: Any bit change on either port can assert INT.
- INTCONA=0x00, INTCONB=0x00 (compare-to-previous).
  Effect: Interrupt on any edge (rising or falling).

Interrupt clearing and data read
- INT is cleared by reading the port that changed (GPIOx) or the latched INTCAPx.
- Implementation detail: `read_data()` reads GPIOA then GPIOB to ensure INT is cleared regardless of source.
  Consider using INTCAPx to avoid races; see Datasheet §1.6, §3.1.7.

Assumptions and wiring
- Raspberry Pi uses internal pull-down on its INT input (Pi-only). MCP23017 pins themselves need proper biasing.
- MCP23017 has internal pull-ups (GPPU) but no pull-downs; enable as needed and accept idle HIGH.

Modes and future configuration
- Any-change mode (current): INTCONx=0x00, GPINTENx=0xFF. Triggers on both edges; simplest for mixed signals.
- Rising-only/falling-only (optional): Set INTCONx=0xFF and program DEFVALx baseline; triggers when GPIOx != DEFVALx.
- Input direction and pulls (optional): Configure IODIRx for inputs and GPPUx for internal pulls per circuit needs.

References
- MCP23017 Datasheet (DS20001952C): Interrupt logic and registers: §1.5–1.6, §3.1 (IOCON/INTCON/GPINTEN/DEFVAL/INTCAP), §3.2 (GPIO/GPPU).
  https://ww1.microchip.com/downloads/en/devicedoc/20001952c.pdf
"""

# Arch: HW.Drv.MCP23017
from typing import TYPE_CHECKING, Protocol, runtime_checkable
import warnings

if TYPE_CHECKING:
    # Imported for type checking only; avoids a hard runtime dependency here.
    import smbus2  # noqa: F401


@runtime_checkable
class I2CBus(Protocol):
    """Minimal protocol for an I2C bus used by MCP23017.

    This defines only the methods required by this driver, allowing callers to
    pass in any compatible object (e.g., smbus2.SMBus, a mock, or another I2C implementation).
    """

    def read_byte_data(self, i2c_addr: int, register: int) -> int: ...

    def write_byte_data(self, i2c_addr: int, register: int, value: int) -> None: ...


class MCP23017:
    """
    Class for interacting with the MCP23017 hardware component.
    """

    # Define register addresses
    IOCON = 0x0A  # Configuration register for MCP23017
    GPINTENA = 0x04  # Interrupt-on-change control for port A
    GPINTENB = 0x05  # Interrupt-on-change control for port B
    INTCONA = 0x08  # Interrupt control (0=compare to previous, 1=compare to DEFVAL) for port A
    INTCONB = 0x09  # Interrupt control for port B

    def __init__(self, bus: "I2CBus", device_address: int):
        """
        Initialize the MCP23017.

        This constructor is lightweight and performs no I2C reads/writes. It stores
        the provided bus and device address. Call explicit setup methods (e.g.,
        `setup()`) when you want to apply configuration to the hardware.

        Args:
            bus (I2CBus): The I2C bus instance to use for communication. This can be
                an `smbus2.SMBus` or any object implementing the minimal I2CBus protocol.
            device_address (int): The device address for I2C communication (e.g., 0x20).
        """

        self.bus = bus
        self.device_address = device_address
        # No side effects here: do not configure IOCON or enable interrupts automatically.
        # Use explicit methods to configure the device after construction.

    def setup(self):
        """
        Program MCP23017 for any-change interrupt on all GPIOs with active-high, push-pull INT.

        Sets:
        - IOCON: INTPOL=1 (active-high), MIRROR=1 (tie INTA/INTB), ODR=0 (push-pull)
        - INTCON[A/B]=0x00 (compare-to-previous => both edges)
        - GPINTEN[A/B]=0xFF (enable on all pins)

        See module docstring in `hardware/mcp23017.py` for rationale, wiring assumptions, and references.
        """
        # Read the current IOCON register value
        current_iocon = self.bus.read_byte_data(self.device_address, self.IOCON)

        # IOCON: INTPOL=1 (active-high), MIRROR=1 (tie INTA/INTB), ODR=0 (push-pull: drives high/low)
        # Bit masks: INTPOL=0x02, ODR=0x04, MIRROR=0x40
        new_iocon = (current_iocon | 0x02 | 0x40) & ~0x04

        # Write the new value to the IOCON register
        self.bus.write_byte_data(self.device_address, self.IOCON, new_iocon)

        # INTCON[A/B]=0x00: compare-to-previous => any-change (both edges)
        self.bus.write_byte_data(self.device_address, self.INTCONA, 0x00)
        self.bus.write_byte_data(self.device_address, self.INTCONB, 0x00)

        # GPINTEN[A/B]=0xFF: enable interrupt-on-change on all pins
        self.bus.write_byte_data(self.device_address, self.GPINTENA, 0xFF)
        self.bus.write_byte_data(self.device_address, self.GPINTENB, 0xFF)

    def read_ports(self) -> tuple[int, int]:
        """
        Read both ports in order (A then B) and return their values.

        Reading both ensures the interrupt is cleared regardless of which port
        triggered when IOCON.MIRROR is enabled.
        """
        data_a = self.bus.read_byte_data(self.device_address, 0x12)  # GPIOA
        data_b = self.bus.read_byte_data(self.device_address, 0x13)  # GPIOB
        return data_a, data_b

    def read_port(self, port: str) -> int:
        """
        Read a single port ('A' or 'B') while still clearing interrupts safely.

        Internally reads A then B to clear INT in MIRROR mode, returning the
        requested port's value.
        """
        p = port.upper()
        if p not in ("A", "B"):
            raise ValueError("port must be 'A' or 'B'")
        a, b = self.read_ports()
        return a if p == "A" else b

    def read_data(self) -> int:
        """
        Deprecated. Returns GPIOA value. Use read_port('A') or read_ports().
        """
        warnings.warn(
            "MCP23017.read_data() is deprecated; use read_port('A') or read_ports()",
            DeprecationWarning,
            stacklevel=2,
        )
        a, _b = self.read_ports()
        return a
