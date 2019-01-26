from django.core.exceptions import ObjectDoesNotExist

import conf

from constants.jobs import JobLifeCycle
from db.models.repos import Repo
from dockerizer.builders.base import BaseDockerBuilder


class BaseJobDockerBuilder(BaseDockerBuilder):
    CHECK_INTERVAL = 10

    def __init__(self,
                 project_id,
                 project_name,
                 repo_path,
                 from_image,
                 image_name,
                 image_tag,
                 copy_code=True,
                 in_tmp_repo=True,
                 build_steps=None,
                 env_vars=None,
                 dockerfile_name='Dockerfile'):
        self.project_id = project_id
        self.project_name = project_name
        super().__init__(
            repo_path=repo_path,
            from_image=from_image,
            image_name=image_name,
            image_tag=image_tag,
            copy_code=copy_code,
            in_tmp_repo=in_tmp_repo,
            build_steps=build_steps,
            env_vars=env_vars,
            dockerfile_name=dockerfile_name)

    def _handle_logs(self, log_line):
        pass

    def _check_pulse(self, check_pulse):
        pass


def get_job_repo_info(project, job):
    project_name = project.name
    # job_spec = job.specification
    # if job_spec.build.git:  # We need to fetch the repo first
    #
    #     repo, is_created = ExternalRepo.objects.get_or_create(project=project,
    #                                                           git_url=job_spec.build.git)
    #     if not is_created:
    #         # If the repo already exist, we just need to refetch it
    #         git.fetch(git_url=repo.git_url, repo_path=repo.path)
    #
    #     repo_path = repo.path
    #     repo_name = repo.name
    #     last_commit = repo.last_commit
    # else:
    repo_path = project.repo.path
    repo_name = project_name

    image_name = '{}/{}'.format(conf.get('REGISTRY_HOST'), repo_name)
    try:
        last_commit = project.repo.last_commit
    except ValueError:
        raise Repo.DoesNotExist
    image_tag = last_commit[0]
    return {
        'repo_path': repo_path,
        'image_name': image_name,
        'image_tag': image_tag
    }


def build_job(project, job, job_builder, image_tag=None):
    """Build necessary code for a job to run"""
    job_spec = job.specification
    build_info = get_job_repo_info(project, job)

    # Build the image
    docker_builder = job_builder(project_id=project.id,
                                 project_name=project.unique_name,
                                 repo_path=build_info['repo_path'],
                                 from_image=job_spec.build.image,
                                 image_name=build_info['image_name'],
                                 image_tag=image_tag or build_info['image_tag'],
                                 build_steps=job_spec.build.build_steps,
                                 env_vars=job_spec.build.env_vars)
    docker_builder.login(registry_user=conf.get('REGISTRY_USER'),
                         registry_password=conf.get('REGISTRY_PASSWORD'),
                         registry_host=conf.get('REGISTRY_HOST'))
    if docker_builder.check_image():
        # Image already built
        docker_builder.clean()
        return True
    if not docker_builder.build():
        docker_builder.clean()
        return False
    if not docker_builder.push():
        docker_builder.clean()
        try:
            job.set_status(JobLifeCycle.FAILED,
                           message='The docker image could not be pushed.')
        except ObjectDoesNotExist:
            pass
        return False
    docker_builder.clean()
    return True
