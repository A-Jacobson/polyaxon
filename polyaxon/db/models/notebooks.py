from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.functional import cached_property

from db.models.abstract_jobs import AbstractJobStatus, JobMixin
from db.models.plugins import PluginJobBase
from db.models.unique_names import NOTEBOOK_UNIQUE_NAME_FORMAT
from db.models.utils import DataReference
from libs.spec_validation import validate_notebook_spec_config
from schemas.specifications import NotebookSpecification


class NotebookJob(PluginJobBase, DataReference, JobMixin):
    """A model that represents the configuration for tensorboard job."""
    JOBS_NAME = 'notebooks'

    project = models.ForeignKey(
        'db.Project',
        on_delete=models.CASCADE,
        related_name='notebook_jobs')
    config = JSONField(
        help_text='The compiled polyaxonfile for the notebook job.',
        validators=[validate_notebook_spec_config])
    status = models.OneToOneField(
        'db.NotebookJobStatus',
        related_name='+',
        blank=True,
        null=True,
        editable=True,
        on_delete=models.SET_NULL)

    class Meta:
        app_label = 'db'

    @cached_property
    def unique_name(self):
        return NOTEBOOK_UNIQUE_NAME_FORMAT.format(
            project_name=self.project.unique_name,
            id=self.id)

    @cached_property
    def specification(self):
        return NotebookSpecification(values=self.config)

    def set_status(self,  # pylint:disable=arguments-differ
                   status,
                   created_at=None,
                   message=None,
                   traceback=None,
                   details=None):
        params = {'created_at': created_at} if created_at else {}
        return self._set_status(status_model=NotebookJobStatus,
                                status=status,
                                message=message,
                                traceback=traceback,
                                details=details,
                                **params)


class NotebookJobStatus(AbstractJobStatus):
    """A model that represents notebook job status at certain time."""
    job = models.ForeignKey(
        'db.NotebookJob',
        on_delete=models.CASCADE,
        related_name='statuses')

    class Meta(AbstractJobStatus.Meta):
        app_label = 'db'
        verbose_name_plural = 'Notebook Job Statuses'
