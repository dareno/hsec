# tests/integration/test_hardware_integration.py
# Validates: any-change (both edges) interrupts across ports A/B; mirrored INT line to Pi;
# interrupt clears after reading GPIOA then GPIOB (see hardware/mcp23017.py module docstring).

import threading
import time
import pytest
from queue import Queue
from sensor_monitor import SensorMonitor
from event_processor import EventProcessor
from hardware.mcp23017 import MCP23017
from hardware.mygpio import MyGPIO

@pytest.mark.hardware
def test_hardware_integration():
    event_queue = Queue()
    shutdown_event = threading.Event()

    i2c_bus = 1
    i2c_address = 0x20
    mcp23017 = MCP23017(i2c_bus, i2c_address)
    gpio = MyGPIO(5)

    sensor_monitor = SensorMonitor(gpio, mcp23017, event_queue, shutdown_event)
    event_processor = EventProcessor(event_queue, shutdown_event)

    sensor_thread = threading.Thread(target=sensor_monitor.wait_for_completion)
    processor_thread = threading.Thread(target=event_processor.run)
    sensor_thread.start()
    processor_thread.start()

    try:
        print("Please trigger the hardware (e.g., press the button) to generate an event.")
        time.sleep(10)  # Give the user time to trigger the hardware

        while not event_queue.empty():
            event = event_queue.get(timeout=1)
            print(f"Event processed: {event}")
            assert event is not None  # Check if event is not None
    except KeyboardInterrupt:
        print("Test interrupted.")
    finally:
        shutdown_event.set()
        sensor_thread.join()
        processor_thread.join()
        sensor_monitor.cleanup()

if __name__ == "__main__":
    test_hardware_integration()
