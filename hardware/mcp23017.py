import smbus2

class MCP23017:
    """
    Class for interacting with the MCP23017 hardware component.
    """
    # Define register addresses
    IOCON = 0x0A  # Configuration register for MCP23017
    GPINTENA = 0x04  # Interrupt-on-change control for port A
    GPINTENB = 0x05  # Interrupt-on-change control for port B
    
    def __init__(self, bus_number=1, device_address=0x20):
        """
        Initialize the MCP23017.

        Args:
            bus_number (int): The bus number for I2C communication (default: 1).
            device_address (int): The device address for I2C communication (default: 0x20).
        """

        self.bus = smbus2.SMBus(bus_number)
        self.device_address = device_address
        # Configure IOCON to use active-high interrupts and mirror INTA and INTB
        self.configure_iocon()

    def configure_iocon(self):
        """
        Configure the IOCON register to set INTPOL to active-high and MIRROR to 1.
        """
        # Read the current IOCON register value
        current_iocon = self.bus.read_byte_data(self.device_address, self.IOCON)
        
        # Set the INTPOL bit (bit 1) to 1 and MIRROR bit (bit 6) to 1
        new_iocon = current_iocon | 0x02 | 0x40
        
        # Write the new value to the IOCON register
        self.bus.write_byte_data(self.device_address, self.IOCON, new_iocon)

        # Enable interrupts on all pins
        self.enable_interrupts()

    def enable_interrupts(self):
        """
        Enable interrupts on all pins.
        """
        # Enable interrupts on all pins of GPIOA and GPIOB
        self.bus.write_byte_data(self.device_address, self.GPINTENA, 0xFF)
        self.bus.write_byte_data(self.device_address, self.GPINTENB, 0xFF)

    def read_data(self) -> int:
        """
        Reads data from MCP23017 GPIOA register.

        Returns:
            int: The data read from MCP23017 GPIOA register.
        """
        # Read data from the GPIOA register
        data = self.bus.read_byte_data(self.device_address, 0x12)
        return data
