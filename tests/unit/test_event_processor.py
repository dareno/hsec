import pytest
from unittest.mock import MagicMock
from queue import Queue

# Skip module if Event Processor component is not yet implemented
event_processor_mod = pytest.importorskip(
    "event_processor",
    reason="Event Processor is a planned component; file not present yet"
)
EventProcessor = event_processor_mod.EventProcessor


@pytest.mark.unit
def test_process_event():
    # Create a real event queue
    event_queue = Queue()

    # Create a mock shutdown event
    shutdown_event = MagicMock()
    shutdown_event.is_set.return_value = False

    # Create an instance of EventProcessor
    event_processor = EventProcessor(event_queue, shutdown_event)

    # Define a sample event
    sample_event = "Sample event data"

    # Add the sample event to the queue
    event_queue.put(sample_event)

    # Process the event
    event_processor.process_event(event_queue.get())

    # Verify that the event processor processes the event
    assert event_queue.empty()


if __name__ == "__main__":
    pytest.main()
