import uuid

from django.contrib.postgres.fields import ArrayField, JSONField
from django.core.cache import cache
from django.core.validators import validate_slug
from django.db import models
from django.utils.functional import cached_property

from libs.blacklist import validate_blacklist_name
from libs.spec_validation import validate_outputs_config, validate_persistence_config
from schemas.environments import OutputsConfig, PersistenceConfig


class DescribableModel(models.Model):
    description = models.TextField(blank=True, null=True)

    class Meta:
        abstract = True

    @property
    def has_description(self):
        return bool(self.description)


class NameableModel(models.Model):
    name = models.CharField(
        max_length=256,
        blank=True,
        null=True,
        default=None,
        validators=[validate_slug, validate_blacklist_name])

    class Meta:
        abstract = True


class SequenceManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().order_by('sequence')


class SequenceModel(models.Model):
    sequence = models.PositiveSmallIntegerField(
        editable=False,
        null=False)

    objects = models.Manager()
    sequence_objects = SequenceManager()

    class Meta:
        abstract = True

    def _set_sequence(self, filter_query):
        if self.pk is None:
            last = filter_query.last()
            self.sequence = 1
            if last:
                self.sequence = last.sequence + 1


class DiffModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class NodeSchedulingModel(models.Model):
    node_scheduled = models.CharField(max_length=256, blank=True, null=True)

    class Meta:
        abstract = True


class RunTimeModel(models.Model):
    started_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True


class TypeModel(models.Model):
    name = models.CharField(max_length=128, unique=True)
    schema_definition = models.TextField()

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class TagModel(models.Model):
    tags = ArrayField(
        base_field=models.CharField(max_length=64),
        blank=True,
        null=True,
        help_text='The parameters used for this experiment.')

    class Meta:
        abstract = True


class PersistenceModel(models.Model):
    persistence = JSONField(
        null=True,
        blank=True,
        help_text='The persistence definition.',
        validators=[validate_persistence_config])

    class Meta:
        abstract = True

    @cached_property
    def persistence_config(self):
        return PersistenceConfig.from_dict(self.persistence) if self.persistence else None

    @cached_property
    def persistence_data(self):
        return self.persistence_config.data if self.persistence_config else None

    @cached_property
    def persistence_outputs(self):
        return self.persistence_config.outputs if self.persistence_config else None


class OutputsModel(models.Model):
    outputs = JSONField(
        null=True,
        blank=True,
        help_text='The persistence definition.',
        validators=[validate_outputs_config])
    outputs_refs = models.OneToOneField(
        'db.OutputsRefs',
        related_name='+',
        blank=True,
        null=True,
        editable=False,
        on_delete=models.SET_NULL)

    class Meta:
        abstract = True

    @cached_property
    def outputs_config(self):
        return OutputsConfig.from_dict(self.outputs) if self.outputs else None

    @cached_property
    def outputs_jobs(self):
        return self.outputs_config.jobs if self.outputs_config else None

    @cached_property
    def outputs_experiments(self):
        return self.outputs_config.experiments if self.outputs_config else None

    @cached_property
    def outputs_refs_jobs(self):
        if not self.outputs_refs:
            return None

        specs = self.outputs_refs.get_jobs_outputs_spec()
        if not specs:
            return None

        # Return an ordered list
        refs = []
        for job in self.outputs_jobs:
            refs.append(specs[int(job)])

        return refs

    @cached_property
    def outputs_refs_experiments(self):
        if not self.outputs_refs:
            return None

        specs = self.outputs_refs.get_experiments_outputs_spec()
        if not specs:
            return None

        # Return an ordered list
        refs = []
        for experiment in self.outputs_experiments:
            refs.append(specs[int(experiment)])

        return refs


class Singleton(DiffModel):
    """A base model to represents a singleton."""

    class Meta:
        abstract = True

    def set_cache(self):
        cache.set(self.__class__.__name__, self)

    def save(self, *args, **kwargs):  # pylint:disable=arguments-differ
        self.pk = 1
        super().save(*args, **kwargs)
        self.set_cache()

    def delete(self, *args, **kwargs):  # pylint:disable=arguments-differ
        pass

    @classmethod
    def may_be_update(cls, obj):
        raise NotImplementedError  # noqa

    @classmethod
    def load(cls):
        raise NotImplementedError  # noqa


class StatusModel(models.Model):
    """A model that represents a status at certain time.

    This is an abstract class, every subclass must implement a status attribute,
    it must implement also Foreignkey to the model that needs a status.

    e.g.

    # status = db.CharField(
        max_length=64,
        blank=True,
        null=True,
        default=STATUSES.CREATED,
        choices=STATUSES.CHOICES)
    # job = db.ForeignKey(Job, on_delete=db.CASCADE, related_name='statuses')
    """
    STATUSES = None

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        null=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    message = models.CharField(max_length=256, null=True, blank=True)

    def __str__(self):
        return '{} <{}>'.format(str(self), self.status)

    class Meta:
        verbose_name_plural = 'Statuses'
        ordering = ['created_at']
        abstract = True


class LastStatusMixin(object):
    """A mixin that extracts the logic of last_status.

    This is an abstract class, every subclass must implement a status attribute,
    as well as a last_status attribute:

    e.g.

    status = db.OneToOneField(
        'ExperimentStatus',
        related_name='+',
        blank=True,
        null=True,
        editable=True,
        on_delete=db.SET_NULL)
    """
    STATUSES = None

    @property
    def last_status(self):
        return self.status.status if self.status else None

    @property
    def is_running(self):
        return self.STATUSES.is_running(self.last_status)

    @property
    def is_done(self):
        return self.STATUSES.is_done(self.last_status)

    @property
    def failed(self):
        return self.STATUSES.failed(self.last_status)

    @property
    def succeeded(self):
        return self.STATUSES.succeeded(self.last_status)

    @property
    def stopped(self):
        return self.STATUSES.stopped(self.last_status)

    def set_status(self, status, message=None, **kwargs):
        raise NotImplemented  # noqa


class CachedMixin(object):
    """
    A mixin to help clear cached properties.
    """
    CACHED_PROPERTIES = ()

    def clear_cached_properties(self, properties=None):
        properties = properties or self.CACHED_PROPERTIES
        for key in properties:
            if key in self.__dict__:
                del self.__dict__[key]
