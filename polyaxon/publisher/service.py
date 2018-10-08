from amqp import AMQPError
from redis import RedisError

from django.conf import settings

from db.redis.to_stream import RedisToStream
from libs.services import Service
from polyaxon.celery_api import app as celery_app
from polyaxon.settings import EventsCeleryTasks, RoutingKeys
from schemas.utils import to_list


class PublisherService(Service):
    __all__ = ('publish_experiment_job_log',
               'publish_build_job_log',
               'publish_job_log',
               'setup')

    def __init__(self):
        self._logger = None

    def publish_experiment_job_log(self,
                                   log_lines,
                                   status,
                                   experiment_uuid,
                                   experiment_name,
                                   job_uuid,
                                   task_type=None,
                                   task_idx=None):

        self._logger.debug("Publishing log event for task: %s.%s, %s",
                           task_type, task_idx, experiment_name)
        celery_app.send_task(
            EventsCeleryTasks.EVENTS_HANDLE_LOGS_EXPERIMENT_JOB,
            kwargs={
                'experiment_name': experiment_name,
                'experiment_uuid': experiment_uuid,
                'job_uuid': job_uuid,
                'log_lines': log_lines,
                'task_type': task_type,
                'task_idx': task_idx})
        try:
            should_stream = (RedisToStream.is_monitored_job_logs(job_uuid) or
                             RedisToStream.is_monitored_experiment_logs(experiment_uuid))
        except RedisError:
            should_stream = False
        if should_stream:
            self._logger.info("Streaming new log event for experiment: %s job: %s",
                              experiment_uuid,
                              job_uuid)

            with celery_app.producer_or_acquire(None) as producer:
                try:
                    producer.publish(
                        {
                            'experiment_uuid': experiment_uuid,
                            'job_uuid': job_uuid,
                            'log_lines': log_lines,
                            'status': status,
                            'task_type': task_type,
                            'task_idx': task_idx
                        },
                        retry=True,
                        routing_key='{}.{}.{}'.format(RoutingKeys.LOGS_SIDECARS_EXPERIMENTS,
                                                      experiment_uuid,
                                                      job_uuid),
                        exchange=settings.INTERNAL_EXCHANGE,
                    )
                except (TimeoutError, AMQPError):
                    pass

    def _stream_job_log(self, job_uuid, log_lines, routing_key):
        try:
            should_stream = RedisToStream.is_monitored_job_logs(job_uuid)
        except RedisError:
            should_stream = False
        if should_stream:
            self._logger.info("Streaming new log event for job: %s", job_uuid)

            with celery_app.producer_or_acquire(None) as producer:
                try:
                    producer.publish(
                        {
                            'job_uuid': job_uuid,
                            'log_lines': log_lines,
                        },
                        retry=True,
                        routing_key='{}.{}'.format(routing_key, job_uuid),
                        exchange=settings.INTERNAL_EXCHANGE,
                    )
                except (TimeoutError, AMQPError):
                    pass

    def publish_build_job_log(self, log_lines, job_uuid, job_name):
        log_lines = to_list(log_lines)

        self._logger.info("Publishing log event for task: %s", job_uuid)
        celery_app.send_task(
            EventsCeleryTasks.EVENTS_HANDLE_LOGS_BUILD_JOB,
            kwargs={'job_uuid': job_uuid, 'job_name': job_name, 'log_lines': log_lines})
        self._stream_job_log(job_uuid=job_uuid,
                             log_lines=log_lines,
                             routing_key=RoutingKeys.LOGS_SIDECARS_BUILDS)

    def publish_job_log(self, log_lines, job_uuid, job_name):
        self._logger.info("Publishing log event for task: %s", job_uuid)
        celery_app.send_task(
            EventsCeleryTasks.EVENTS_HANDLE_LOGS_JOB,
            kwargs={'job_uuid': job_uuid, 'job_name': job_name, 'log_lines': log_lines})
        self._stream_job_log(job_uuid=job_uuid,
                             log_lines=log_lines,
                             routing_key=RoutingKeys.LOGS_SIDECARS_JOBS)

    def setup(self):
        import logging

        self._logger = logging.getLogger('polyaxon.monitors.publisher')
