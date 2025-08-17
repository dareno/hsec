from queue import Empty


# Arch: SEC.APP.EventProc
class EventProcessor:
    """
    Class to process events from the event queue.
    """

    def __init__(self, event_queue, shutdown_event):
        """
        Initialize the EventProcessor.

        Args:
            event_queue (Queue): The event queue for processing events.
            shutdown_event (threading.Event): The shutdown event for clean shutdown.
        """
        self.event_queue = event_queue
        self.shutdown_event = shutdown_event

    def run(self):
        """
        Method to run event processing.

        This method continuously processes events from the event queue until
        the shutdown event is set.
        """
        print("EventProcessor started up.")  # Print statement indicating startup
        while not self.shutdown_event.is_set():
            try:
                # Get the next event from the event queue
                event = self.event_queue.get(
                    timeout=1
                )  # Timeout to allow checking the shutdown event
                # Process the event
                self.process_event(event)
            except Empty:
                # Timeout occurred, check if shutdown event is set
                continue
        print("EventProcessor shutting down.")  # Print statement indicating startup

    def process_event(self, event):
        """
        Process a single event.

        Args:
            event: The event to be processed.
        """
        print(f"Processing event: {event}")
        # Add your event processing logic here
