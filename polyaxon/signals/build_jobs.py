import logging

from hestia.decorators import ignore_raw, ignore_updates, ignore_updates_pre

from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver

import auditor

from constants.jobs import JobLifeCycle
from db.models.build_jobs import BuildJob, BuildJobStatus
from db.redis.tll import RedisTTL
from event_manager.events.build_job import (
    BUILD_JOB_DELETED,
    BUILD_JOB_DONE,
    BUILD_JOB_FAILED,
    BUILD_JOB_NEW_STATUS,
    BUILD_JOB_STOPPED,
    BUILD_JOB_SUCCEEDED
)
from libs.paths.jobs import delete_job_logs
from libs.repos.utils import assign_code_reference
from polyaxon.celery_api import celery_app
from polyaxon.settings import SchedulerCeleryTasks
from signals.run_time import set_job_finished_at, set_job_started_at
from signals.utils import remove_bookmarks, set_tags

_logger = logging.getLogger('polyaxon.signals.build_jobs')


@receiver(pre_save, sender=BuildJob, dispatch_uid="build_job_pre_save")
@ignore_updates_pre
@ignore_raw
def build_job_pre_save(sender, **kwargs):
    instance = kwargs['instance']
    set_tags(instance=instance)
    assign_code_reference(instance)


@receiver(post_save, sender=BuildJob, dispatch_uid="build_job_post_save")
@ignore_updates
@ignore_raw
def build_job_post_save(sender, **kwargs):
    instance = kwargs['instance']
    instance.set_status(status=JobLifeCycle.CREATED)


@receiver(post_save, sender=BuildJobStatus, dispatch_uid="build_job_status_post_save")
@ignore_updates
@ignore_raw
def build_job_status_post_save(sender, **kwargs):
    instance = kwargs['instance']
    job = instance.job
    previous_status = job.last_status

    # Update job last_status
    job.status = instance
    set_job_started_at(instance=job, status=instance.status)
    set_job_finished_at(instance=job, status=instance.status)
    job.save(update_fields=['status', 'started_at', 'finished_at'])
    auditor.record(event_type=BUILD_JOB_NEW_STATUS,
                   instance=job,
                   previous_status=previous_status)
    if instance.status == JobLifeCycle.STOPPED:
        auditor.record(event_type=BUILD_JOB_STOPPED,
                       instance=job,
                       previous_status=previous_status)

    if instance.status == JobLifeCycle.FAILED:
        auditor.record(event_type=BUILD_JOB_FAILED,
                       instance=job,
                       previous_status=previous_status)

    if instance.status == JobLifeCycle.SUCCEEDED:
        auditor.record(event_type=BUILD_JOB_SUCCEEDED,
                       instance=job,
                       previous_status=previous_status)

    # Check if we need to schedule a job stop
    if instance.status in (JobLifeCycle.FAILED, JobLifeCycle.SUCCEEDED):
        _logger.info('The build job  `%s` failed or is done, '
                     'send signal to stop.', job.unique_name)
        # Schedule stop for this job
        celery_app.send_task(
            SchedulerCeleryTasks.BUILD_JOBS_STOP,
            kwargs={
                'project_name': job.project.unique_name,
                'project_uuid': job.project.uuid.hex,
                'build_job_name': job.unique_name,
                'build_job_uuid': job.uuid.hex,
                'update_status': False
            },
            countdown=RedisTTL.get_for_build(build_id=job.id))

    # handle done status
    if JobLifeCycle.is_done(instance.status):
        auditor.record(event_type=BUILD_JOB_DONE,
                       instance=job,
                       previous_status=previous_status)
        celery_app.send_task(
            SchedulerCeleryTasks.BUILD_JOBS_NOTIFY_DONE,
            kwargs={'build_job_id': job.id})


@receiver(pre_delete, sender=BuildJob, dispatch_uid="build_job_pre_delete")
@ignore_raw
def build_job_pre_delete(sender, **kwargs):
    job = kwargs['instance']

    # Delete outputs and logs
    delete_job_logs(job.unique_name)

    if not job.is_running:
        return

    celery_app.send_task(
        SchedulerCeleryTasks.BUILD_JOBS_STOP,
        kwargs={
            'project_name': job.project.unique_name,
            'project_uuid': job.project.uuid.hex,
            'build_job_name': job.unique_name,
            'build_job_uuid': job.uuid.hex,
            'update_status': False
        })


@receiver(post_delete, sender=BuildJob, dispatch_uid="build_job_post_delete")
@ignore_raw
def build_job_post_delete(sender, **kwargs):
    instance = kwargs['instance']
    auditor.record(event_type=BUILD_JOB_DELETED, instance=instance)
    remove_bookmarks(object_id=instance.id, content_type='buildjob')
