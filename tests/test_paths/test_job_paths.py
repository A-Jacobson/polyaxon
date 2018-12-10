import os

import pytest

from factories.factory_jobs import JobFactory
from libs.paths.jobs import (
    create_job_logs_path,
    create_job_outputs_path,
    delete_job_logs,
    delete_job_outputs,
    get_job_logs_path,
    get_job_outputs_path
)
from tests.utils import BaseTest


@pytest.mark.paths_mark
class TestJobPaths(BaseTest):
    DISABLE_RUNNER = True

    def test_job_logs_path_creation_deletion(self):
        job = JobFactory()
        job_logs_path = get_job_logs_path(job.unique_name, temp=False)
        create_job_logs_path(job.unique_name, temp=False)
        open(job_logs_path, '+w')
        # Should be true, created by the signal
        assert os.path.exists(job_logs_path) is True
        delete_job_logs(job.unique_name)
        assert os.path.exists(job_logs_path) is False

    def test_job_outputs_path_creation_deletion(self):
        job = JobFactory()
        create_job_outputs_path(persistence_outputs=job.persistence_outputs,
                                job_name=job.unique_name)
        job_outputs_path = get_job_outputs_path(persistence_outputs=job.persistence_outputs,
                                                job_name=job.unique_name)
        assert os.path.exists(job_outputs_path) is True
        delete_job_outputs(persistence_outputs=job.persistence_outputs, job_name=job.unique_name)
        assert os.path.exists(job_outputs_path) is False
