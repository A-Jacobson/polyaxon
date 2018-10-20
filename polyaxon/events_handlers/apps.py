from django.apps import AppConfig


class EventsHandlersConfig(AppConfig):
    name = 'events_handlers'
    verbose_name = 'EventsHandlers'

    def ready(self):
        import signals.build_jobs  # noqa
        import signals.experiment_groups  # noqa
        import signals.experiments  # noqa
        import signals.jobs  # noqa
        import signals.projects  # noqa
        import signals.pipelines  # noqa
        import signals.project_notebook_jobs  # noqa
        import signals.project_tensorboard_jobs  # noqa
        import signals.nodes  # noqa
        import signals.pipelines  # noqa
