from queue import Queue
import threading


# Arch: SEC.APP.SensorMonitor
class SensorMonitor:
    """
    Class to monitor sensors, read data when an interrupt occurs,
    and put data on the event queue.
    """

    def __init__(self, gpio, i2c, event_queue: Queue, shutdown_event: threading.Event):
        """
        Initialize the SensorMonitor.

        Args:
            gpio: The GPIO object for handling interrupts.
            i2c: The I2C object for communication with the sensor.
            event_queue (Queue): The event queue for sharing events between threads.
            shutdown_event (threading.Event): The shutdown event for clean shutdown.
        """
        self.gpio = gpio
        self.i2c = i2c
        self.event_queue = event_queue
        self.shutdown_event = shutdown_event

        # Register interrupt callback
        self.gpio.register_interrupt_callback(self.read_data_on_interrupt)

        print("SensorMonitor startup.")

    def read_data_on_interrupt(self, channel=None):
        """
        Callback method to read data when interrupt occurs.

        Args:
            channel: The GPIO channel number (default: None).
        """

        print("SensorMonitor detects event.")

        # Read data from sensor via I2C
        data = self.i2c.read_data()

        # Put data on the event queue
        self.event_queue.put(data)

    def wait_for_completion(self):
        """Block until the shutdown event is set."""
        self.shutdown_event.wait()

    def cleanup(self):
        self.gpio.cleanup()
        print("SensorMonitor shutdown.")
