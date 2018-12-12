import logging

from hestia.signal_decorators import (
    check_specification,
    ignore_raw,
    ignore_updates,
    ignore_updates_pre
)

from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver

import auditor

from constants.experiments import ExperimentLifeCycle
from constants.jobs import JobLifeCycle
from db.models.cloning_strategies import CloningStrategy
from db.models.experiment_groups import ExperimentGroup
from db.models.experiment_jobs import ExperimentJob, ExperimentJobStatus
from db.models.experiments import Experiment, ExperimentMetric, ExperimentStatus
from db.redis.tll import RedisTTL
from event_manager.events.experiment import (
    EXPERIMENT_DELETED,
    EXPERIMENT_DONE,
    EXPERIMENT_FAILED,
    EXPERIMENT_NEW_METRIC,
    EXPERIMENT_NEW_STATUS,
    EXPERIMENT_STOPPED,
    EXPERIMENT_SUCCEEDED
)
from libs.paths.experiments import delete_experiment_logs, delete_experiment_outputs
from libs.repos.utils import assign_code_reference
from polyaxon.celery_api import celery_app
from polyaxon.settings import HPCeleryTasks, SchedulerCeleryTasks
from signals.outputs import set_outputs, set_outputs_refs
from signals.run_time import (
    set_finished_at,
    set_job_finished_at,
    set_job_started_at,
    set_started_at
)
from signals.utils import remove_bookmarks, set_persistence, set_tags

_logger = logging.getLogger('polyaxon.signals.experiments')


@receiver(pre_save, sender=Experiment, dispatch_uid="experiment_pre_save")
@ignore_updates_pre
@ignore_raw
def experiment_pre_save(sender, **kwargs):
    instance = kwargs['instance']
    # Check if declarations need to be set
    if not instance.declarations and instance.specification:
        instance.declarations = instance.specification.declarations
    set_tags(instance=instance)
    set_persistence(instance=instance)
    set_outputs(instance=instance)
    set_outputs_refs(instance=instance)
    if not instance.specification or not instance.specification.build:
        return

    assign_code_reference(instance)


@receiver(post_save, sender=Experiment, dispatch_uid="experiment_post_save")
@ignore_updates
@ignore_raw
def experiment_post_save(sender, **kwargs):
    instance = kwargs['instance']
    instance.set_status(ExperimentLifeCycle.CREATED)

    if instance.is_independent:
        # Clean outputs and logs
        delete_experiment_logs(instance.unique_name)
        delete_experiment_outputs(persistence_outputs=instance.persistence_outputs,
                                  experiment_name=instance.unique_name)


@receiver(pre_delete, sender=Experiment, dispatch_uid="experiment_pre_delete")
@ignore_raw
def experiment_pre_delete(sender, **kwargs):
    instance = kwargs['instance']
    # Delete outputs and logs
    delete_experiment_outputs(
        persistence_outputs=instance.persistence_outputs,
        experiment_name=instance.unique_name)
    delete_experiment_logs(instance.unique_name)

    # Delete clones
    for experiment in instance.clones.filter(cloning_strategy=CloningStrategy.RESUME):
        experiment.delete()


@receiver(post_delete, sender=Experiment, dispatch_uid="experiment_post_delete")
@ignore_raw
def experiment_post_delete(sender, **kwargs):
    instance = kwargs['instance']
    auditor.record(event_type=EXPERIMENT_DELETED, instance=instance)
    remove_bookmarks(object_id=instance.id, content_type='experiment')


@receiver(post_save, sender=ExperimentJob, dispatch_uid="experiment_job_post_save")
@ignore_updates
@ignore_raw
def experiment_job_post_save(sender, **kwargs):
    instance = kwargs['instance']
    instance.set_status(status=JobLifeCycle.CREATED)


@receiver(post_save, sender=ExperimentJobStatus, dispatch_uid="experiment_job_status_post_save")
@ignore_updates
@ignore_raw
def experiment_job_status_post_save(sender, **kwargs):
    instance = kwargs['instance']
    job = instance.job

    job.status = instance
    set_job_started_at(instance=job, status=instance.status)
    set_job_finished_at(instance=job, status=instance.status)
    job.save(update_fields=['status', 'started_at', 'finished_at'])

    # check if the new status is done to remove the containers from the monitors
    if job.is_done:
        from db.redis.containers import RedisJobContainers

        RedisJobContainers.remove_job(job.uuid.hex)

    # Check if we need to change the experiment status
    experiment = instance.job.experiment
    if experiment.is_done:
        return

    celery_app.send_task(
        SchedulerCeleryTasks.EXPERIMENTS_CHECK_STATUS,
        kwargs={'experiment_id': experiment.id},
        countdown=1)


@receiver(post_save, sender=ExperimentStatus, dispatch_uid="experiment_status_post_save")
@ignore_updates
@ignore_raw
def experiment_status_post_save(sender, **kwargs):
    instance = kwargs['instance']
    experiment = instance.experiment
    previous_status = experiment.last_status

    # update experiment last_status
    experiment.status = instance
    set_started_at(instance=experiment,
                   status=instance.status,
                   starting_statuses=[ExperimentLifeCycle.STARTING])
    set_finished_at(instance=experiment,
                    status=instance.status,
                    is_done=ExperimentLifeCycle.is_done)
    experiment.save(update_fields=['status', 'started_at', 'finished_at'])
    auditor.record(event_type=EXPERIMENT_NEW_STATUS,
                   instance=experiment,
                   previous_status=previous_status)

    if instance.status == ExperimentLifeCycle.SUCCEEDED:
        # update all workers with succeeded status, since we will trigger a stop mechanism
        for job in experiment.jobs.all():
            if not job.is_done:
                job.set_status(JobLifeCycle.SUCCEEDED, message='Master is done.')
        auditor.record(event_type=EXPERIMENT_SUCCEEDED,
                       instance=experiment,
                       previous_status=previous_status)
    if instance.status == ExperimentLifeCycle.FAILED:
        auditor.record(event_type=EXPERIMENT_FAILED,
                       instance=experiment,
                       previous_status=previous_status)

    if instance.status == ExperimentLifeCycle.STOPPED:
        auditor.record(event_type=EXPERIMENT_STOPPED,
                       instance=experiment,
                       previous_status=previous_status)

    if ExperimentLifeCycle.is_done(instance.status):
        auditor.record(event_type=EXPERIMENT_DONE,
                       instance=experiment,
                       previous_status=previous_status)
        # Check if it's part of an experiment group, and start following tasks
        if not experiment.is_independent:
            celery_app.send_task(
                HPCeleryTasks.HP_START,
                kwargs={'experiment_group_id': experiment.experiment_group.id},
                countdown=1)


@receiver(post_save, sender=ExperimentMetric, dispatch_uid="experiment_metric_post_save")
@ignore_updates
@ignore_raw
def experiment_metric_post_save(sender, **kwargs):
    instance = kwargs['instance']
    experiment = instance.experiment

    # update experiment last_metric
    def update_metric(last_metrics, metrics):
        last_metrics.update(metrics)
        return last_metrics

    experiment.last_metric = update_metric(last_metrics=experiment.last_metric,
                                           metrics=instance.values)
    experiment.save(update_fields=['last_metric'])
    auditor.record(event_type=EXPERIMENT_NEW_METRIC,
                   instance=experiment)


@receiver(post_save, sender=Experiment, dispatch_uid="start_new_experiment")
@check_specification
@ignore_updates
@ignore_raw
def start_new_experiment(sender, **kwargs):
    instance = kwargs['instance']
    if instance.is_independent or instance.is_clone:
        # Start building the experiment and then Schedule it to be picked by the spawners
        celery_app.send_task(
            SchedulerCeleryTasks.EXPERIMENTS_BUILD,
            kwargs={'experiment_id': instance.id},
            countdown=1)


@receiver(pre_delete, sender=Experiment, dispatch_uid="stop_running_experiment")
@check_specification
@ignore_raw
def stop_running_experiment(sender, **kwargs):
    instance = kwargs['instance']
    if not instance.is_running or instance.jobs.count() == 0:
        return

    try:
        group = instance.experiment_group
        celery_app.send_task(
            SchedulerCeleryTasks.EXPERIMENTS_STOP,
            kwargs={
                'project_name': instance.project.unique_name,
                'project_uuid': instance.project.uuid.hex,
                'experiment_name': instance.unique_name,
                'experiment_uuid': instance.uuid.hex,
                'experiment_group_name': group.unique_name if group else None,
                'experiment_group_uuid': group.uuid.hex if group else None,
                'specification': instance.config,
                'update_status': False,
                'collect_logs': False,
            },
            countdown=1)
    except ExperimentGroup.DoesNotExist:
        # The experiment was already stopped when the group was deleted
        pass


@receiver(post_save, sender=ExperimentStatus, dispatch_uid="handle_new_experiment_status")
@ignore_raw
def handle_new_experiment_status(sender, **kwargs):
    instance = kwargs['instance']
    experiment = instance.experiment
    if not experiment.specification:
        return

    stop_condition = (
        instance.status in (ExperimentLifeCycle.FAILED, ExperimentLifeCycle.SUCCEEDED) and
        experiment.jobs.count() > 0
    )
    if stop_condition:
        _logger.debug('One of the workers failed or Master for experiment `%s` is done, '
                      'send signal to other workers to stop.', experiment.unique_name)
        # Schedule stop for this experiment because other jobs may be still running
        group = experiment.experiment_group
        celery_app.send_task(
            SchedulerCeleryTasks.EXPERIMENTS_STOP,
            kwargs={
                'project_name': experiment.project.unique_name,
                'project_uuid': experiment.project.uuid.hex,
                'experiment_name': experiment.unique_name,
                'experiment_uuid': experiment.uuid.hex,
                'experiment_group_name': group.unique_name if group else None,
                'experiment_group_uuid': group.uuid.hex if group else None,
                'specification': experiment.config,
                'update_status': False,
                'collect_logs': True,
            },
            countdown=RedisTTL.get_for_experiment(experiment_id=experiment.id))
