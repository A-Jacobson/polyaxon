import logging
import uuid

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.functional import cached_property

from constants.jobs import JobLifeCycle
from db.models.utils import DiffModel, LastStatusMixin, RunTimeModel, StatusModel

_logger = logging.getLogger('polyaxon.db.jobs')


class AbstractJob(DiffModel, RunTimeModel, LastStatusMixin):
    """An abstract base class for job, used both by experiment jobs and other jobs."""
    STATUSES = JobLifeCycle

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        null=False)
    definition = JSONField(help_text='The specific values/manifest for this job.', default={})

    class Meta:
        abstract = True

    def _set_status(self, status_model, status, message=None, details=None):
        current_status = self.last_status
        if self.is_done:
            # We should not update statuses anymore
            _logger.debug(
                'Received a new status `%s` for job `%s`. '
                'But the job is already done with status `%s`',
                status, self.unique_name, current_status)
            return False
        if JobLifeCycle.can_transition(status_from=current_status, status_to=status):
            # Add new status to the job
            status_model.objects.create(job=self,
                                        status=status,
                                        message=message,
                                        details=details)
            return True
        return False


class JobMixin(object):

    def __str__(self):
        return self.unique_name

    @cached_property
    def unique_name(self):
        pass

    @cached_property
    def image(self):
        return self.specification.build.image

    @cached_property
    def resources(self):
        return self.specification.resources

    @cached_property
    def node_selector(self):
        return self.specification.node_selector

    @cached_property
    def affinity(self):
        return self.specification.affinity

    @cached_property
    def tolerations(self):
        return self.specification.tolerations

    @cached_property
    def build_steps(self):
        return self.specification.build.build_steps

    @cached_property
    def env_vars(self):
        return self.specification.build.env_vars


class TensorboardJobMixin(object):
    @property
    def tensorboard(self):
        return self.tensorboard_jobs.last()

    @property
    def has_tensorboard(self):
        tensorboard = self.tensorboard
        return tensorboard and tensorboard.is_running


class AbstractJobStatus(StatusModel):
    """A model that represents job status at certain time."""
    STATUSES = JobLifeCycle

    status = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        default=STATUSES.CREATED,
        choices=STATUSES.CHOICES)
    details = JSONField(null=True, blank=True, default={})

    def __str__(self):
        return '{} <{}>'.format(self.job.unique_name, self.status)

    class Meta:
        verbose_name_plural = 'Job Statuses'
        ordering = ['created_at']
        abstract = True
