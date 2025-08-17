"""
GPIO interface for the Raspberry Pi INT line from MCP23017.

Notes
- Pi INT input uses the Pi's internal pull-down; this only biases the Pi input, not MCP GPIOs.
- MCP23017 INT is configured as active-high, push-pull (see `hardware/mcp23017.py`).
- Debounce can be applied on the Pi side using gpiozero's `bounce_time` if needed.
  We keep code minimal here; tune in hardware-in-loop as required.
"""

# Arch: HW.GPIO.INT
from gpiozero import Button


class MyGPIO:
    """
    Class for GPIO interaction using gpiozero library.
    """

    def __init__(self, pin_number=5):
        """
        Initialize the MyGPIO.

        Args:
            pin_number (int): The BCM GPIO pin number (default: 5).
        """
        # INT line from MCP23017 to Pi: use pull_up=False because INT is active-high push-pull
        # Optional debounce: pass bounce_time (e.g., 0.05 for ~50 ms) if needed for your hardware
        self.button = Button(pin_number, pull_up=False)

    def register_interrupt_callback(self, callback):
        """
        Registers an interrupt callback.

        Args:
            callback: The callback function to be registered.
        """
        self.button.when_pressed = callback

    def cleanup(self):
        """Cleans up GPIO resources."""
        # No cleanup needed for gpiozero
        pass
