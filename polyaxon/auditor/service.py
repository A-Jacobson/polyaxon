from auditor.manager import default_manager
from event_manager.event_service import EventService


class AuditorService(EventService):
    """An service that just passes the event to author services."""

    event_manager = default_manager

    def __init__(self):
        self.notifier = None
        self.tracker = None
        self.activitylogs = None

    def get_event(self, event_type, instance, **kwargs):
        return {
            'event_type': event_type,
            'instance': instance,
            'kwargs': kwargs
        }

    def record_event(self, event):
        self.notifier.record(event_type=event['event_type'],
                             instance=event['instance'],
                             **event['kwargs'])
        self.tracker.record(event_type=event['event_type'],
                            instance=event['instance'],
                            **event['kwargs'])
        self.activitylogs.record(event_type=event['event_type'],
                                 instance=event['instance'],
                                 **event['kwargs'])

    def setup(self):
        super().setup()
        # Load default event types
        import auditor.events  # noqa

        import notifier
        import activitylogs
        import tracker

        self.notifier = notifier
        self.tracker = tracker
        self.activitylogs = activitylogs
