import pytest
from unittest.mock import MagicMock
import threading
from queue import Queue

# Skip if planned components are not implemented yet
sensor_monitor_mod = pytest.importorskip(
    "sensor_monitor",
    reason="Sensor Monitor component is planned; file not present yet"
)
event_processor_mod = pytest.importorskip(
    "event_processor",
    reason="Event Processor component is planned; file not present yet"
)

SensorMonitor = sensor_monitor_mod.SensorMonitor
EventProcessor = event_processor_mod.EventProcessor


def test_integration_sensor_to_event_processor(capsys):
    """End-to-end: SensorMonitor enqueues data and EventProcessor processes it."""
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

    # Check if data is put on the event queue (should now contain one item)
    assert not event_queue.empty()

    # Process the event
    event = event_queue.get()
    event_processor.process_event(event)

    # Assert observable processor behavior
    out, _ = capsys.readouterr()
    assert "Processing event: mocked_data" in out


if __name__ == "__main__":
    pytest.main()
