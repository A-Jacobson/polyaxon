from hestia.decorators import ignore_raw, ignore_updates, ignore_updates_pre

from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver

import auditor

from constants.jobs import JobLifeCycle
from db.models.tensorboards import TensorboardJob, TensorboardJobStatus
from event_manager.events.tensorboard import (
    TENSORBOARD_FAILED,
    TENSORBOARD_NEW_STATUS,
    TENSORBOARD_STOPPED,
    TENSORBOARD_SUCCEEDED
)
from libs.repos.utils import assign_code_reference
from polyaxon.celery_api import celery_app
from polyaxon.settings import SchedulerCeleryTasks
from signals.outputs import set_outputs, set_outputs_refs
from signals.run_time import set_job_finished_at, set_job_started_at
from signals.utils import set_persistence, set_tags


@receiver(pre_save, sender=TensorboardJob, dispatch_uid="tensorboard_job_pre_save")
@ignore_updates_pre
@ignore_raw
def tensorboard_job_pre_save(sender, **kwargs):
    instance = kwargs['instance']
    set_tags(instance=instance)
    default_persistence_outputs = None
    if instance.experiment:
        default_persistence_outputs = instance.experiment.persistence_outputs
    if instance.experiment_group:
        default_persistence_outputs = instance.experiment_group.persistence_outputs
    set_persistence(instance=instance, default_persistence_outputs=default_persistence_outputs)
    set_outputs(instance=instance)
    set_outputs_refs(instance=instance)
    assign_code_reference(instance)


@receiver(post_save, sender=TensorboardJob, dispatch_uid="tensorboard_job_post_save")
@ignore_updates
@ignore_raw
def tensorboard_job_post_save(sender, **kwargs):
    instance = kwargs['instance']
    instance.set_status(status=JobLifeCycle.CREATED)


@receiver(post_save, sender=TensorboardJobStatus, dispatch_uid="tensorboard_job_status_post_save")
@ignore_updates
@ignore_raw
def tensorboard_job_status_post_save(sender, **kwargs):
    instance = kwargs['instance']
    job = instance.job
    previous_status = job.last_status
    # Update job last_status
    job.status = instance
    set_job_started_at(instance=job, status=instance.status)
    set_job_finished_at(instance=job, status=instance.status)
    job.save(update_fields=['status', 'started_at', 'finished_at'])
    auditor.record(event_type=TENSORBOARD_NEW_STATUS,
                   instance=job,
                   previous_status=previous_status,
                   target='project')
    if instance.status == JobLifeCycle.STOPPED:
        auditor.record(event_type=TENSORBOARD_STOPPED,
                       instance=job,
                       previous_status=previous_status,
                       target='project')

    if instance.status == JobLifeCycle.FAILED:
        auditor.record(event_type=TENSORBOARD_FAILED,
                       instance=job,
                       previous_status=previous_status,
                       target='project')
        # Schedule stop for this tensorboard
        celery_app.send_task(
            SchedulerCeleryTasks.TENSORBOARDS_STOP,
            kwargs={
                'project_name': job.project.unique_name,
                'project_uuid': job.project.uuid.hex,
                'tensorboard_job_name': job.unique_name,
                'tensorboard_job_uuid': job.uuid.hex,
                'update_status': False
            })

    if instance.status == JobLifeCycle.STOPPED:
        auditor.record(event_type=TENSORBOARD_SUCCEEDED,
                       instance=job,
                       previous_status=previous_status,
                       target='project')


@receiver(pre_delete, sender=TensorboardJob, dispatch_uid="tensorboard_job_pre_delete")
@ignore_raw
def tensorboard_job_pre_delete(sender, **kwargs):
    job = kwargs['instance']

    celery_app.send_task(
        SchedulerCeleryTasks.TENSORBOARDS_STOP,
        kwargs={
            'project_name': job.project.unique_name,
            'project_uuid': job.project.uuid.hex,
            'tensorboard_job_name': job.unique_name,
            'tensorboard_job_uuid': job.uuid.hex,
            'update_status': False
        })
