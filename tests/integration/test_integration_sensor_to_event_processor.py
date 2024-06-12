import pytest
from unittest.mock import MagicMock
from sensor_monitor import SensorMonitor
from event_processor import EventProcessor
import threading
from queue import Queue

def test_integration_sensor_to_event_processor():
    # Create a real event queue
    event_queue = Queue()

    # Create a shutdown event
    shutdown_event = threading.Event()

    # Create mock hardware objects
    mock_i2c = MagicMock()
    mock_gpio = MagicMock()

    # Simulate data to be read by the mock I2C
    mock_i2c.read_data.return_value = "mocked_data"

    # Create instances of SensorMonitor and EventProcessor
    sensor_monitor = SensorMonitor(mock_gpio, mock_i2c, event_queue, shutdown_event)
    event_processor = EventProcessor(event_queue, shutdown_event)

    # Trigger an interrupt (simulate sensor reading)
    sensor_monitor.read_data_on_interrupt()

    # Process the event
    event_processor.process_event(event_queue.get())

    # Check if data is put on the event queue
    assert not event_queue.empty() == False

if __name__ == "__main__":
    pytest.main()
