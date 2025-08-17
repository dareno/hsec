import pytest
from unittest.mock import MagicMock

# Skip module if Sensor Monitor component is not yet implemented
sensor_monitor_mod = pytest.importorskip(
    "sensor_monitor",
    reason="Sensor Monitor is a planned component; file not present yet"
)
SensorMonitor = sensor_monitor_mod.SensorMonitor


@pytest.mark.unit
def test_read_data_on_interrupt():
    # Create mock hardware objects
    mock_i2c = MagicMock()
    mock_gpio = MagicMock()

    # Set up SensorMonitor with mock hardware
    event_queue = MagicMock()
    shutdown_event = MagicMock()
    sensor_monitor = SensorMonitor(mock_gpio, mock_i2c, event_queue, shutdown_event)

    # Simulate data to be read by the mock I2C
    mock_i2c.read_data.return_value = "mocked_data"

    # Trigger interrupt
    sensor_monitor.read_data_on_interrupt()

    # Check if data is put on the event queue
    event_queue.put.assert_called_once_with("mocked_data")


if __name__ == "__main__":
    pytest.main()
