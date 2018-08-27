from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

import auditor

from api.experiment_groups import queries
from api.experiment_groups.serializers import (
    ExperimentGroupCreateSerializer,
    ExperimentGroupDetailSerializer,
    ExperimentGroupSerializer,
    ExperimentGroupStatusSerializer
)
from api.filters import OrderingFilter, QueryFilter
from api.utils.views import AuditorMixinView, ListCreateAPIView
from db.models.experiment_groups import ExperimentGroup, ExperimentGroupStatus
from event_manager.events.experiment_group import (
    EXPERIMENT_GROUP_DELETED_TRIGGERED,
    EXPERIMENT_GROUP_STATUSES_VIEWED,
    EXPERIMENT_GROUP_STOPPED_TRIGGERED,
    EXPERIMENT_GROUP_UPDATED,
    EXPERIMENT_GROUP_VIEWED
)
from event_manager.events.project import PROJECT_EXPERIMENT_GROUPS_VIEWED
from libs.permissions.projects import IsItemProjectOwnerOrPublicReadOnly, get_permissible_project
from libs.utils import to_bool
from polyaxon.celery_api import app as celery_app
from polyaxon.settings import SchedulerCeleryTasks


class ExperimentGroupListView(ListCreateAPIView):
    """
    get:
        List experiment groups under a project.

    post:
        Create an experiment group under a project.
    """
    queryset = queries.groups
    serializer_class = ExperimentGroupSerializer
    create_serializer_class = ExperimentGroupCreateSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (QueryFilter, OrderingFilter,)
    query_manager = 'experiment_group'
    ordering = ('-updated_at',)
    ordering_fields = ('created_at', 'updated_at', 'started_at', 'finished_at')

    def filter_queryset(self, queryset):
        project = get_permissible_project(view=self)
        auditor.record(event_type=PROJECT_EXPERIMENT_GROUPS_VIEWED,
                       instance=project,
                       actor_id=self.request.user.id,
                       actor_name=self.request.user.username)
        queryset = queryset.filter(project=project)
        return super().filter_queryset(queryset=queryset)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, project=get_permissible_project(view=self))


class ExperimentGroupDetailView(AuditorMixinView, RetrieveUpdateDestroyAPIView):
    """
    get:
        Get an experiment group details.
    patch:
        Update an experiment group details.
    delete:
        Delete an experiment group.
    """
    queryset = queries.groups_details
    serializer_class = ExperimentGroupDetailSerializer
    permission_classes = (IsAuthenticated, IsItemProjectOwnerOrPublicReadOnly)
    lookup_field = 'id'
    get_event = EXPERIMENT_GROUP_VIEWED
    update_event = EXPERIMENT_GROUP_UPDATED
    delete_event = EXPERIMENT_GROUP_DELETED_TRIGGERED

    def filter_queryset(self, queryset):
        return queryset.filter(project=get_permissible_project(view=self))

    def get_object(self):
        obj = super().get_object()
        # Check project permissions
        self.check_object_permissions(self.request, obj)
        return obj


class ExperimentGroupStopView(CreateAPIView):
    """Stop an experiment group."""
    queryset = ExperimentGroup.objects.all()
    serializer_class = ExperimentGroupSerializer
    permission_classes = (IsAuthenticated, IsItemProjectOwnerOrPublicReadOnly)
    lookup_field = 'id'

    def filter_queryset(self, queryset):
        return queryset.filter(project=get_permissible_project(view=self))

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        pending = request.data.get('pending')
        pending = to_bool(pending) if pending is not None else False
        auditor.record(event_type=EXPERIMENT_GROUP_STOPPED_TRIGGERED,
                       instance=obj,
                       actor_id=request.user.id,
                       actor_name=request.user.username,
                       pending=pending)
        celery_app.send_task(
            SchedulerCeleryTasks.EXPERIMENTS_GROUP_STOP_EXPERIMENTS,
            kwargs={'experiment_group_id': obj.id,
                    'pending': pending,
                    'message': 'User stopped experiment group'})
        return Response(status=status.HTTP_200_OK)


class ExperimentGroupStatusListView(ListCreateAPIView):
    """
    get:
        List all statuses of experiment group.
    post:
        Create an experiment group status.
    """
    queryset = ExperimentGroupStatus.objects.order_by('created_at').all()
    serializer_class = ExperimentGroupStatusSerializer
    permission_classes = (IsAuthenticated,)
    project = None
    group = None

    def get_experiment_group(self):
        # Get project and check access
        self.project = get_permissible_project(view=self)
        group_id = self.kwargs['group_id']
        self.group = get_object_or_404(ExperimentGroup, project=self.project, id=group_id)
        return self.group

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        return queryset.filter(experiment_group=self.get_experiment_group())

    def perform_create(self, serializer):
        serializer.save(experiment_group=self.get_experiment_group())

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        auditor.record(event_type=EXPERIMENT_GROUP_STATUSES_VIEWED,
                       instance=self.group,
                       actor_id=request.user.id,
                       actor_name=request.user.username)
        return response
