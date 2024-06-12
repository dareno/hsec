# main.py

import threading
from queue import Queue
from hardware.mcp23017 import MCP23017
from hardware.mygpio import MyGPIO
from sensor_monitor import SensorMonitor
from event_processor import EventProcessor

def main():
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
        sensor_thread.join()
        processor_thread.join()
    except KeyboardInterrupt:
        shutdown_event.set()
        sensor_thread.join()
        processor_thread.join()
        sensor_monitor.cleanup()

if __name__ == "__main__":
    main()
