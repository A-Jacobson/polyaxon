# pylint:disable=ungrouped-imports

from unittest.mock import patch

import pytest

import activitylogs
import auditor
import notifier
import tracker

from event_manager.events import experiment_job as experiment_job_events
from factories.factory_experiments import ExperimentJobFactory
from tests.utils import BaseTest


@pytest.mark.auditor_mark
class AuditorExperimentJobTest(BaseTest):
    """Testing subscribed events"""
    DISABLE_RUNNER = True

    def setUp(self):
        super().setUp()
        self.experiment_job = ExperimentJobFactory()
        auditor.validate()
        auditor.setup()
        tracker.validate()
        tracker.setup()
        activitylogs.validate()
        activitylogs.setup()
        notifier.validate()
        notifier.setup()

    @patch('notifier.service.NotifierService.record_event')
    @patch('tracker.service.TrackerService.record_event')
    @patch('activitylogs.service.ActivityLogService.record_event')
    def test_experiment_job_viewed(self,
                                   activitylogs_record,
                                   tracker_record,
                                   notifier_record):
        auditor.record(event_type=experiment_job_events.EXPERIMENT_JOB_VIEWED,
                       instance=self.experiment_job,
                       actor_id=1,
                       actor_name='foo')

        assert tracker_record.call_count == 1
        assert activitylogs_record.call_count == 1
        assert notifier_record.call_count == 0

    @patch('notifier.service.NotifierService.record_event')
    @patch('tracker.service.TrackerService.record_event')
    @patch('activitylogs.service.ActivityLogService.record_event')
    def test_experiment_resources_viewed(self,
                                         activitylogs_record,
                                         tracker_record,
                                         notifier_record):
        auditor.record(event_type=experiment_job_events.EXPERIMENT_JOB_RESOURCES_VIEWED,
                       instance=self.experiment_job,
                       actor_id=1,
                       actor_name='foo')

        assert tracker_record.call_count == 1
        assert activitylogs_record.call_count == 1
        assert notifier_record.call_count == 0

    @patch('notifier.service.NotifierService.record_event')
    @patch('tracker.service.TrackerService.record_event')
    @patch('activitylogs.service.ActivityLogService.record_event')
    def test_experiment_logs_viewed(self,
                                    activitylogs_record,
                                    tracker_record,
                                    notifier_record):
        auditor.record(event_type=experiment_job_events.EXPERIMENT_JOB_LOGS_VIEWED,
                       instance=self.experiment_job,
                       actor_id=1,
                       actor_name='foo')

        assert tracker_record.call_count == 1
        assert activitylogs_record.call_count == 1
        assert notifier_record.call_count == 0

    @patch('notifier.service.NotifierService.record_event')
    @patch('tracker.service.TrackerService.record_event')
    @patch('activitylogs.service.ActivityLogService.record_event')
    def test_experiment_job_statuses_viewed(self,
                                            activitylogs_record,
                                            tracker_record,
                                            notifier_record):
        auditor.record(event_type=experiment_job_events.EXPERIMENT_JOB_STATUSES_VIEWED,
                       instance=self.experiment_job,
                       actor_id=1,
                       actor_name='foo')

        assert tracker_record.call_count == 1
        assert activitylogs_record.call_count == 1
        assert notifier_record.call_count == 0
