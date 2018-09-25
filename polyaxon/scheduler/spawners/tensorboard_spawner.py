import json
import random

from django.conf import settings
from polyaxon_k8s.exceptions import PolyaxonK8SError

from scheduler.spawners.project_job_spawner import ProjectJobSpawner
from scheduler.spawners.templates import constants, ingresses, services
from scheduler.spawners.templates.pod_environment import (
    get_affinity,
    get_node_selector,
    get_tolerations
)
from scheduler.spawners.templates.project_jobs import deployments
from scheduler.spawners.templates.volumes import (
    get_pod_outputs_volume,
    get_pod_refs_outputs_volumes
)


class TensorboardSpawner(ProjectJobSpawner):
    TENSORBOARD_JOB_NAME = 'tensorboard'
    PORT = 6006

    def get_tensorboard_url(self):
        return self._get_service_url(self.TENSORBOARD_JOB_NAME)

    def request_tensorboard_port(self):
        if not self._use_ingress():
            return self.PORT

        labels = 'app={},role={}'.format(settings.APP_LABELS_TENSORBOARD,
                                         settings.ROLE_LABELS_DASHBOARD)
        ports = [service.spec.ports[0].port for service in self.list_services(labels)]
        port = random.randint(*settings.TENSORBOARD_PORT_RANGE)
        while port in ports:
            port = random.randint(*settings.TENSORBOARD_PORT_RANGE)
        return port

    def start_tensorboard(self,
                          image,
                          outputs_path,
                          persistence_outputs,
                          outputs_refs_jobs=None,
                          outputs_refs_experiments=None,
                          resources=None,
                          node_selector=None,
                          affinity=None,
                          tolerations=None):
        ports = [self.request_tensorboard_port()]
        target_ports = [self.PORT]
        volumes, volume_mounts = get_pod_outputs_volume(persistence_outputs)
        refs_volumes, refs_volume_mounts = get_pod_refs_outputs_volumes(
            outputs_refs=outputs_refs_jobs,
            persistence_outputs=persistence_outputs)
        volumes += refs_volumes
        volume_mounts += refs_volume_mounts
        refs_volumes, refs_volume_mounts = get_pod_refs_outputs_volumes(
            outputs_refs=outputs_refs_experiments,
            persistence_outputs=persistence_outputs)
        volumes += refs_volumes
        volume_mounts += refs_volume_mounts

        node_selector = get_node_selector(
            node_selector=node_selector,
            default_node_selector=settings.NODE_SELECTOR_EXPERIMENTS)
        affinity = get_affinity(
            affinity=affinity,
            default_affinity=settings.AFFINITY_EXPERIMENTS)
        tolerations = get_tolerations(
            tolerations=tolerations,
            default_tolerations=settings.TOLERATIONS_EXPERIMENTS)
        deployment = deployments.get_deployment(
            namespace=self.namespace,
            app=settings.APP_LABELS_TENSORBOARD,
            name=self.TENSORBOARD_JOB_NAME,
            project_name=self.project_name,
            project_uuid=self.project_uuid,
            job_name=self.job_name,
            job_uuid=self.job_uuid,
            volume_mounts=volume_mounts,
            volumes=volumes,
            image=image,
            command=["/bin/sh", "-c"],
            args=["tensorboard --logdir={} --port={}".format(outputs_path, self.PORT)],
            ports=target_ports,
            container_name=settings.CONTAINER_NAME_PLUGIN_JOB,
            resources=resources,
            node_selector=node_selector,
            affinity=affinity,
            tolerations=tolerations,
            role=settings.ROLE_LABELS_DASHBOARD,
            type=settings.TYPE_LABELS_EXPERIMENT)
        deployment_name = constants.JOB_NAME.format(name=self.TENSORBOARD_JOB_NAME,
                                                    job_uuid=self.job_uuid)
        deployment_labels = deployments.get_labels(app=settings.APP_LABELS_TENSORBOARD,
                                                   project_name=self.project_name,
                                                   project_uuid=self.project_uuid,
                                                   job_name=self.job_name,
                                                   job_uuid=self.job_uuid,
                                                   role=settings.ROLE_LABELS_DASHBOARD,
                                                   type=settings.TYPE_LABELS_EXPERIMENT)

        dep_resp, _ = self.create_or_update_deployment(name=deployment_name, data=deployment)
        service = services.get_service(
            namespace=self.namespace,
            name=deployment_name,
            labels=deployment_labels,
            ports=ports,
            target_ports=target_ports,
            service_type=self._get_service_type())
        service_resp, _ = self.create_or_update_service(name=deployment_name, data=service)
        results = {'deployment': dep_resp.to_dict(), 'service': service_resp.to_dict()}

        if self._use_ingress():
            annotations = json.loads(settings.K8S_INGRESS_ANNOTATIONS)
            paths = [{
                'path': '/tensorboard/{}'.format(self.project_name.replace('.', '/')),
                'backend': {
                    'serviceName': deployment_name,
                    'servicePort': ports[0]
                }
            }]
            ingress = ingresses.get_ingress(namespace=self.namespace,
                                            name=deployment_name,
                                            labels=deployment_labels,
                                            annotations=annotations,
                                            paths=paths)
            self.create_or_update_ingress(name=deployment_name, data=ingress)

        return results

    def stop_tensorboard(self):
        deployment_name = constants.JOB_NAME.format(name=self.TENSORBOARD_JOB_NAME,
                                                    job_uuid=self.job_uuid)
        try:
            self.delete_deployment(name=deployment_name)
            self.delete_service(name=deployment_name)
            if self._use_ingress():
                self.delete_ingress(name=deployment_name)
            return True
        except PolyaxonK8SError:
            return False
