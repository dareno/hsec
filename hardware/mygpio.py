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
