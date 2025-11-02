"""
Event subscribers for observability.

Subscribers listen to hook events and perform actions like:
- Storing events to database
- Sending to external services
- Logging
- Analytics
"""

from .events import BaseEvent, EventType
from .storage import get_event_store


class DatabaseEventSubscriber:
    """
    Subscribes to all events and stores them in the database.
    """

    def __init__(self):
        """Initialize subscriber."""
        self.store = get_event_store()

    def handle_event(self, event: BaseEvent):
        """
        Handle any event by storing to database.

        Args:
            event: Event to handle
        """
        try:
            self.store.store_event(event)
        except Exception as e:
            print(f"⚠️  Failed to store event: {e}")


def register_default_subscribers():
    """
    Register default subscribers to the global hook manager.

    This should be called during application initialization.
    """
    from .hooks import get_hooks

    hooks = get_hooks()
    subscriber = DatabaseEventSubscriber()

    # Subscribe to all event types
    for event_type in EventType:
        hooks.subscribe(event_type, subscriber.handle_event)

    print("✅ Registered database event subscriber")
