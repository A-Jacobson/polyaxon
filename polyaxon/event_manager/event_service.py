from hestia.service_interface import Service


class EventService(Service):
    __all__ = ('record', 'setup')

    event_manager = None

    def can_handle(self, event_type):
        return isinstance(event_type, str) and self.event_manager.knows(event_type)

    def get_event(self, event_type, event_data=None, instance=None, **kwargs):
        if instance or not event_data:
            return self.event_manager.get(
                event_type,
            ).from_instance(instance, **kwargs)
        return self.event_manager.get(
            event_type,
        ).from_event_data(event_data=event_data, **kwargs)

    def record(self, event_type, event_data=None, instance=None, **kwargs):
        """ Validate and record an event.

        >>> record('event.action', object_instance)
        """
        if not self.is_setup:
            return
        if not self.can_handle(event_type=event_type):
            return

        event = self.get_event(event_type=event_type,
                               event_data=event_data,
                               instance=instance,
                               **kwargs)
        self.record_event(event)
        return event

    def record_event(self, event):
        """ Record an event.

        >>> record_event(Event())
        """
        pass
