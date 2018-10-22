from constants.experiment_groups import ExperimentGroupLifeCycle
from db.getters.experiment_groups import get_running_experiment_group
from hpsearch.tasks import base
from hpsearch.tasks.logger import logger
from polyaxon.celery_api import celery_app
from polyaxon.settings import HPCeleryTasks, Intervals


def create(experiment_group):
    experiment_group.iteration_manager.create_iteration()
    experiments = base.create_group_experiments(experiment_group=experiment_group)

    if not experiments:
        logger.error('Experiment group `%s` could not create any experiment.',
                     experiment_group.id)
        experiment_group.set_status(ExperimentGroupLifeCycle.FAILED,
                                    message='Experiment group could not create new suggestions.')
        return

    experiment_group.iteration_manager.add_iteration_experiments(
        experiment_ids=[xp.id for xp in experiments])

    celery_app.send_task(
        HPCeleryTasks.HP_HYPERBAND_START,
        kwargs={'experiment_group_id': experiment_group.id},
        countdown=1)


@celery_app.task(name=HPCeleryTasks.HP_HYPERBAND_CREATE, ignore_result=True)
def hp_hyperband_create(experiment_group_id):
    experiment_group = get_running_experiment_group(experiment_group_id=experiment_group_id)
    if not experiment_group:
        return

    create(experiment_group)


@celery_app.task(name=HPCeleryTasks.HP_HYPERBAND_START,
                 bind=True,
                 max_retries=None,
                 ignore_result=True)
def hp_hyperband_start(self, experiment_group_id):
    experiment_group = get_running_experiment_group(experiment_group_id=experiment_group_id)
    if not experiment_group:
        return

    should_retry = base.start_group_experiments(experiment_group=experiment_group)
    if should_retry:
        # Schedule another task
        self.retry(countdown=Intervals.EXPERIMENTS_SCHEDULER)
        return

    celery_app.send_task(
        HPCeleryTasks.HP_HYPERBAND_ITERATE,
        kwargs={'experiment_group_id': experiment_group_id})


@celery_app.task(name=HPCeleryTasks.HP_HYPERBAND_ITERATE,
                 bind=True,
                 max_retries=None,
                 ignore_result=True)
def hp_hyperband_iterate(self, experiment_group_id):
    experiment_group = get_running_experiment_group(experiment_group_id=experiment_group_id)
    if not experiment_group:
        return

    if experiment_group.non_done_experiments.count() > 0:
        # Schedule another task, because all experiment must be done
        self.retry(countdown=Intervals.EXPERIMENTS_SCHEDULER)
        return

    iteration_config = experiment_group.iteration_config
    iteration_manager = experiment_group.iteration_manager
    search_manager = experiment_group.search_manager

    iteration_manager.update_iteration()

    if search_manager.should_reschedule(iteration=iteration_config.iteration,
                                        bracket_iteration=iteration_config.bracket_iteration):
        celery_app.send_task(
            HPCeleryTasks.HP_HYPERBAND_CREATE,
            kwargs={'experiment_group_id': experiment_group_id})
        return

    if search_manager.should_reduce_configs(iteration=iteration_config.iteration,
                                            bracket_iteration=iteration_config.bracket_iteration):
        iteration_manager.reduce_configs()
        celery_app.send_task(
            HPCeleryTasks.HP_HYPERBAND_START,
            kwargs={'experiment_group_id': experiment_group_id})
        return

    base.check_group_experiments_finished(experiment_group_id)
